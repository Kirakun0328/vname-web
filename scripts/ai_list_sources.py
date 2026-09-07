"""Read AITuberList's public, static directory without executing upstream JS.

Directory membership or an AI-generated tag alone is not enough: require an
explicit AI performer description and published content (not a future stream).
Keep channel identity separate from character identity when enriching names.
"""
import datetime
import json
import re
from urllib.parse import urljoin, urlsplit
from update_dictionary import key
from broad_sources import preparing
from platform_sources import canonical_account, record_accounts

SITE = 'https://aituberlist.net/'
AI_ROLE = re.compile(r'AI[\s-]*V?[\s-]*Tuber|AI[\s-]*(?:virtual|streamer)|AI.{0,8}(?:キャラ|バーチャル|버튜버)|人工知能|自律.{0,8}配信|Нейросетев\w*\s+стример', re.I)


def parse_bundle(document):
    # Only decode literal JSON.parse arguments, never evaluate a script.
    for match in re.finditer(r"JSON\.parse\('((?:\\.|[^'\\])*)'\)", document):
        def unescape(m):
            value = m[1]
            if value[0] in 'xu': return chr(int(value[1:], 16))
            if value in ("'", '\\'): return value
            raise ValueError('Unsupported JavaScript string escape')
        literal = re.sub(r"\\(x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|.)", unescape, match[1])
        literal = literal.encode('utf-16', 'surrogatepass').decode('utf-16')
        payload = json.loads(literal)
        rows = payload.get('B') if isinstance(payload, dict) else None
        if not isinstance(rows, list): continue
        if not 100 <= len(rows) <= 3000: raise ValueError('Incomplete AITuberList snapshot')
        if any(not isinstance(r, dict) or not isinstance(r.get('name'), str) for r in rows):
            raise ValueError('Invalid AITuberList record')
        return rows
    raise ValueError('Public AITuberList data missing')


def collect(fetch):
    document = fetch(SITE)
    bundles = re.findall(r'<script\b[^>]*\bsrc="(/_next/static/chunks/app/page-[\w-]+\.js)"', document)
    if len(set(bundles)) != 1: raise ValueError('Directory bundle changed')
    rows = parse_bundle(fetch(urljoin(SITE, bundles[0])))
    # The server-rendered total catches truncated bundles and deployment races.
    total = re.search(r'AITuber一覧・検索[（(](\d+)名', document)
    if not total or int(total[1]) != len(rows): raise ValueError('Directory total mismatch')
    return rows


def past_date(value, today):
    try:
        date = datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).date()
        return date.isoformat() if date <= today else None
    except (ValueError, TypeError, AttributeError): return None


def rows_from(items, today=None):
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    rows = []
    for item in items:
        name = item['name'].strip(); description = item.get('description') or ''
        if not name or len(name) > 300 or preparing(name) or not AI_ROLE.search(name+' '+description): continue
        if re.search(r'初配信(?:に向け|予定)|未デビュー|\bpre[ -]?debut\b', description, re.I): continue
        cid = item.get('youtubeChannelID', '')
        channel = canonical_account('https://www.youtube.com/channel/'+cid) if isinstance(cid, str) else None
        twitch = canonical_account(item.get('twitchURL'))
        accounts = [a for a in (channel, twitch) if a]
        if not accounts: continue
        published = []
        if channel:
            candidates = list(item.get('recentYoutubeVideos') or [])
            if item.get('isUpcoming') is False:
                candidates.append({'url': item.get('latestVideoUrl'), 'date': item.get('latestVideoDate')})
            for video in candidates:
                url = video.get('url') or ''; date = past_date(video.get('date'), today)
                if item.get('isUpcoming') is True and url == item.get('latestVideoUrl'): continue
                if date and video.get('isUpcoming') is not True and re.fullmatch(r'https://(?:www\.)?youtube\.com/(?:watch\?v=|shorts/)[\w-]{11}', url):
                    published.append((date, url))
        if twitch:
            date = past_date(item.get('twitchContentDate'), today)
            url = item.get('twitchContentUrl') or ''
            if date and re.fullmatch(r'https://(?:www\.)?twitch\.tv/videos/\d+', url): published.append((date, url))
            if item.get('twitchIsLive') is True: published.append((today.isoformat(), twitch['url']))
        if not published: continue
        slug = 'youtube-'+cid if channel else 'twitch-'+str(item.get('twitchUserID') or twitch['id'])
        source = SITE+'aitubers/'+slug+'/'
        handle = item.get('youtubeURL') or ''
        if channel and isinstance(handle, str) and re.fullmatch(r'@?[\w.-]+', handle):
            accounts.append(canonical_account('https://www.youtube.com/@'+handle.lstrip('@')))
        x = item.get('twitterID') or ''
        if re.fullmatch(r'@?\w+', x): accounts.append(canonical_account('https://x.com/'+x.lstrip('@')))
        row = {'source_id':'aituberlist:'+slug, 'display_name':name, 'source_url':source,
               'category':'AIVTuber', 'category_source':source,
               'activity_source':source, 'activity_evidence':'ai_profile_with_published_content',
               'activity_snapshot_at':max(published)[0], 'activity_content_url':max(published)[1],
               'platform_accounts':[a for a in accounts if a]}
        if channel: row['youtube_channel_id'] = cid
        icon = item.get('imageUrl') or ''
        if urlsplit(icon).scheme == 'https' and urlsplit(icon).hostname in ('yt3.ggpht.com', 'yt3.googleusercontent.com'):
            row.update(icon_url=icon, icon_source=source, icon_kind='channel')
        rows.append(row)
    if len({r['source_id'] for r in rows}) != len(rows): raise ValueError('Duplicate directory identity')
    return rows


