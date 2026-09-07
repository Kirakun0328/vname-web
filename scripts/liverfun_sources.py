"""Small-account VTubers with an explicit activity statement in their profile.

The directory's count is a sum of social followers, not YouTube subscribers.
Directory membership alone is insufficient: fans and preparing creators occur
in this source, so require both a VTuber self-description and active wording.
"""
import datetime
import json
import re
from concurrent.futures import ThreadPoolExecutor
from broad_sources import text, preparing
from update_dictionary import key

DIRECTORY = 'https://www.liverfun.jp/vtuber/'
ACTIVE = re.compile(r'配信中(?!心|止|断)|配信(?:を|も)?(?:して(?:い|おり)?ます|しております|してる|している)|(?:YouTube|Twitch|VTuber|Vライバー)[^。\n]{0,16}活動(?:中|しています|しております)', re.I)
ROLE = re.compile(r'(?:個人勢|新人|系|として|[｜|@＠ /])?[a-z]*v(?:irtual)?[\s-]*tuber|Vライバー', re.I)


def parse_directory(document):
    rows = []
    for path, block in re.findall(r'<a[^>]+href="(/vtuber/[^/\"]+/)"[^>]*>(.*?)</a>', document, re.S):
        name = re.search(r'<span class="truncate text-\[14px\] font-semibold leading-snug">(.*?)</span>', block)
        count = re.search(r'([\d,]+)\s*$', text(block))
        if name and count:
            rows.append({'source_url': 'https://www.liverfun.jp'+path,
                         'display_name': text(name[1]), 'followers': int(count[1].replace(',', ''))})
    if not 100 <= len(rows) <= 10000 or len({r['source_url'] for r in rows}) != len(rows):
        raise ValueError('Incomplete or changed liverfun directory')
    return rows


def parse_profile(document, row):
    canonical = re.search(r'<link rel="canonical" href="([^"]+)"', document)
    if not canonical or canonical[1] != row['source_url']:
        raise ValueError('liverfun profile identity mismatch')
    profiles = []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', document, re.S):
        item = json.loads(block)
        if item.get('@type') == 'Person':
            profiles.append(item)
    if len(profiles) != 1:
        raise ValueError('liverfun person metadata missing')
    person = profiles[0]
    name, description = person.get('name', ''), person.get('description', '')
    combined = name+'\n'+description
    # A VTuber fan's biography may mention VTubers. Require the role in the
    # creator's name, or a first-person role + actual broadcasting statement.
    role = ROLE.search(name) or re.search(r'(?:個人勢|新人|系)[a-z]*vtuber|vtuber(?:として|です|[、。！!｜|￤])', description, re.I)
    if (not name or len(name)>300 or not role or preparing(combined)
            or re.search(r'準備中|初配信予定|デビュー予定', combined)
            or re.search(r'(?:\d{1,2}[月/.-]\d{1,2}.*(?:デビュー|初配信)|(?:デビュー|初配信).*\d{1,2}[月/.-]\d{1,2})', name)
            or not ACTIVE.search(description)):
        return None
    accounts = [u for u in person.get('sameAs', []) if isinstance(u, str)]
    social = next((u for u in accounts if re.fullmatch(r'https://(?:x|twitter)\.com/[\w]+/?', u)), None)
    cid = next((m[1] for u in accounts if (m:=re.fullmatch(r'https://www\.youtube\.com/channel/(UC[\w-]{22})/?', u))), None)
    if not social and not cid:
        return None
    return dict(row, display_name=name, twitter_url=social, youtube_channel_id=cid)


def merge_profiles(base, previous, rows, vdb):
    merged = {r['source_id']:dict(r) for r in base}
    extra = {r['source_id']:dict(r) for r in previous}
    for r in previous:
        merged.setdefault(r['source_id'], {}).update(r)
    names = {key(n) for r in merged.values() for n in [r['display_name'], *r.get('aliases', [])]}
    accounts = {r.get('twitter_url','').rstrip('/').rsplit('/',1)[-1].lower():sid for sid,r in merged.items() if r.get('twitter_url')}
    channels = {r.get('youtube_channel_id') or sid.removeprefix('youtube:'):sid for sid,r in merged.items() if r.get('youtube_channel_id') or sid.startswith('youtube:')}
    for record in vdb.get('vtbs', []):
        if record.get('uuid') not in merged:
            continue
        for account in record.get('accounts', []):
            if account.get('type') == 'official' and account.get('platform') == 'twitter':
                accounts[str(account['id']).lower()] = record['uuid']
    added = skipped = 0
    for row in rows:
        if not row:
            skipped += 1
            continue
        slug = row['source_url'].rstrip('/').rsplit('/',1)[-1]
        twitter = (row.get('twitter_url') or '').rstrip('/').rsplit('/',1)[-1].lower()
        sid = channels.get(row.get('youtube_channel_id')) or accounts.get(twitter) or 'liverfun:'+slug
        if sid not in merged and key(row['display_name']) in names:
            # An exact known name without a matching account is ambiguous.
            # Do not invent identity links or duplicate it from this source.
            skipped += 1
            continue
        if sid not in merged:
            extra[sid] = {'source_id':sid, 'display_name':row['display_name'], 'reading':'', 'romanized_name':'', 'source_url':row['source_url']}
            merged[sid] = dict(extra[sid])
            names.add(key(row['display_name']))
            added += 1
        patch = extra.setdefault(sid, {'source_id':sid})
        patch.update(activity_source=row['source_url'], activity_evidence='profile_explicit_broadcasting', activity_checked_at=datetime.date.today().isoformat())
        for field in ['twitter_url','youtube_channel_id']:
            if row.get(field):
                patch[field] = row[field]
        merged[sid].update(patch)
        if twitter:
            accounts[twitter] = sid
        if row.get('youtube_channel_id'):
            channels[row['youtube_channel_id']] = sid
    return list(extra.values()), {'new_records':added, 'skipped_unconfirmed_or_duplicate':skipped}


def refresh_liverfun(base, previous, vdb, fetch, state=None, limit=30):
    rows = [r for r in parse_directory(fetch(DIRECTORY)) if 0<r['followers']<1000 and not preparing(r['display_name'])]
    state = state or {}
    start = min(max(0, state.get('next_index',0)), max(0,len(rows)-1))
    targets = rows[start:start+limit]
    def get(row):
        try:
            return True, parse_profile(fetch(row['source_url']), row)
        except (OSError, ValueError, UnicodeError):
            return False, None
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(get, targets))
    updated, counts = merge_profiles(base, previous, [r for ok,r in results if ok], vdb)
    return updated, dict(counts, source=DIRECTORY, checked_at=datetime.date.today().isoformat(),
                         next_index=(start+len(targets))%max(1,len(rows)), small_account_candidates=len(rows),
                         checked_profiles=sum(ok for ok,r in results), failed_profiles=sum(not ok for ok,r in results),
                         size_measure='combined_social_followers_below_1000')
