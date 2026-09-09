"""Verify SearXNG-discovered leads against direct public creator profiles.

Search results are never publication evidence. YouTube video leads are resolved
to their uploader channel first. A public record is created only after the
channel/profile page itself yields a usable identity plus VTuber/V-liver
evidence (or is an avatar-first platform profile such as IRIAM/REALITY/Avvy).
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import html
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path

from platform_sources import canonical_account
import profile_backoff as backoff
from update_dictionary import read_js

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / 'scripts' / 'searxng-candidates.json'
REPORT = ROOT / 'scripts' / 'searxng-verification-report.json'
EXTRA = ROOT / 'extra-data.js'

VTUBER = re.compile(r'\bvtuber\b|v[- ]?tuber|virtual\s+youtuber|バーチャル\s*youtuber|バーチャルYouTuber|ＶＴｕｂｅｒ|Vライバー|Ｖライバー|バーチャルライバー|vliver|v-liver|aivtuber|ai\s*vtuber|AIライバー', re.I)
VTUBER = re.compile(VTUBER.pattern + r'|\bvsinger\b|バーチャルシンガー|virtual\s+(?:streamer|singer)|虚拟(?:主播|UP主)|虛擬(?:主播|實況主|YouTuber)|버튜버|버츄얼\s*(?:유튜버|스트리머)|버추얼\s*(?:유튜버|스트리머)', re.I)
AIV = re.compile(r'aivtuber|aituber|ai\s*vtuber|ai\s*v[- ]?tuber|AIライバー|AI\s*Vライバー|\bAI\s+(?:virtual\s+)?streamer\b', re.I)
VLIVER = re.compile(r'Vライバー|Ｖライバー|バーチャルライバー|vliver|v-liver', re.I)
REJECT = re.compile(r'切り抜き|切抜|クリップ|まとめ|翻訳|非公式|ファン(?:チャンネル|ch)|応援ch|\b(?:clips?|clipping|highlights?|compilations?|reactions?|reacts?|archive|subbed)\b|\bfan\s+(?:channel|ch)\b|\bvod\s*channel\b|\beng\s*sub\b', re.I)
FAN_PROFILE = re.compile(r'切り抜き(?:チャンネル|ch|動画を(?:投稿|紹介|制作|作成))|切抜き?(?:チャンネル|ch)|非公式(?:チャンネル|ch)|ファン(?:チャンネル|ch)|応援(?:チャンネル|ch)|\bfan\s+channel\b|\b(?:clips?|clipping|compilation|highlights?|reaction|vod|archive|translation)\s+channel\b|\b(?:post|make|upload|share|translate)\s+(?:(?:short|funny|vtuber|translated)\s+)*(?:clips|compilations|highlights)\b', re.I)
VERIFIER_VERSION = 2
PREDEBUT = re.compile(r'VTuber\s*準備中|Vライバー\s*準備中|デビュー準備中|初配信予定|デビュー予定|pre[- ]?debut', re.I)
ENDED = re.compile(r'活動終了|活動を終了|引退しました|卒業しました|配信活動を終了', re.I)
NATIVE_V = {'iriam', 'reality', 'avvy'}
VIDEO_RE = re.compile(r'^[\w-]{11}$')
CHANNEL_RE = re.compile(r'^UC[\w-]{22}$')
HOST_LOCK = threading.Lock()
HOST_NEXT = {}
HOST_BLOCKED = set()
PROFILE_CACHE_LOCK = threading.Lock()
PROFILE_CACHE = {}
PROFILE_CACHE_ENABLED = False


@contextlib.contextmanager
def profile_cache():
    global PROFILE_CACHE_ENABLED
    PROFILE_CACHE.clear()
    PROFILE_CACHE_ENABLED = True
    try:
        yield
    finally:
        PROFILE_CACHE_ENABLED = False
        PROFILE_CACHE.clear()


def fan_channel(title, description):
    # A creator's fan-art tags, clip permissions, translated subtitles and VOD
    # archive links do not describe the channel as a fan-operated account.
    return bool(REJECT.search(title) or FAN_PROFILE.search(description))


def fetch_profile(url):
    # Several discovered videos can belong to one uploader. Fetch that public
    # profile once per verifier process, retaining the existing host rate limit.
    if not PROFILE_CACHE_ENABLED:
        return fetch_page(url)
    with PROFILE_CACHE_LOCK:
        owner = url not in PROFILE_CACHE
        future = PROFILE_CACHE.setdefault(url, Future())
    if owner:
        try:
            future.set_result(fetch_page(url))
        except Exception as error:
            future.set_exception(error)
    return future.result()


def throttle(url):
    host = backoff.host_key(url)
    with HOST_LOCK:
        if host in HOST_BLOCKED or backoff.blocked(url):
            raise backoff.DeferredHost('host cooldown remains active')
        now = time.monotonic()
        due = max(now, HOST_NEXT.get(host, now))
        HOST_NEXT[host] = due + 0.8
    time.sleep(max(0, due - now))
    if backoff.blocked(url):
        raise backoff.DeferredHost('host paused while this request was waiting')


def activity_evidence(document, description, platform):
    if platform == 'youtube':
        # Only inspect the channel's upload UI, not recommendation text.
        if re.search(r'"(?:videoRenderer|gridVideoRenderer|reelItemRenderer)"\s*:', document):
            return 'public_channel_uploads'
        if re.search(r'"videoCountText"\s*:\s*\{[^}]*[1-9][0-9,]*', document):
            return 'public_channel_video_count'
    if re.search(r'配信中|配信しています|配信している|活動中|デビュー済|初配信を終|streaming\s+(?:on|every)|stream\s+(?:on|every)|have\s+streamed', description, re.I):
        return 'creator_profile_describes_started_activity'
    # Retired creators remain eligible when past activity is stated explicitly.
    if ENDED.search(description):
        return 'creator_profile_describes_past_activity'
    return None


def clean_text(value):
    return html.unescape(re.sub(r'\s+', ' ', str(value or ''))).strip()


def meta(document, key):
    escaped = re.escape(key)
    for pattern in (
        rf'<meta\b[^>]*(?:property|name|itemprop)=["\']{escaped}["\'][^>]*content=["\']([^"\']*)["\']',
        rf'<meta\b[^>]*content=["\']([^"\']*)["\'][^>]*(?:property|name|itemprop)=["\']{escaped}["\']',
    ):
        match = re.search(pattern, document, re.I)
        if match:
            return clean_text(match.group(1))
    return ''


def title_of(document):
    return meta(document, 'og:title') or meta(document, 'twitter:title') or clean_text(re.sub(r'<[^>]+>', '', (re.search(r'<title\b[^>]*>(.*?)</title>', document, re.I | re.S) or [None, ''])[1]))


def description_of(document):
    return meta(document, 'og:description') or meta(document, 'description') or meta(document, 'twitter:description')


def youtube_channel_id(document):
    for pattern in (
        r'<meta\b[^>]*itemprop=["\']channelId["\'][^>]*content=["\'](UC[\w-]{22})["\']',
        r'"externalId"\s*:\s*"(UC[\w-]{22})"',
        r'"channelId"\s*:\s*"(UC[\w-]{22})"',
    ):
        match = re.search(pattern, document)
        if match:
            return match.group(1)
    return None


def fetch_page(url):
    throttle(url)
    request = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; VName-primary-verifier/1.0; +https://github.com/Kirakun0328/vname-web)',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.5',
    })
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read(4 * 1024 * 1024 + 1)
            ctype = response.headers.get('content-type', '')
    except urllib.error.HTTPError as error:
        if error.code in (403, 429):
            with HOST_LOCK:
                HOST_BLOCKED.add(backoff.host_key(url))
                backoff.pause(url, error.code, error.headers.get('Retry-After') if error.headers else None)
        raise
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError('profile page too large')
    match = re.search(r'charset=([\w.-]+)', ctype, re.I)
    charset = match.group(1) if match else 'utf-8'
    try:
        return raw.decode(charset, errors='replace')
    except LookupError:
        return raw.decode('utf-8', errors='replace')


def resolve_youtube_lead(url):
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or '').lower().removeprefix('www.').removeprefix('m.')
    if host != 'youtube.com':
        return url, None
    path = parsed.path.rstrip('/')
    is_video = path == '/watch' or bool(re.fullmatch(r'/shorts/[\w-]{11}', path))
    if not is_video:
        return url, None
    document = fetch_page(url)
    cid = youtube_channel_id(document)
    if not cid:
        return url, 'video_channel_unavailable'
    return 'https://www.youtube.com/channel/' + cid, None


def clean_name(title, platform):
    value = clean_text(title)
    patterns = {
        'youtube': [r'\s*[-|]\s*YouTube\s*$', r'\s*YouTube\s*$'],
        'twitch': [r'\s*[-|]\s*Twitch\s*$'],
        'tiktok': [r'\s*[-|]\s*TikTok\s*$', r'\s+on\s+TikTok\s*$', r'\s*\(@[\w.\-]+\)\s*$'],
        'iriam': [r'\s*[-|]\s*IRIAM\s*$'],
        'reality': [r'\s*[-|]\s*REALITY\s*$'],
        'avvy': [r'\s*[-|]\s*Avvy\s*$'],
        'showroom': [r'\s*[-|]\s*SHOWROOM.*$'],
        '17live': [r'\s*[-|]\s*17LIVE.*$'],
        'mirrativ': [r'\s*[-|]\s*Mirrativ.*$'],
        'niconico': [r'\s*[-|]\s*ニコニコ.*$'],
        'kick': [r'\s*[-|]\s*Kick\s*$'],
    }
    for pattern in patterns.get(platform, []):
        value = re.sub(pattern, '', value, flags=re.I).strip()
    value = re.sub(r'^[【\[]\s*(?:VTuber|Vライバー)\s*[】\]]\s*', '', value, flags=re.I).strip()
    if not value or len(value) > 120 or any(c in value for c in '\r\n\t'):
        return ''
    return value


def existing_indexes():
    merged = {}
    account_index = {}
    for file, variable in (('data.js', 'VTUBER_DATA'), ('extra-data.js', 'VTUBER_EXTRA'), ('platform-data.js', 'VTUBER_PLATFORMS')):
        path = ROOT / file
        if not path.exists():
            continue
        for row in read_js(path, variable):
            merged.setdefault(row['source_id'], {}).update(row)
    for sid, row in merged.items():
        for item in row.get('platform_accounts', []):
            account = canonical_account(item.get('url')) if isinstance(item, dict) else None
            if account:
                account_index[(account['platform'], account['id'])] = sid
        cid = row.get('youtube_channel_id')
        if isinstance(cid, str) and CHANNEL_RE.fullmatch(cid):
            account_index[('youtube', 'channel/' + cid)] = sid
    return merged, account_index


def verify_one(candidate):
    original_url = candidate.get('url', '')
    try:
        url, resolve_error = resolve_youtube_lead(original_url)
        if resolve_error:
            return candidate, None, resolve_error
        account = canonical_account(url)
        if not account:
            return candidate, None, 'invalid_profile_url'
        document = fetch_profile(url)
    except backoff.DeferredHost:
        return candidate, None, 'deferred_host_backoff'
    except urllib.error.HTTPError as error:
        if error.code in (403, 429):
            return candidate, None, 'deferred_host_backoff'
        return candidate, None, 'unavailable:HTTP' + str(error.code)
    except (OSError, ValueError, UnicodeError) as error:
        return candidate, None, 'unavailable:' + type(error).__name__

    title = title_of(document)
    description = description_of(document)
    # Related videos and embedded recommendations can mention unrelated people.
    searchable = clean_text(title + ' ' + description)
    if PREDEBUT.search(searchable):
        return candidate, None, 'predebut'
    if fan_channel(title, description):
        return candidate, None, 'fan_or_clip_channel'

    platform = account['platform']
    if platform not in NATIVE_V and not (VTUBER.search(searchable) or AIV.search(searchable)):
        return candidate, None, 'no_direct_vtuber_evidence'
    activity = activity_evidence(document, description, platform)
    if not activity:
        return candidate, None, 'activity_unconfirmed'
    name = clean_name(title, platform)
    if not name:
        return candidate, None, 'name_unavailable'

    profile_account = account
    source_id = f"{platform}:{account['id']}"
    if platform == 'youtube':
        cid = youtube_channel_id(document)
        if not cid:
            return candidate, None, 'youtube_channel_id_unavailable'
        source_id = 'youtube:' + cid
        profile_account = {'platform': 'youtube', 'id': 'channel/' + cid, 'url': 'https://www.youtube.com/channel/' + cid}

    category = 'AIVTuber' if AIV.search(searchable) else ('Vライバー' if platform in NATIVE_V or VLIVER.search(searchable) else 'VTuber')
    today = datetime.date.today().isoformat()
    row = {
        'source_id': source_id,
        'display_name': name,
        'aliases': [],
        'category': category,
        'source_url': profile_account['url'],
        'name_source': profile_account['url'],
        'activity_source': profile_account['url'],
        'activity_evidence': 'direct_public_profile_verified_after_searxng_discovery',
        'activity_detail': activity,
        'activity_checked_at': today,
        'platform_accounts': [profile_account],
        'primary_platforms': [platform],
        'primary_platform_source': profile_account['url'],
        'primary_platform_evidence': 'direct_public_creator_profile',
        'searxng_discovered': True,
    }
    if platform == 'youtube':
        row['youtube_channel_id'] = source_id[8:]
    if platform == 'twitch':
        row['twitch_login'] = account['id']
    if category == 'AIVTuber':
        row['character_specific'] = True
    return candidate, row, 'verified'


def canonical_accounts(*groups):
    """Deduplicate platform accounts by canonical platform/account identity."""
    output = []
    seen = set()
    for group in groups:
        if not isinstance(group, list):
            continue
        for item in group:
            if not isinstance(item, dict):
                continue
            canonical = canonical_account(item.get('url'))
            if canonical:
                identity = (canonical['platform'], canonical['id'])
                normalized = canonical
            else:
                platform = item.get('platform')
                account_id = item.get('id')
                url = item.get('url')
                if not all(isinstance(v, str) and v for v in (platform, account_id, url)):
                    continue
                identity = (platform, account_id)
                normalized = {'platform': platform, 'id': account_id, 'url': url}
            if identity in seen:
                continue
            seen.add(identity)
            output.append(normalized)
    return output


def diverse_candidates(targets):
    """Check distinct search-result authors first without discarding any leads.

    Author labels affect ordering only; uploader resolution and direct profile
    verification remain mandatory even when two search results share a label.
    """
    seen = set()
    first, later = [], []
    for row in targets:
        author = str(row.get('candidate_author') or '').strip().casefold()
        identity = (urllib.parse.urlsplit(row['url']).hostname, author) if author else None
        if identity and identity in seen:
            later.append(row)
        else:
            first.append(row)
            if identity:
                seen.add(identity)
    return first + later


def merge_verified(rows):
    extra = read_js(EXTRA, 'VTUBER_EXTRA')
    original_size = EXTRA.stat().st_size
    by_id = {row['source_id']: dict(row) for row in extra}
    merged, account_index = existing_indexes()

    grouped = {}
    for row in rows:
        account = row['platform_accounts'][0]
        target = account_index.get((account['platform'], account['id']), row['source_id'])
        grouped.setdefault(target, []).append(row)

    added = enriched = 0
    for target, group in grouped.items():
        row = group[0]
        old = merged.get(target, {})
        patch = dict(by_id.get(target, {}))
        discovered_accounts = [item for candidate in group for item in candidate.get('platform_accounts', [])]

        if old:
            aliases = list(dict.fromkeys([*old.get('aliases', []), *patch.get('aliases', [])]))
            for candidate in group:
                name = candidate.get('display_name')
                if name and name != old.get('display_name') and name not in aliases:
                    aliases.append(name)
            if aliases:
                patch['aliases'] = aliases
            patch.setdefault('source_id', target)
            patch.setdefault('category', old.get('category') or row['category'])
            accounts = canonical_accounts(old.get('platform_accounts', []), patch.get('platform_accounts', []), discovered_accounts)
            if accounts:
                patch['platform_accounts'] = accounts
            for field in (
                'activity_source', 'activity_evidence', 'activity_checked_at',
                'primary_platforms', 'primary_platform_source',
                'primary_platform_evidence', 'youtube_channel_id', 'twitch_login',
            ):
                if row.get(field) and not old.get(field):
                    patch[field] = row[field]
            enriched += 1
        else:
            patch.update(row)
            patch['platform_accounts'] = canonical_accounts(discovered_accounts)
            aliases = []
            for candidate in group[1:]:
                name = candidate.get('display_name')
                if name and name != row.get('display_name') and name not in aliases:
                    aliases.append(name)
            if aliases:
                patch['aliases'] = aliases
            added += 1

        by_id[target] = patch
        merged.setdefault(target, {}).update(patch)
        for account in patch.get('platform_accounts', []):
            account_index[(account['platform'], account['id'])] = target

    content = '// Additive, source-linked VTuber/AIVTuber names and verified readings.\nwindow.VTUBER_EXTRA = ' + json.dumps(list(by_id.values()), ensure_ascii=False, separators=(',', ':')) + ';\n'
    encoded_size = len(content.encode('utf-8'))
    github_safe_limit = 90 * 1024 * 1024
    growth_limit = max(original_size * 2, original_size + 16 * 1024 * 1024)
    if encoded_size > github_safe_limit or encoded_size > growth_limit:
        raise ValueError(f'Refusing unexpected extra-data.js growth: {original_size} -> {encoded_size} bytes')

    tmp = EXTRA.with_suffix('.js.tmp')
    tmp.write_text(content, encoding='utf-8')
    tmp.replace(EXTRA)
    return added, enriched, len(grouped)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=200)
    parser.add_argument('--workers', type=int, default=5)
    parser.add_argument('--seconds', type=int, default=1200)
    parser.add_argument('--retry-unavailable', action='store_true', help='Retry profiles that previously failed with a temporary HTTP/network error')
    parser.add_argument('--recheck-classification', action='store_true', help='Recheck old fan/language exclusions once with the corrected classifier')
    args = parser.parse_args()
    backoff.load()
    HOST_BLOCKED.clear()
    queue = json.loads(QUEUE.read_text(encoding='utf-8')) if QUEUE.exists() else []
    recovered = sum(backoff.recover_legacy_candidate(row) for row in queue)
    allowed_statuses = {'pending_primary_confirmation'}
    if args.retry_unavailable:
        allowed_statuses.add('unavailable')
    PROFILE_CACHE.clear()
    targets = [r for r in queue if (r.get('review_status') in allowed_statuses or
               (args.recheck_classification and r.get('verifier_version', 1) < VERIFIER_VERSION and
                r.get('verification_status') in {'fan_or_clip_channel', 'no_direct_vtuber_evidence'}))
               and r.get('verification_status') not in {'unavailable:HTTP404', 'unavailable:HTTP410'}]
    targets.sort(key=lambda r: r.get('verified_at') or r.get('discovered_at') or '')
    targets = diverse_candidates(targets)
    deferred_hosts = sum(backoff.blocked(row['url']) for row in targets)
    targets = [row for row in targets if not backoff.blocked(row['url'])]
    targets = targets[:max(0, min(args.limit, 5000))]
    verified = []
    statuses = {}
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    deadline = time.monotonic() + max(1, args.seconds)
    attempted = 0

    def bounded_verify(row):
        if time.monotonic() >= deadline:
            return row, None, 'deferred_time_budget'
        return verify_one(row)

    with profile_cache(), ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as pool:
        futures = [pool.submit(bounded_verify, row) for row in targets]
        for future in as_completed(futures):
            candidate, record, status = future.result()
            if status == 'deferred_time_budget':
                continue
            if status == 'deferred_host_backoff':
                candidate.update(review_status='pending_primary_confirmation', verification_status=status)
                deferred_hosts += 1
                continue
            attempted += 1
            statuses[status] = statuses.get(status, 0) + 1
            candidate['verified_at'] = stamp
            candidate['verification_status'] = status
            candidate['verifier_version'] = VERIFIER_VERSION
            if record:
                verified.append(record)
                candidate['review_status'] = 'verified_direct_profile'
                candidate['published'] = True
                candidate['verified_source_id'] = record['source_id']
            elif status.startswith('unavailable:'):
                candidate['review_status'] = 'unavailable'
            else:
                candidate['review_status'] = 'not_confirmed'
                candidate['published'] = False

    added, enriched, unique_profiles = merge_verified(verified) if verified else (0, 0, 0)
    QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    backoff.save()
    report = {
        'schema': 2,
        'verifier_version': VERIFIER_VERSION,
        'updated_at': stamp,
        'candidates_total': len(queue),
        'attempted_this_run': attempted,
        'deferred_host_backoff': deferred_hosts,
        'recovered_backoff_candidates': recovered,
        'verified_this_run': len(verified),
        'verified_unique_profiles': unique_profiles,
        'new_public_records': added,
        'existing_records_enriched': enriched,
        'statuses': statuses,
        'policy': 'SearXNG discovery only; publication requires direct public creator/profile verification.',
    }
    previous = json.loads(REPORT.read_text(encoding='utf-8')) if REPORT.exists() else {}
    totals = previous.get('cumulative_since_checkpoint_fix', {})
    for key in ('attempted_this_run','verified_this_run','new_public_records','existing_records_enriched'):
        totals[key] = totals.get(key, 0) + report[key]
    report['cumulative_since_checkpoint_fix'] = totals
    report['queue_statuses'] = {status:sum(r.get('review_status') == status for r in queue)
        for status in sorted({r.get('review_status', 'unknown') for r in queue})}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
