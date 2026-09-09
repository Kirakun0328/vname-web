"""Verify SearXNG-discovered leads against direct public creator profiles.

Search results are never publication evidence. YouTube video leads are resolved
to their uploader channel first. A public record is created only after the
channel/profile page itself yields a usable identity plus VTuber/V-liver
evidence (or is an avatar-first platform profile such as IRIAM/REALITY/Avvy).
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from platform_sources import canonical_account
from update_dictionary import read_js

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / 'scripts' / 'searxng-candidates.json'
REPORT = ROOT / 'scripts' / 'searxng-verification-report.json'
EXTRA = ROOT / 'extra-data.js'

VTUBER = re.compile(r'\bvtuber\b|v[- ]?tuber|virtual\s+youtuber|バーチャル\s*youtuber|バーチャルYouTuber|ＶＴｕｂｅｒ|Vライバー|Ｖライバー|バーチャルライバー|vliver|v-liver|aivtuber|ai\s*vtuber|AIライバー', re.I)
AIV = re.compile(r'aivtuber|ai\s*vtuber|ai\s*v[- ]?tuber|AIライバー|AI\s*Vライバー', re.I)
VLIVER = re.compile(r'Vライバー|Ｖライバー|バーチャルライバー|vliver|v-liver', re.I)
REJECT = re.compile(r'切り抜き|切抜|クリップ|まとめ|翻訳|非公式|ファン(?:チャンネル|ch)?|応援ch|clips?|clipping|highlights?|compilat(?:ion|ions)|reaction|reacts?|fan\s*(?:channel|ch)?|archive|vod\s*channel|eng\s*sub|subbed', re.I)
PREDEBUT = re.compile(r'VTuber\s*準備中|Vライバー\s*準備中|デビュー準備中|初配信予定|デビュー予定|pre[- ]?debut', re.I)
ENDED = re.compile(r'活動終了|活動を終了|引退しました|卒業しました|配信活動を終了', re.I)
NATIVE_V = {'iriam', 'reality', 'avvy'}
VIDEO_RE = re.compile(r'^[\w-]{11}$')
CHANNEL_RE = re.compile(r'^UC[\w-]{22}$')


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
    request = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; VName-primary-verifier/1.0; +https://github.com/Kirakun0328/vname-web)',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.5',
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
        ctype = response.headers.get('content-type', '')
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
        document = fetch_page(url)
    except (OSError, ValueError, UnicodeError) as error:
        return candidate, None, 'unavailable:' + type(error).__name__

    title = title_of(document)
    description = description_of(document)
    searchable = clean_text(title + ' ' + description + ' ' + re.sub(r'<[^>]+>', ' ', document[:700000]))
    if PREDEBUT.search(searchable):
        return candidate, None, 'predebut'
    if ENDED.search(searchable):
        return candidate, None, 'ended'
    if REJECT.search(title + ' ' + description):
        return candidate, None, 'fan_or_clip_channel'

    platform = account['platform']
    if platform not in NATIVE_V and not VTUBER.search(searchable):
        return candidate, None, 'no_direct_vtuber_evidence'
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
    parser.add_argument('--retry-unavailable', action='store_true', help='Retry profiles that previously failed with a temporary HTTP/network error')
    args = parser.parse_args()
    queue = json.loads(QUEUE.read_text(encoding='utf-8')) if QUEUE.exists() else []
    allowed_statuses = {'pending_primary_confirmation'}
    if args.retry_unavailable:
        allowed_statuses.add('unavailable')
    targets = [r for r in queue if r.get('review_status') in allowed_statuses]
    targets.sort(key=lambda r: r.get('verified_at') or r.get('discovered_at') or '')
    targets = targets[:max(0, min(args.limit, 1500))]
    verified = []
    statuses = {}
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as pool:
        futures = [pool.submit(verify_one, row) for row in targets]
        for future in as_completed(futures):
            candidate, record, status = future.result()
            statuses[status] = statuses.get(status, 0) + 1
            candidate['verified_at'] = stamp
            candidate['verification_status'] = status
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
    report = {
        'schema': 2,
        'updated_at': stamp,
        'candidates_total': len(queue),
        'attempted_this_run': len(targets),
        'verified_this_run': len(verified),
        'verified_unique_profiles': unique_profiles,
        'new_public_records': added,
        'existing_records_enriched': enriched,
        'statuses': statuses,
        'policy': 'SearXNG discovery only; publication requires direct public creator/profile verification.',
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
