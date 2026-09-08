"""Collect the long tail of public VTuber directories, without a subscriber floor.

VTuber Post pagination is a POST form, not a GET query. Validate the actual
rank on every page so a redirected/error page cannot masquerade as new data.
Only names, channel IDs, source URLs and activity evidence are persisted.
"""
import datetime
import html
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

POST_URL = 'https://vtuber-post.com/ranking_index.html'
PREDEBUT = re.compile(r'(?:[a-z]*v(?:irtual)?[\s-]*tuber\s*準備中|準備中\s*(?:個人勢)?\s*[a-z]*vtuber|(?<!再)デビュー準備中|(?<!再)デビュー前|(?:Vライバー|IRIAM|Avvy|REALITY)\s*準備中|準備中\s*Vライバー|未デビュー|\bpre[\s-]?debut\b)', re.I)


def preparing(name):
    return bool(PREDEBUT.search(name or ''))


def text(fragment):
    return html.unescape(re.sub(r'<[^>]*>', '', fragment)).strip()


def parse_post(document, page):
    if not isinstance(page, int) or not 0 <= page <= 1999:
        raise ValueError('Invalid page number')
    pages = [int(p) for p in re.findall(r'FormSubmit\((\d+)\)', document)]
    if not pages or max(pages) > 1999:
        raise ValueError('VTuber Post pagination unavailable')
    rows = []
    pattern = r'<p class="name">(.*?)</p>\s*<p class="regist">(.*?)</p>\s*<p class="increase">.*?</p>\s*<p class="play">(.*?)</p>'
    for block, subscribers, views in re.findall(pattern, document, re.S):
        link = re.search(r'<a href="(?:\.\./)?database_detail\.html\?id=(UC[\w-]{22})"[^>]*>(.*?)</a>', block, re.S)
        rank = re.search(r'([\d,]+)位', text(block))
        if not link or not rank:
            raise ValueError('Invalid VTuber Post identity or rank')
        name = text(link[2])
        nums = [re.fullmatch(r'([\d,]+)\s*[人回]', text(x)) for x in (subscribers, views)]
        if not name or len(name) > 300 or not all(nums):
            raise ValueError('Invalid VTuber Post name or activity counters')
        rows.append({'channel_id': link[1], 'display_name': name,
                     'rank': int(rank[1].replace(',', '')),
                     'subscribers': int(nums[0][1].replace(',', '')),
                     'views': int(nums[1][1].replace(',', ''))})
    if not rows or len(rows) > 25 or rows[0]['rank'] != page * 25 + 1:
        raise ValueError(f'VTuber Post returned the wrong/empty page for {page}')
    if [r['rank'] for r in rows] != list(range(page * 25 + 1, page * 25 + 1 + len(rows))):
        raise ValueError('Non-contiguous VTuber Post ranks')
    if page < max(pages) and len(rows) != 25:
        raise ValueError('Truncated VTuber Post page')
    if len({r['channel_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate channels in VTuber Post page')
    return rows, max(pages)


def fetch_post(page):
    from source_policy import check_fetch
    check_fetch(POST_URL)
    payload = urllib.parse.urlencode({'page_v': page, 'pageFlg': '1'}).encode()
    request = urllib.request.Request(POST_URL, data=payload, headers={
        'User-Agent': 'VName-dictionary-updater/2.0 (+https://github.com/Kirakun0328/vname-web)'})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError('VTuber Post page exceeds size limit')
            return raw.decode('utf-8')
        except OSError:
            if attempt:
                raise
            time.sleep(2)


def collect_post(fetch=fetch_post, full=False, batch_size=90, state=None):
    first, last = parse_post(fetch(0), 0)
    state = state or {}
    # Start at the small channels, then work back toward the top over daily runs.
    cursor = min(last, max(1, state.get('next_page', last)))
    pages = list(range(last, 0, -1)) if full else list(range(cursor, max(0, cursor-batch_size), -1))
    scan_pages = set(pages)
    next_page = min(pages)-1 if pages and min(pages)>1 else last
    pages = list(dict.fromkeys(pages + [p for p in state.get('retry_pages', [])[:20] if isinstance(p, int) and 1 <= p <= last]))
    records = list(first)
    successful = [0]
    failures = []
    def get(page):
        time.sleep(0.35)
        try:
            rows, reported_last = parse_post(fetch(page), page)
            if abs(reported_last - last) > 1:
                raise ValueError('Directory changed during collection')
            return page, rows, None
        except (OSError, ValueError, UnicodeError) as error:
            return page, [], type(error).__name__
    checked = []
    # Bounded batches allow a troubled source to stop without losing valid pages.
    # In particular, do not queue hundreds of requests after repeated failures.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for offset in range(0, len(pages), 16):
            batch = pages[offset:offset+16]
            batch_errors = 0
            for page, rows, error in pool.map(get, batch):
                checked.append(page)
                if error:
                    failures.append(page)
                    batch_errors += 1
                    print(f'VTuber Post page {page}: {error}; previous records retained', flush=True)
                else:
                    records.extend(rows)
                    successful.append(page)
            print(f'VTuber Post: checked {len(checked)+1}/{len(pages)+1} pages', flush=True)
            if batch_errors >= max(3, len(batch)*0.75):
                print('VTuber Post is unavailable on most pages; save valid results and resume later', flush=True)
                break
    scan_checked = set(checked) & scan_pages
    if scan_checked:
        next_page = min(scan_checked)-1 if min(scan_checked)>1 else last
    unique = {r['channel_id']: r for r in records}
    if len(unique) < len(records) * 0.97:
        raise ValueError('Unexpected duplicate pages/channels; refusing import')
    report = {'source': POST_URL, 'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'total_pages': last+1, 'checked_pages': len(successful), 'failed_pages': failures,
              'fetched_channels': len(unique), 'full_scan': full,
              'scan_complete': full and len(checked)==len(pages) and not failures,
              'next_page': next_page}
    # Retry failed pages in future batches rather than silently forgetting them.
    report['retry_pages'] = sorted(set(failures + state.get('retry_pages', [])) - set(successful))
    return list(unique.values()), report


def merge_post(base, previous, rows, vdb, source_name='VTuber Post'):
    merged = {r['source_id']: dict(r) for r in base}
    extra = {r['source_id']: dict(r) for r in previous}
    for r in previous:
        merged.setdefault(r['source_id'], {}).update(r)
    channels = {}
    for sid, record in merged.items():
        cid = sid.removeprefix('youtube:') if sid.startswith('youtube:') else record.get('youtube_channel_id')
        if cid:
            channels.setdefault(cid, set()).add(sid)
    for record in vdb.get('vtbs', []):
        if record.get('uuid') not in merged:
            continue
        for account in record.get('accounts', []):
            if account.get('platform') == 'youtube' and account.get('type') == 'official':
                channels.setdefault(account['id'], set()).add(record['uuid'])
    added = skipped = small = 0
    today = datetime.date.today().isoformat()
    for row in rows:
        cid, name = row['channel_id'], row['display_name']
        if not re.fullmatch(r'UC[\w-]{22}', cid) or not name.strip():
            raise ValueError('Invalid import identity')
        targets = channels.get(cid, set())
        # Subscriber count alone is not activity evidence. A published directory
        # entry with recorded video views is the minimum signal for this source.
        if preparing(name) or row['views'] <= 0:
            skipped += 1
            for sid in targets:
                if preparing(name):
                    extra.setdefault(sid, {'source_id': sid}).update(listing_status='predebut', listing_status_source=row.get('source_url', POST_URL))
            continue
        source = row.get('source_url') or 'https://vtuber-post.com/database_detail.html?id=' + cid
        if not targets:
            sid = 'youtube:' + cid
            rowdata = {'source_id': sid, 'display_name': name, 'reading': '', 'romanized_name': '', 'source_url': source}
            merged[sid] = rowdata
            extra[sid] = dict(rowdata)
            targets = {sid}
            channels[cid] = targets
            added += 1
            small += 0 < row['subscribers'] < 1000
        for sid in sorted(targets):
            old = merged[sid]
            patch = extra.setdefault(sid, {'source_id': sid})
            # Never merge people merely because their names look alike.
            aliases = list(dict.fromkeys([*old.get('aliases', []), *([name] if name != old['display_name'] else [])]))
            if aliases:
                patch['aliases'] = aliases
            patch.update(youtube_channel_id=cid, activity_source=source,
                         activity_evidence='directory_video_views', activity_checked_at=today)
            # A fresh, active profile can bring a formerly preparing record back.
            if old.get('listing_status') == 'predebut':
                patch['listing_status'] = 'active'
            if preparing(old['display_name']):
                patch['display_name'] = name
                patch['aliases'] = [n for n in aliases if not preparing(n)]
            old.update(patch)
    print(f'{source_name}: {added} added ({small} below 1,000 subscribers), {skipped} without activity/predebut', flush=True)
    return list(extra.values()), {'new_records': added, 'new_below_1000': small, 'skipped_without_activity_or_predebut': skipped}
