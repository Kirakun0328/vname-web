"""AIV Navi's public character listing supplies classification, names and explicit kana."""
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from reading_sources import kana
from update_dictionary import key

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

def merge_aivtubers(base, previous, characters, vdb):
    merged = {r['source_id']: dict(r) for r in base}
    extra = {r['source_id']: dict(r) for r in previous}
    for r in previous:
        merged.setdefault(r['source_id'], {}).update(r)
    channels = {}
    for sid in merged:
        if sid.startswith('youtube:'):
            channels.setdefault(sid.split(':',1)[1], set()).add(sid)
    for r in vdb.get('vtbs', []):
        if r.get('uuid') in merged:
            for account in r.get('accounts', []):
                if account.get('platform') == 'youtube' and account.get('type') == 'official':
                    channels.setdefault(account['id'], set()).add(r['uuid'])
    mapping_file = Path(__file__).with_name('aivnav_channels.json')
    resolved = json.loads(mapping_file.read_text()) if mapping_file.exists() else {}
    added = tagged = 0
    for character in characters:
        name = character['name'].strip()
        cid = youtube_id(character.get('youtube_url'))
        known_channel = resolved.get(character['id'], {})
        if not cid and known_channel.get('youtube_url') == character.get('youtube_url') and re.fullmatch(r'UC[\w-]{22}', known_channel.get('channel_id','')):
            cid = known_channel['channel_id']
        source = SITE + character['id']
        previous_matches = {sid for sid,r in merged.items() if character['id'] in r.get('aivnav_ids',[])}
        targets = previous_matches or channels.get(cid, set())
        if not targets:
            # A matching name is insufficient identity evidence (e.g. AIずんだもん).
            sid = 'youtube:' + cid if cid else 'aivnav:' + character['id']
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
            patch['aivnav_ids'] = sorted(set(old.get('aivnav_ids', []) + patch.get('aivnav_ids', []) + [character['id']]))
            aliases = list(dict.fromkeys([*old.get('aliases', []), *patch.get('aliases', []), *([name] if name != old['display_name'] else [])]))
            if aliases:
                patch['aliases'] = aliases
            reading = kana(character.get('name_kana') or '')
            if reading and key(name) == key(old['display_name']) and (not old.get('reading_source') or old.get('reading_source_kind') == 'directory_explicit'):
                patch.update(reading=reading, reading_source=source, reading_source_kind='directory_explicit')
            old.update(patch)
            tagged += 1
    print(f'AIV Navi: {len(characters)} listings, {added} new records, {tagged} tagged records')
    return list(extra.values())
