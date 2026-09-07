"""Collect explicit readings only; never derive pronunciations from kanji or English."""
import datetime
import html
import json
import re
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urlparse


def fetch_reading(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'VName-reading-updater/1.0 (+https://github.com/Kirakun0328/vname-web)'})
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read(6 * 1024 * 1024 + 1)
    if len(raw) > 6 * 1024 * 1024:
        raise ValueError('Reading profile too large')
    return raw.decode('utf-8')

def kana(text):
    text = unicodedata.normalize('NFKC', text)
    text = ''.join(chr(ord(c)-96) if 'ァ' <= c <= 'ヶ' else c for c in text)
    text = re.sub(r'[\s・･•·]', '', text)
    return text if re.fullmatch(r'[ぁ-ゖー]+', text) else ''


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.descriptions = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and (a.get('property') == 'og:description' or a.get('name') == 'description'):
            self.descriptions.append(a.get('content', ''))


def explicit_profile_reading(document, name, channel_id):
    # Require this profile's linked channel and restrict extraction to profile metadata.
    if not re.search(r'youtube\.com/channel/' + re.escape(channel_id) + r'(?:["/?\s<]|$)', document):
        return ''
    parser = Metadata()
    parser.feed(document)
    found = set()
    # Accept an unambiguous full-name pronunciation only in a self-introduction.
    # Bare parentheses (e.g. nickname, affiliation) are deliberately not sufficient.
    pattern = re.compile(re.escape(name) + r'\s*[（(]([ぁ-ゖァ-ヶー\s・･•·]+)[）)](?:[」』])?\s*(?:と申します|といいます|と言います|です)')
    for description in parser.descriptions:
        for match in pattern.finditer(description):
            reading = kana(match[1])
            if reading:
                found.add(reading)
    return next(iter(found)) if len(found) == 1 else ''


def page_data(document):
    match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', document, re.S)
    if not match:
        raise ValueError('Official page structure changed')
    return json.loads(match[1])['props']['pageProps']


def official_reading(document, expected_name):
    record = page_data(document)['liverDetail']
    if record.get('name') != expected_name:
        raise ValueError('Official profile identity mismatch')
    value = kana(record.get('ruby', ''))
    if not value:
        raise ValueError('Official page has no explicit kana reading')
    return value, record.get('enName', '')


def refresh_readings(base, previous, fetch, official_limit=20, profile_limit=30):
    from update_dictionary import key
    today = datetime.date.today().isoformat()
    extra = {r['source_id']: dict(r) for r in previous}
    records = {r['source_id']: dict(r) for r in base}
    for r in previous:
        records.setdefault(r['source_id'], {}).update(r)
    by_name = {}
    for sid, r in records.items():
        for n in [r['display_name'], *r.get('aliases', [])]:
            by_name.setdefault(key(n), set()).add(sid)
    fetched = 0
    acquired = 0
    def save(sid, value, url, kind, english=''):
        nonlocal acquired
        patch = extra.setdefault(sid, {'source_id': sid})
        if value:
            if kind == 'profile_explicit' and records[sid].get('reading_source_kind') == 'official':
                return
            patch.update(reading=value, reading_source=url, reading_source_kind=kind)
            if english:
                patch.update(romanized_name=english, romanized_source=url)
            acquired += 1
        patch['reading_checked_at'] = today
    try:
        livers = page_data(fetch('https://www.nijisanji.jp/talents'))['allLivers']
        if not isinstance(livers, list) or len(livers) < 50:
            raise ValueError('Incomplete official talent list')
        targets = []
        for talent in livers:
            matched = by_name.get(key(talent['name']), set())
            # Multiple records with exactly the same full name may be different people.
            if len(matched) != 1 or not re.fullmatch(r'[a-z0-9-]+', talent.get('slug','')):
                continue
            sid = next(iter(matched))
            if records[sid].get('reading_checked_at') == today:
                continue
            targets.append((sid, talent))
        targets.sort(key=lambda x: records[x[0]].get('reading_checked_at', ''))
        def get_official(item):
            sid, talent = item
            url = 'https://www.nijisanji.jp/talents/l/' + talent['slug']
            try:
                value, english = official_reading(fetch(url), talent['name'])
                return sid, value, url, english
            except (OSError, ValueError, KeyError, TypeError) as error:
                print('Official reading unavailable:', talent['name'], type(error).__name__, flush=True)
                return None
        with ThreadPoolExecutor(max_workers=3) as pool:
            for result in pool.map(get_official, targets[:official_limit]):
                if result:
                    sid, value, url, english = result
                    save(sid, value, url, 'official', english)
                    fetched += 1
                    print('Official reading acquired:', records[sid]['display_name'], flush=True)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('Official reading source unavailable; previous readings retained:', type(error).__name__)
    targets = [(sid, r) for sid, r in records.items() if re.fullmatch(r'youtube:UC[\w-]{22}', sid)
               and extra.get(sid, {}).get('reading_checked_at') != today
               and r.get('reading_source_kind') != 'official']
    targets.sort(key=lambda x: x[1].get('reading_checked_at',''))
    def get_profile(item):
        sid, r = item
        url = 'https://vtuber-post.com/database_detail.html?id=' + sid.split(':',1)[1]
        try:
            document = fetch(url)
            value = explicit_profile_reading(document, r['display_name'], sid.split(':',1)[1])
            if r['display_name'] not in document:
                raise ValueError('Profile missing')
            return sid, value, url
        except (OSError, ValueError) as error:
            print('Profile reading unavailable:', sid, type(error).__name__, flush=True)
            return None
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(get_profile, targets[:profile_limit]):
            if result:
                sid, value, url = result
                save(sid, value, url, 'profile_explicit')
                fetched += 1
    print(f'Reading profiles checked: {fetched}; explicit readings obtained: {acquired}')
    return list(extra.values())
