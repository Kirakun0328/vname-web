"""Public VSTATS independent-channel directory, with profile activity checks."""
import datetime
import re
from concurrent.futures import ThreadPoolExecutor
from broad_sources import text, preparing, merge_post

DIRECTORY = 'https://www.vstats.jp/brands/1'


def parse_directory(document):
    rows = []
    pattern = r'<a href="/channels/1:(UC[\w-]{22})/overall"[^>]*>(.*?)</a>.*?<div class="fs-5">([\d,]+)</div>'
    for cid, name, subscribers in re.findall(pattern, document, re.S):
        name = text(name)
        if not name or len(name)>300:
            raise ValueError('Invalid VSTATS name')
        rows.append({'channel_id': cid, 'display_name': name, 'subscribers': int(subscribers.replace(',','')),
                     'source_url': 'https://www.vstats.jp/channels/1:'+cid+'/overall'})
    if not 100 <= len(rows) <= 5000 or len({r['channel_id'] for r in rows}) != len(rows):
        raise ValueError('Incomplete or changed VSTATS directory')
    return rows


def profile_views(document, cid):
    if not re.search(r'href="https://www\.youtube\.com/channel/'+re.escape(cid)+'"', document):
        raise ValueError('VSTATS channel identity mismatch')
    match = re.search(r'総再生回数</span>\s*<span[^>]*>([\d,]+)</span>', document)
    if not match:
        raise ValueError('VSTATS activity count missing')
    return int(match[1].replace(',',''))


def refresh_vstats(base, previous, vdb, fetch, limit=30):
    rows = parse_directory(fetch(DIRECTORY))
    known = {r['source_id'].removeprefix('youtube:') for r in base+previous if r['source_id'].startswith('youtube:')}
    known.update(r['youtube_channel_id'] for r in base+previous if r.get('youtube_channel_id'))
    for r in vdb.get('vtbs', []):
        known.update(a['id'] for a in r.get('accounts',[]) if a.get('platform')=='youtube' and a.get('type')=='official')
    targets = sorted((r for r in rows if r['channel_id'] not in known and not preparing(r['display_name'])),
                     key=lambda r:(r['subscribers']==0,r['subscribers'],r['channel_id']))[:limit]
    def get(row):
        try:
            return dict(row, views=profile_views(fetch(row['source_url']), row['channel_id']))
        except (OSError, ValueError, UnicodeError):
            return None
    with ThreadPoolExecutor(max_workers=3) as pool:
        checked = [r for r in pool.map(get, targets) if r is not None]
    updated, counts = merge_post(base, previous, checked, vdb, source_name='VSTATS')
    return updated, dict(counts, source=DIRECTORY, checked_at=datetime.date.today().isoformat(),
                         directory_channels=len(rows), checked_profiles=len(checked), failed_profiles=len(targets)-len(checked))