def name_keys(row):
    variants = [row['display_name'], *row.get('aliases', [])]
    out = set()
    for name in variants:
        out.add(key(name))
        clean = re.sub(r'[【\[].*?[】\]]', '', name)
        clean = re.sub(r'\bAI[\s-]*V?[\s-]*Tuber\b|\bCh(?:annel)?\.?', '', clean, flags=re.I)
        out.add(key(clean))
        out.update(key(part) for part in re.split(r'\s+[/／|｜]\s+', clean) if part.strip())
    return out - {''}


def merge_rows(base, previous, rows):
    merged = {r['source_id']:dict(r) for r in base}
    extra = {r['source_id']:dict(r) for r in previous}
    for r in previous: merged.setdefault(r['source_id'], {}).update(r)
    index = {}
    for sid, r in merged.items():
        for a in record_accounts(r):
            if a['platform'] in ('youtube', 'twitch'): index.setdefault((a['platform'], a['id']), set()).add(sid)
    counts = {'new_records':0, 'matched_existing':0, 'ambiguous_skipped':0}
    for row in rows:
        linked = record_accounts(row)
        matches = set().union(*(index.get((a['platform'], a['id']), set()) for a in linked if a['platform'] in ('youtube','twitch')))
        compatible = {sid for sid in matches if name_keys(row) & name_keys(merged[sid])}
        if row['source_id'] in merged: sid = row['source_id']
        elif len(compatible) == 1: sid = next(iter(compatible))
        elif matches:
            # A directory's channel title must not relabel a different host or
            # collapse multiple characters sharing the same account.
            counts['ambiguous_skipped'] += 1; continue
        else: sid = row['source_id']
        old = merged.get(sid)
        counts['matched_existing' if old else 'new_records'] += 1
        patch = extra.setdefault(sid, {'source_id':sid})
        if not old:
            patch.update(row); patch.update(source_id=sid, reading='', romanized_name='')
            old = dict(patch); merged[sid] = old
        patch.update(category='AIVTuber', category_source=row['category_source'])
        patch['aliases'] = list(dict.fromkeys([*old.get('aliases', []), *([row['display_name']] if row['display_name'] != old['display_name'] else [])]))
        accounts = {(a['platform'], a['id']):a for a in record_accounts(old)}
        accounts.update({(a['platform'], a['id']):a for a in linked})
        patch['platform_accounts'] = list(accounts.values())
        patch['platform_sources'] = {**old.get('platform_sources', {}), **{a['platform']:row['source_url'] for a in linked}}
        for field in ('youtube_channel_id',):
            if row.get(field): patch[field] = row[field]
        if not old.get('activity_source'):
            for field in ('activity_source','activity_evidence','activity_snapshot_at','activity_content_url'): patch[field] = row[field]
        if row.get('icon_url') and not old.get('icon_url'):
            for field in ('icon_url','icon_source','icon_kind'): patch[field] = row[field]
        old.update(patch)
        for a in linked:
            if a['platform'] in ('youtube', 'twitch'): index.setdefault((a['platform'], a['id']), set()).add(sid)
    return list(extra.values()), counts


def refresh(fetch, base, previous, report):
    try:
        items = collect(fetch); rows = rows_from(items)
        updated, counts = merge_rows(base, previous, rows)
        report['aituberlist'] = {'source':SITE, 'source_records':len(items), 'verified_records':len(rows), **counts}
        print('AITuberList', report['aituberlist'], flush=True)
        return updated
    except (OSError, ValueError, UnicodeError, TypeError, KeyError) as error:
        report.setdefault('aituberlist', {})['last_error'] = type(error).__name__
        print('AITuberList unavailable; existing records retained', type(error).__name__, flush=True)
        return previous
