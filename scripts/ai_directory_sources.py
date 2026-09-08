"""Additive AITuberList, FC2 and reviewed Kedamasuzume introductions.

Upstream JavaScript is parsed as a string literal and JSON, never executed.
Only identity facts, evidence links are persisted.
"""
import datetime
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from broad_sources import preparing, text
from platform_sources import canonical_account, record_accounts
from update_dictionary import key
from channel_sources import youtube_profile

LIST = 'https://aituberlist.net/'
FC2 = 'https://aituber.web.fc2.com/channels.html'
AI_NAME = re.compile(r'AI\s*V?Tuber|AIVtuber|AIチューバー|AIずんだもん', re.I)


from ai_list_sources import collect as collect_list, parse_bundle, rows_from


def parse_list(items, today=None):
    rows = rows_from(items, today)
    raw = {i.get('youtubeChannelID') or (i.get('twitchLogin') or '').lower(): i for i in items}
    for row in rows:
        ident = row.get('youtube_channel_id') or next((a['id'] for a in row['platform_accounts'] if a['platform'] == 'twitch'), '')
        item = raw.get(ident, {})
        row['_requires_character_match'] = '一部AITuber' in item.get('tags', []) and not AI_NAME.search(row['display_name'])
    from popularity_sources import list_counts
    metrics = list_counts(items)
    for row in rows:
        accounts = {(a['platform'], a['id']) for a in record_accounts(row)}
        row['audience_metrics'] = [m for m in metrics if (m['platform'], m['account_id']) in accounts]
    return rows, {'source_records': len(items), 'eligible_records': len(rows), 'excluded_unconfirmed_or_preparing': len(items) - len(rows)}


def name_keys(row):
    variants = [row.get('display_name', ''), *row.get('aliases', [])]
    keys = {key(n) for n in variants if n}
    for name in variants:
        clean = re.sub(r'[【\[].*?[】\]]', '', name)
        clean = re.sub(r'(?i)\b(?:AI\s*V?Tuber|V?Tuber|Ch(?:annel)?)\b\.?', '', clean)
        for part in re.split(r'\s*[/／|｜]\s*', clean):
            if part.strip():
                keys.add(key(part))
    return keys - {''}


def merge_ai(base, previous, rows):
    merged = {r['source_id']: dict(r) for r in base}
    extra = {r['source_id']: dict(r) for r in previous}
    for r in previous:
        merged.setdefault(r['source_id'], {}).update(r)
    index = {}
    profiles = {}
    def index_row(sid, row):
        for a in record_accounts(row):
            # An X account often belongs to the developer of several personas.
            if a['platform'] in ('youtube', 'twitch'):
                index.setdefault((a['platform'], a['id']), set()).add(sid)
        for source in row.get('source_profiles', []):
            profiles.setdefault(source, set()).add(sid)
    for sid, row in merged.items():
        index_row(sid, row)
    added = matched = ambiguous = mixed = 0
    for row in rows:
        if preparing(row['display_name']) or not row.get('activity_source'):
            continue
        candidates = set()
        for a in record_accounts(row):
            candidates.update(index.get((a['platform'], a['id']), set()))
        compatible = {sid for sid in candidates if name_keys(row) & name_keys(merged[sid])}
        if row.get('_requires_character_match') and not any(merged[sid].get('category') == 'AIVTuber' for sid in compatible):
            mixed += 1
            continue
        previous_targets = {sid for sid in profiles.get(row['source_url'], set()) if name_keys(row) & name_keys(merged[sid])}
        if row['source_id'] in merged:
            previous_targets = previous_targets | {row['source_id']}
        targets = previous_targets or compatible
        if len(targets) > 1:
            ambiguous += 1
            continue
        if targets:
            sid = next(iter(targets))
            matched += 1
        else:
            if candidates and not row.get('character_specific'):
                ambiguous += 1
                continue
            sid = row['source_id']
            # A fresh channel-backed name uses the established channel ID form.
            if row.get('youtube_channel_id') and not candidates and not row.get('character_specific'):
                sid = 'youtube:' + row['youtube_channel_id']
            merged[sid] = {'source_id': sid, 'display_name': row['display_name'], 'reading': '', 'romanized_name': '', 'source_url': row['source_url']}
            extra[sid] = dict(merged[sid])
            added += 1
        old = merged[sid]
        patch = extra.setdefault(sid, {'source_id': sid})
        patch.update(category='AIVTuber')
        # Prioritize the explicitly reviewed introduction over directory tags.
        if not str(old.get('category_source', '')).startswith('https://x.com/kedamasuzume/status/'):
            patch['category_source'] = row['category_source']
        aliases = list(dict.fromkeys([*old.get('aliases', []), row['display_name'], *row.get('aliases', [])]))
        patch['aliases'] = [n for n in aliases if n != old['display_name']]
        patch['source_profiles'] = list(dict.fromkeys([*old.get('source_profiles', []), row['source_url']]))
        accounts = {(a['platform'], a['id']): a for a in record_accounts(old)}
        accounts.update({(a['platform'], a['id']): a for a in record_accounts(row)})
        patch['platform_accounts'] = list(accounts.values())
        for field in ('youtube_channel_id', 'twitch_login', 'official_website', 'official_website_source', 'audience_metrics'):
            if row.get(field):
                patch[field] = row[field]
        if not old.get('activity_source'):
            for field in ('activity_source', 'activity_evidence', 'activity_content_url'):
                if row.get(field):
                    patch[field] = row[field]
            patch['activity_checked_at'] = datetime.date.today().isoformat()
        if row.get('reading_source') and not old.get('reading_source') and key(old['display_name']) == key(row['display_name']):
            for field in ('reading', 'reading_source', 'reading_source_kind'):
                patch[field] = row[field]
        old.update(patch)
        index_row(sid, old)
    return list(extra.values()), {'new_records': added, 'matched_records': matched, 'ambiguous_records': ambiguous,
                                 'mixed_or_unconfirmed_character': mixed}


