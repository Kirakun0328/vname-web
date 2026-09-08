"""AIV Navi's public character listing supplies classification, names and explicit kana."""
import json
import re
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from reading_sources import kana
from update_dictionary import key
from broad_sources import preparing

API = 'https://aiv-api.nyagsicapp.com/api/characters?page='
SITE = 'https://aiv.nyagsicapp.com/characters/'

def parse_page(text, page):
    response = json.loads(text)
    data = response.get('data', {})
    if response.get('success') is not True or data.get('page') != page or not isinstance(data.get('items'), list):
        raise ValueError('Invalid AIV Navi response')
    if not isinstance(data.get('totalPages'), int) or not 1 <= data['totalPages'] <= 100:
        raise ValueError('Unexpected AIV Navi pagination')
    for r in data['items']:
        if not isinstance(r, dict) or not re.fullmatch(r'char-[\w-]+', r.get('id', '')) or not isinstance(r.get('name'), str) or not r['name'].strip():
            raise ValueError('Invalid AIV Navi character')
    return data

def collect(fetch):
    first = parse_page(fetch(API + '1'), 1)
    pages = first['totalPages']
    def get_page(page):
        data = parse_page(fetch(API + str(page)), page)
        if data['totalPages'] != pages or data.get('total') != first.get('total'):
            raise ValueError('AIV Navi changed during collection; retry next run')
        return data['items']
    rows = list(first['items'])
    with ThreadPoolExecutor(max_workers=3) as pool:
        for items in pool.map(get_page, range(2, pages + 1)):
            rows.extend(items)
    if len(rows) != first.get('total') or len({r['id'] for r in rows}) != len(rows) or not rows:
        raise ValueError('Incomplete AIV Navi snapshot')
    return rows

def youtube_id(url):
    if not isinstance(url, str):
        return None
    parsed = urlparse(url)
    if parsed.scheme not in ('http','https') or parsed.hostname not in ('youtube.com','www.youtube.com','m.youtube.com'):
        return None
    match = re.fullmatch(r'/channel/(UC[\w-]{22})/?', parsed.path)
    return match[1] if match else None

def resolve_channels(characters, fetch, limit=30):
    from channel_sources import youtube_profile
    from platform_sources import canonical_account
    path = Path(__file__).with_name('aivnav_channels.json')
    resolved = json.loads(path.read_text()) if path.exists() else {}
    targets = []
    retry_before = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    for c in characters:
        account = canonical_account(c.get('youtube_url'))
        cached = resolved.get(c['id'], {})
        complete = cached.get('youtube_url') == c.get('youtube_url') and re.fullmatch(r'UC[\w-]{22}', cached.get('channel_id', ''))
        if (account and account['platform'] == 'youtube' and account['id'].startswith('@')
                and not complete and cached.get('checked_at', '') < retry_before):
            targets.append((c, account))
    targets.sort(key=lambda pair: resolved.get(pair[0]['id'], {}).get('checked_at', ''))
    def get(pair):
        c, account = pair
        try:
            profile = youtube_profile(fetch(account['url']), account['id'])
            return c['id'], {'youtube_url': c['youtube_url'], 'channel_id': profile['channel_id'],
                             'channel_title': profile['name'], 'verified_url': account['url'], 'checked_at': datetime.date.today().isoformat()}
        except (OSError, ValueError, KeyError, TypeError):
            return c['id'], {'youtube_url': c['youtube_url'], 'checked_at': datetime.date.today().isoformat()}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(get, targets[:limit]):
            if result:
                resolved[result[0]] = result[1]
    return resolved


