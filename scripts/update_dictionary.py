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

def consolidate_duplicates(base, updated):
    from deduplicate_sources import deduplicate
    # `base` at this point also contains previous extras. Only on-disk base
    # and platform rows are immutable; stale extra identities may be removed.
    fixed = read_js(ROOT / 'data.js', 'VTUBER_DATA')
    platform_path = ROOT / 'platform-data.js'
    if platform_path.exists():
        fixed += read_js(platform_path, 'VTUBER_PLATFORMS')
    result = deduplicate(fixed, updated)
    removed = {r['source_id'] for r in updated} - {r['source_id'] for r in result}
    base[:] = [r for r in base if r['source_id'] not in removed]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Fetch and validate without writing')
    parser.add_argument('--full', action='store_true', help='Check every VTuber Post ranking page, including small channels')
    parser.add_argument('--skip-readings', action='store_true', help='Skip the optional reading refresh')
    parser.add_argument('--ai-only', action='store_true', help='Refresh AIVTuber sources only')
    parser.add_argument('--reviewed-only', action='store_true', help='Apply verified profiles and renames without network access')
    args = parser.parse_args()
    if args.ai_only and args.reviewed_only:
        parser.error('--ai-only and --reviewed-only cannot be combined')
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
    if args.reviewed_only:
        refresh_reviewed_only(base, previous, args)
        return
    if args.ai_only:
        refresh_ai_only(base, previous, args)
        return
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
    from aivtuber_sources import collect, merge_aivtubers, resolve_channels
    try:
        characters = collect(fetch_reading)
        resolved = resolve_channels(characters, fetch_reading)
        updated = merge_aivtubers(base, updated, characters, vdb, resolved=resolved)
        if not args.check:
            (ROOT / 'scripts/aivnav_channels.json').write_text(json.dumps(resolved, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('AIV Navi unavailable; existing tags and records retained:', type(error).__name__)
    from ai_directory_sources import refresh_ai_directories
    updated = refresh_ai_directories(base, updated, fetch_reading, report)
    from popularity_sources import refresh as refresh_popularity
    updated = refresh_popularity(fetch_reading, base, updated, report)
    if not args.skip_readings:
        updated = refresh_readings(base, updated, fetch_reading)
    from reviewed_sources import merge_reviewed
    updated = merge_reviewed(updated, base=base)
    updated = consolidate_duplicates(base, updated)
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
    report['aivtuber_records'] = sum(r.get('category') == 'AIVTuber' for r in eligible)
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

def refresh_ai_only(base, previous, args):
    from aivtuber_sources import collect, merge_aivtubers, resolve_channels
    from ai_directory_sources import refresh_ai_directories
    from reading_sources import fetch_reading
    path = ROOT / 'scripts/collection-report.json'
    report = json.loads(path.read_text()) if path.exists() else {}
    updated = previous
    try:
        characters = collect(fetch_reading)
        resolved = resolve_channels(characters, fetch_reading)
        updated = merge_aivtubers(base, updated, characters, {}, resolved=resolved)
        if not args.check:
            (ROOT / 'scripts/aivnav_channels.json').write_text(json.dumps(resolved, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        report['aivnav'] = {'source_records': len(characters), 'status': 'ok'}
    except (OSError, ValueError, KeyError, TypeError) as error:
        report['aivnav'] = {**report.get('aivnav', {}), 'status': 'unavailable', 'error': type(error).__name__}
    updated = refresh_ai_directories(base, updated, fetch_reading, report)
    from popularity_sources import refresh as refresh_popularity
    updated = refresh_popularity(fetch_reading, base, updated, report)
    from reviewed_sources import merge_reviewed
    updated = merge_reviewed(updated, base=base)
    updated = consolidate_duplicates(base, updated)
    merged = {r['source_id']: dict(r) for r in base}
    for r in updated:
        merged.setdefault(r['source_id'], {}).update(r)
    from broad_sources import preparing
    eligible = [r for r in merged.values() if r.get('listing_status') != 'predebut' and not preparing(r['display_name'])]
    report['aivtuber_records'] = sum(r.get('category') == 'AIVTuber' for r in eligible)
    report['records'] = {'stored': len(merged), 'listed': len(eligible), 'excluded_predebut': len(merged) - len(eligible),
                         'with_activity_source': sum(bool(r.get('activity_source')) for r in eligible)}
    print('AIVTuber records:', report['aivtuber_records'], flush=True)
    if args.check:
        return
    for target, content in [(ROOT / 'extra-data.js', '// Additive, source-linked VTuber/AIVTuber names and verified readings.\nwindow.VTUBER_EXTRA = ' + json.dumps(updated, ensure_ascii=False, separators=(',', ':')) + ';\n'),
                            (path, json.dumps(report, ensure_ascii=False, indent=2) + '\n')]:
        temporary = target.with_suffix(target.suffix + '.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(target)


def refresh_reviewed_only(base, previous, args):
    from reviewed_sources import merge_reviewed, reviewed_profiles
    from broad_sources import preparing
    reviewed = reviewed_profiles()
    updated = merge_reviewed(previous, reviewed, base=base)
    updated = consolidate_duplicates(base, updated)
    platform_path = ROOT / 'platform-data.js'
    platforms = read_js(platform_path, 'VTUBER_PLATFORMS') if platform_path.exists() else []
    platform_ids = {r['source_id'] for r in platforms}
    # The browser applies platform-data last. Reapply approved identity fields
    # there too when a platform collector has an older name for this account.
    approved_platforms = [r for r in reviewed if r['source_id'] in platform_ids]
    platforms = merge_reviewed(platforms, approved_platforms, base=base)
    merged = {r['source_id']: dict(r) for r in base}
    for row in [*updated, *platforms]:
        merged.setdefault(row['source_id'], {}).update(row)
    eligible = [r for r in merged.values() if r.get('listing_status') != 'predebut' and not preparing(r['display_name'])]
    report_path = ROOT / 'scripts/collection-report.json'
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    report['records'] = {'stored': len(merged), 'listed': len(eligible),
                         'excluded_predebut': len(merged)-len(eligible),
                         'with_activity_source': sum(bool(r.get('activity_source')) for r in eligible)}
    report['aivtuber_records'] = sum(r.get('category') == 'AIVTuber' for r in eligible)
    community = [r for r in reviewed if r.get('report_source')]
    report['community_profiles'] = {'reviewed_records': len(community),
                                    'checked_at': max((r['activity_checked_at'] for r in community), default=None),
                                    'coverage': 'publicly_accessible_quotes_and_replies_only',
                                    'all_quotes_checked': False,
                                    'source': 'https://x.com/Kiratchi0328/status/2096914177667567915'}
    print(f'Reviewed profiles: {len(reviewed)}; community profiles: {len(community)}; listed: {len(eligible)}')
    if args.check:
        return
    writes = [(ROOT / 'extra-data.js', '// Additive, source-linked VTuber/AIVTuber names and verified readings.\nwindow.VTUBER_EXTRA = ' + json.dumps(updated, ensure_ascii=False, separators=(',', ':')) + ';\n'),
              (report_path, json.dumps(report, ensure_ascii=False, indent=2)+'\n')]
    if platform_path.exists():
        writes.append((platform_path, '// Public V-liver identities and source-linked platform metadata.\nwindow.VTUBER_PLATFORMS = ' + json.dumps(platforms, ensure_ascii=False, separators=(',', ':')) + ';\n'))
    for path, content in writes:
        if path.exists() and path.read_text(encoding='utf-8') == content:
            continue
        temporary = path.with_suffix(path.suffix+'.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(path)


if __name__ == '__main__':
    main()
