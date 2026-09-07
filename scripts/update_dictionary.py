"""Refresh additive records. Never execute upstream code or remove existing entries."""
import argparse
import html
import json
import re
import time
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_js(path, variable):
    text = path.read_text(encoding='utf-8')
    match = re.search(r'window\.' + re.escape(variable) + r'\s*=\s*(\[.*\])\s*;?\s*$', text, re.S)
    if not match:
        raise ValueError(f'Invalid local data: {path.name}')
    rows = json.loads(match[1])
    if not isinstance(rows, list) or any(not isinstance(r, dict) or not isinstance(r.get('source_id'), str) for r in rows):
        raise ValueError('Invalid records')
    if len({r['source_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate source IDs')
    return rows

def key(value):
    return ''.join(c for c in unicodedata.normalize('NFKC', value).lower() if c.isalnum())

def fetch(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'VName-dictionary-updater/1.0 (+https://github.com/Kirakun0328/vname-web)'})
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read(12 * 1024 * 1024 + 1)
            if len(raw) > 12 * 1024 * 1024:
                raise ValueError('Source exceeds size limit')
            return raw.decode('utf-8')
        except (OSError, UnicodeError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def parse_ranking(text):
    rows = []
    for uid, block in re.findall(r'<tr data-href="/user/([\w]+)">(.*?)</tr>', text, re.S):
        match = re.search(r'<img class="thumbnail" alt="([^"]+)"', block)
        if match:
            name = html.unescape(match[1]).strip()
            if name and len(name) <= 300:
                rows.append((uid, name))
    if len(rows) < 10:
        raise ValueError('Ranking unavailable or markup changed; keeping previous data')
    return rows

def expand(base, previous, vdb, rankings):
    vtbs = vdb.get('vtbs')
    if not isinstance(vtbs, list) or len(vtbs) < 5000:
        raise ValueError('Incomplete VDB; keeping previous data')
    merged = {r['source_id']: dict(r) for r in base}
    extra = {r['source_id']: dict(r) for r in previous}
    for r in previous:
        merged.setdefault(r['source_id'], {}).update(r)
    # Index stable accounts for cross-source identity checks.
    known_userlocal = set()
    for v in vtbs:
        if v.get('type') != 'vtuber':
            continue
        sid = v.get('uuid')
        names = v.get('name', {})
        if not isinstance(sid, str) or not isinstance(names, dict):
            raise ValueError('Malformed VDB record')
        accounts = v.get('accounts', [])
        known_userlocal.update(a['id'] for a in accounts if a.get('platform') == 'userlocal' and isinstance(a.get('id'), str))
        youtube_ids = ['youtube:' + a['id'] for a in accounts if a.get('platform') == 'youtube' and a.get('type') == 'official' and isinstance(a.get('id'), str)]
        target = sid if sid in merged else next((i for i in youtube_ids if i in merged), sid)
        variants = [x for k, x in names.items() if k not in ('default', 'extra') and isinstance(x, str)]
        variants += [x for x in names.get('extra', []) if isinstance(x, str)]
        variants = list(dict.fromkeys(x.strip() for x in variants if x.strip() and len(x) <= 300))
        if not variants:
            continue
        if target not in merged:
            display = names.get('jp') or names.get(names.get('default')) or variants[0]
            r = {'source_id': target, 'display_name': display, 'reading': '', 'romanized_name': names.get('en', ''), 'source_url': 'https://vdb.vtbs.moe/'}
            merged[target] = dict(r)
            extra[target] = r
        r = merged[target]
        if isinstance(names.get('en'), str) and names['en'].strip():
            english = names['en'].strip()
            patch = extra.setdefault(target, {'source_id': target})
            if not r.get('romanized_source') or r.get('romanized_source') == 'https://vdb.vtbs.moe/':
                patch.update(romanized_name=english, romanized_source='https://vdb.vtbs.moe/')
                r.update(romanized_name=english, romanized_source='https://vdb.vtbs.moe/')
        aliases = list(dict.fromkeys([*r.get('aliases', []), *(x for x in variants if x != r['display_name'])]))
        if aliases != r.get('aliases', []):
            extra.setdefault(target, {'source_id': target})['aliases'] = aliases
            r['aliases'] = aliases
    known_names = {key(n) for r in merged.values() for n in [r['display_name'], r.get('romanized_name', ''), *r.get('aliases', [])] if n}
    for uid, name in rankings:
        sid = 'userlocal:' + uid
        normalized = key(re.sub(r'\([^)]*\)', '', name))
        if sid in merged or uid in known_userlocal or not normalized:
            continue
        if any(normalized == n or (min(len(normalized), len(n)) >= 4 and (normalized in n or n in normalized)) for n in known_names):
            continue
        row = {'source_id': sid, 'display_name': name, 'reading': '', 'romanized_name': '', 'source_url': 'https://virtual-youtuber.userlocal.jp/user/' + uid}
        merged[sid] = row
        extra[sid] = row
        known_names.add(normalized)
    if len(merged) < len(base) or len(extra) - len(previous) > 2000:
        raise ValueError('Unexpected record count change; manual review required')
    return list(extra.values())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Fetch and validate without writing')
    args = parser.parse_args()
    base = read_js(ROOT / 'data.js', 'VTUBER_DATA')
    previous = read_js(ROOT / 'extra-data.js', 'VTUBER_EXTRA')
    vdb = json.loads(fetch('https://vdb.vtbs.moe/json/list.json'))
    rankings = []
    for page in range(1, 11):
        rankings.extend(parse_ranking(fetch(f'https://virtual-youtuber.userlocal.jp/document/ranking?page={page}')))
        time.sleep(1)
    updated = expand(base, previous, vdb, rankings)
    from reading_sources import refresh_readings, fetch_reading
    updated = refresh_readings(base, updated, fetch_reading)
    print(f'Extra records: {len(previous)} -> {len(updated)}')
    if args.check or updated == previous:
        return
    content = '// Additive updates from VTuber Database and User Local rankings (pages 1–10).\nwindow.VTUBER_EXTRA = ' + json.dumps(updated, ensure_ascii=False, separators=(',', ':')) + ';\n'
    target = ROOT / 'extra-data.js'
    temporary = target.with_suffix('.js.tmp')
    temporary.write_text(content, encoding='utf-8')
    temporary.replace(target)

if __name__ == '__main__':
    main()