def merge_aivtubers(base, previous, characters, vdb, resolved=None):
    from platform_sources import canonical_account, record_accounts
    merged = {r['source_id']: dict(r) for r in base}
    extra = {r['source_id']: dict(r) for r in previous}
    for r in previous:
        merged.setdefault(r['source_id'], {}).update(r)
    channels = {}
    for sid, row in merged.items():
        for account in record_accounts(row):
            if account['platform']=='youtube' and account['id'].startswith('channel/'):
                channels.setdefault(account['id'][8:], set()).add(sid)
    for r in vdb.get('vtbs', []):
        if r.get('uuid') in merged:
            for account in r.get('accounts', []):
                if account.get('platform') == 'youtube' and account.get('type') == 'official':
                    channels.setdefault(account['id'], set()).add(r['uuid'])
    mapping_file = Path(__file__).with_name('aivnav_channels.json')
    if resolved is None:
        resolved = json.loads(mapping_file.read_text()) if mapping_file.exists() else {}
    added = tagged = 0
    for character in characters:
        name = character['name'].strip()
        description = (character.get('description') or '') + '\n' + (character.get('profile') or '')
        if preparing(name):
            continue
        activity = bool(re.search(r'活動中|活動してい|配信中|配信してい|配信を行|配信しています|投稿してい|投稿しています|配信を投稿|streaming|streams on|活動停止中|活動の他にリアル出展|配信をしてい|放送され', description, re.I))
        cid = youtube_id(character.get('youtube_url'))
        known_channel = resolved.get(character['id'], {})
        if not cid and known_channel.get('youtube_url') == character.get('youtube_url') and re.fullmatch(r'UC[\w-]{22}', known_channel.get('channel_id','')):
            cid = known_channel['channel_id']
        source = SITE + character['id']
        previous_matches = {sid for sid,r in merged.items() if character['id'] in r.get('aivnav_ids',[])}
        # Channel identity is necessary but not sufficient: a human host and
        # multiple AI characters can share a broadcast. Require name agreement
        # as well, and never merge on names without that channel evidence.
        variants = list(dict.fromkeys([name,*[s.strip() for s in re.split(r'\s*[/／]\s*',name) if s.strip()]]))
        name_keys = {key(s) for s in variants}
        compatible = {sid for sid in channels.get(cid,set()) if not sid.startswith('aivnav:')
                      and name_keys.intersection(key(s) for s in [merged[sid]['display_name'],*merged[sid].get('aliases',[])])}
        targets = previous_matches
        if len(compatible)==1 and all(sid in compatible or sid=='aivnav:'+character['id'] for sid in previous_matches):
            targets = compatible
            # Retire only this directory's duplicate stub, preserving the
            # existing channel-backed record and its original display name.
            for sid in previous_matches-compatible:
                merged.pop(sid,None)
                extra.pop(sid,None)
        if not targets:
            if not activity:
                continue
            # A matching name is insufficient identity evidence (e.g. AIずんだもん).
            sid = 'youtube:' + cid if cid and not channels.get(cid) else 'aivnav:' + character['id']
            targets = {sid}
            row = {'source_id': sid, 'display_name': name, 'reading': '', 'romanized_name': '', 'source_url': source}
            merged[sid] = row
            extra[sid] = dict(row)
            added += 1
            if cid:
                channels.setdefault(cid, set()).add(sid)
        for sid in sorted(targets):
            old = merged[sid]
            patch = extra.setdefault(sid, {'source_id': sid})
            patch.update(category='AIVTuber', category_source=source)
            website = character.get('website_url')
            if isinstance(website, str):
                parsed_site = urlparse(website)
                if parsed_site.scheme in ('http', 'https') and parsed_site.hostname and not parsed_site.username and not parsed_site.password:
                    patch.update(official_website=website, official_website_source=source)
            linked = [a for field in ('youtube_url','twitter_url','website_url')
                      if (a:=canonical_account(character.get(field)))]
            if cid:
                linked.append(canonical_account('https://www.youtube.com/channel/'+cid))
                patch['youtube_channel_id']=cid
                handle=canonical_account(character.get('youtube_url'))
                if handle and handle['platform']=='youtube' and handle['id'].startswith('@'):
                    patch['youtube_handle']=handle['id']
            accounts={(a['platform'],a['id']):a for a in record_accounts(old)}
            accounts.update({(a['platform'],a['id']):a for a in linked})
            if accounts:
                patch['platform_accounts']=list(accounts.values())
                patch['platform_sources']={**old.get('platform_sources',{}),**{a['platform']:source for a in linked}}
            if activity and not old.get('activity_source'):
                patch.update(activity_source=source, activity_evidence='directory_self_description', activity_checked_at=datetime.date.today().isoformat())
            patch['aivnav_ids'] = sorted(set(old.get('aivnav_ids', []) + patch.get('aivnav_ids', []) + [character['id']]))
            aliases = list(dict.fromkeys([*old.get('aliases', []), *patch.get('aliases', []), *[s for s in variants if s != old['display_name']]]))
            if aliases:
                patch['aliases'] = aliases
            reading = kana(character.get('name_kana') or '')
            if reading and key(name) == key(old['display_name']) and (not old.get('reading_source') or old.get('reading_source_kind') == 'directory_explicit'):
                patch.update(reading=reading, reading_source=source, reading_source_kind='directory_explicit')
            old.update(patch)
            tagged += 1
    print(f'AIV Navi: {len(characters)} listings, {added} new records, {tagged} tagged records')
    return list(extra.values())