def parse_fc2(document):
    count = re.search(r'>(\d+) チャンネル<', document)
    rows = []
    for block in re.findall(r'<div class="stream-row"[^>]*>(.*?)</div>', document, re.S):
        name = re.search(r'<(?:span|a)\b[^>]*style="flex:1;"[^>]*>(.*?)</(?:span|a)>', block, re.S)
        cid = re.search(r'href="https://www\.youtube\.com/channel/(UC[\w-]{22})"', block)
        if not name or not cid:
            raise ValueError('FC2 channel markup changed')
        rows.append({'channel_id': cid[1], 'name': text(name[1])})
    if not count or int(count[1]) != len(rows) or not rows or len({r['channel_id'] for r in rows}) != len(rows):
        raise ValueError('Incomplete FC2 channel roster')
    return rows


def collect_fc2(fetch):
    channels = parse_fc2(fetch(FC2))
    def get(r):
        url = 'https://www.youtube.com/channel/' + r['channel_id']
        try:
            profile = youtube_profile(fetch(url), 'channel/' + r['channel_id'])
            if not profile['published'] or preparing(profile['name']):
                return None
            row = {'source_id': 'fc2:' + r['channel_id'], 'display_name': profile['name'], 'aliases': [r['name']],
                   'youtube_channel_id': r['channel_id'], 'source_url': url, 'category': 'AIVTuber', 'category_source': FC2,
                   'activity_source': url, 'activity_evidence': 'official_channel_published_video_count',
                   'platform_accounts': profile['accounts'], '_requires_character_match': not AI_NAME.search(profile['name'])}
            return row
        except (OSError, ValueError, KeyError, TypeError):
            return None
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = [r for r in pool.map(get, channels) if r]
    return rows, {'source_records': len(channels), 'eligible_records': len(rows), 'unconfirmed_channels': len(channels) - len(rows)}


def reviewed_rows():
    path = Path(__file__).with_name('reviewed-ai-introductions.json')
    rows = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    for r in rows:
        if not re.fullmatch(r'https://x\.com/kedamasuzume/status/\d+', r['source_url']):
            raise ValueError('Invalid reviewed introduction source')
        if r.get('activity_evidence') != 'reviewed_introduction_published_content':
            raise ValueError('Introduction lacks reviewed publication evidence')
        r.update(category='AIVTuber', category_source=r['source_url'], activity_source=r['source_url'])
    return rows


def refresh_ai_directories(base, previous, fetch, report):
    updated = previous
    for name, collect in [('aituberlist', lambda: parse_list(collect_list(fetch))), ('aituber_fc2', lambda: collect_fc2(fetch)),
                          ('kedamasuzume_reviewed', lambda: (reviewed_rows(), {'source': 'https://x.com/kedamasuzume', 'collection': 'reviewed_public_introductions'}))]:
        try:
            rows, info = collect()
            updated, counts = merge_ai(base, updated, rows)
            report[name] = dict(info, **counts, checked_at=datetime.date.today().isoformat(), status='ok')
            print(name, counts, flush=True)
        except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
            report[name] = {**report.get(name, {}), 'status': 'unavailable', 'error': type(error).__name__, 'attempted_at': datetime.date.today().isoformat()}
            print(name, 'unavailable; previous records retained:', type(error).__name__, flush=True)
    return updated
