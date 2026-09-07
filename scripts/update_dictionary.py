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

def parse_ranking(text, page=None):
    rows = []
    for uid, block in re.findall(r'<tr data-href="/user/([\w]+)">(.*?)</tr>', text, re.S):
        match = re.search(r'<img class="thumbnail" alt="([^"]+)"', block)
        if match:
            name = html.unescape(match[1]).strip()
            if name and len(name) <= 300:
                rows.append((uid, name))
    if len(rows) < 10:
        raise ValueError('Ranking unavailable or markup changed; keeping previous data')
    if page is not None:
        ranks = re.findall(r'<strong>([\d,]+)位</strong>', text)
        if not ranks or int(ranks[0].replace(',', '')) != (page-1)*50+1:
            raise ValueError('Ranking returned the wrong page')
    return rows

def expand(base, previous, vdb, rankings):
    vtbs = vdb.get('vtbs')
    if not isinstance(vtbs, list) or len(vtbs) < 5000:
        raise ValueError('Incomplete VDB; keeping previous data')
    merged = {r['source_id']: dict(r) for r in base}
    extra = {r['source_id']: dict(r) for r in previous}
    for r in previous:
        merged.setdefault(r['source_id'], {}).update(r)
    for v in vtbs:
        if v.get('type') != 'vtuber':
            continue
        sid = v.get('uuid')
        names = v.get('name', {})
        if not isinstance(sid, str) or not isinstance(names, dict):
            raise ValueError('Malformed VDB record')
        accounts = v.get('accounts', [])
        youtube_ids = ['youtube:' + a['id'] for a in accounts if a.get('platform') == 'youtube' and a.get('type') == 'official' and isinstance(a.get('id'), str)]
        target = sid if sid in merged else next((i for i in youtube_ids if i in merged), sid)
        variants = [x for k, x in names.items() if k not in ('default', 'extra') and isinstance(x, str)]
        variants += [x for x in names.get('extra', []) if isinstance(x, str)]
        variants = list(dict.fromkeys(x.strip() for x in variants if x.strip() and len(x) <= 300))
        if not variants:
            continue
        if target not in merged:
            # A directory account by itself does not establish a debut. New
            # names enter via an activity-bearing source, then VDB enriches them.
            continue
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
    # Legacy ranking tuples have no channel identity or activity evidence.
    # Keep existing records; use the channel-linked VTuber Post collector for
    # additions instead of excluding people by fuzzy name similarity.
    if len(merged) < len(base) or len(extra) - len(previous) > 2000:
        raise ValueError('Unexpected record count change; manual review required')
    return list(extra.values())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Fetch and validate without writing')
    parser.add_argument('--full', action='store_true', help='Check every VTuber Post ranking page, including small channels')
    parser.add_argument('--skip-readings', action='store_true', help='Skip the optional reading refresh')
    args = parser.parse_args()
    base = read_js(ROOT / 'data.js', 'VTUBER_DATA')
    platform_path = ROOT / 'platform-data.js'
    if platform_path.exists():
        identities = {r['source_id']: dict(r) for r in base}
        # Include existing extra records before applying platform metadata.
        for row in read_js(ROOT / 'extra-data.js', 'VTUBER_EXTRA'):
            identities.setdefault(row['source_id'], {}).update(row)
        for row in read_js(platform_path, 'VTUBER_PLATFORMS'):
            identities.setdefault(row['source_id'], {}).update(row)
        base = list(identities.values())
    previous = read_js(ROOT / 'extra-data.js', 'VTUBER_EXTRA')
    vdb = json.loads(fetch('https://vdb.vtbs.moe/json/list.json'))
    updated = expand(base, previous, vdb, [])
    from broad_sources import collect_post, merge_post
    report_path = ROOT / 'scripts/collection-report.json'
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    from global_sources import refresh_global
    updated = refresh_global(base, updated, vdb, report)
    from legacy_sources import refresh_legacy
    updated = refresh_legacy(base, updated, vdb, report)
    from regional_sources import refresh_regional
    updated = refresh_regional(base, updated, vdb, report)
    from scholar_sources import refresh_scholar
    from reading_sources import fetch_reading
    try:
        updated, report['scholar_vtuber'] = refresh_scholar(base, updated, vdb, fetch_reading, report.get('scholar_vtuber'))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('Academic directory unavailable; existing records retained:', type(error).__name__, flush=True)
    try:
        rows, source_report = collect_post(full=args.full, state=report.get('vtuber_post'))
        updated, counts = merge_post(base, updated, rows, vdb)
        source_report.update(counts)
        report['vtuber_post'] = source_report
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('VTuber Post unavailable; existing records retained:', type(error).__name__, str(error), flush=True)
    from vstats_sources import refresh_vstats
    from reading_sources import refresh_readings
    try:
        updated, report['vstats'] = refresh_vstats(base, updated, vdb, fetch_reading)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('VSTATS unavailable; existing records retained:', type(error).__name__, flush=True)
    from liverfun_sources import refresh_liverfun
    try:
        updated, report['liverfun'] = refresh_liverfun(base, updated, vdb, fetch_reading, state=report.get('liverfun'))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('liverfun unavailable; existing records retained:', type(error).__name__, flush=True)
    from aivtuber_sources import collect, merge_aivtubers
    try:
        characters = collect(fetch_reading)
        updated = merge_aivtubers(base, updated, characters, vdb)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('AIV Navi unavailable; existing tags and records retained:', type(error).__name__)
    if not args.skip_readings:
        updated = refresh_readings(base, updated, fetch_reading)
    from reviewed_sources import merge_reviewed
    updated = merge_reviewed(updated)
    print(f'Extra records: {len(previous)} -> {len(updated)}')
    if args.check:
        return
    from broad_sources import preparing
    merged = {r['source_id']: dict(r) for r in base}
    for row in updated:
        merged.setdefault(row['source_id'], {}).update(row)
    eligible = [r for r in merged.values() if r.get('listing_status') != 'predebut' and not preparing(r['display_name'])]
    report['records'] = {'stored': len(merged), 'listed': len(eligible),
                         'excluded_predebut': len(merged)-len(eligible),
                         'with_activity_source': sum(bool(r.get('activity_source')) for r in eligible)}
    temporary_report = report_path.with_suffix('.json.tmp')
    temporary_report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temporary_report.replace(report_path)
    if updated == previous:
        return
    content = '// Additive, source-linked VTuber/AIVTuber names and verified readings.\nwindow.VTUBER_EXTRA = ' + json.dumps(updated, ensure_ascii=False, separators=(',', ':')) + ';\n'
    target = ROOT / 'extra-data.js'
    temporary = target.with_suffix('.js.tmp')
    temporary.write_text(content, encoding='utf-8')
    temporary.replace(target)

if __name__ == '__main__':
    main()
