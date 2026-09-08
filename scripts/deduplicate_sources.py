"""Consolidate matching character names on an identical YouTube channel.

Names alone, shared developer accounts, and explicitly character-specific
entries are never sufficient evidence for merging.
"""
import copy
import re


def deduplicate(base, previous):
    from ai_directory_sources import name_keys
    from platform_sources import record_accounts

    merged = {r['source_id']: copy.deepcopy(r) for r in base}
    extra = {r['source_id']: copy.deepcopy(r) for r in previous}
    for sid, row in extra.items():
        merged.setdefault(sid, {}).update(row)
    base_ids = {r['source_id'] for r in base}
    channels = {}
    removed = set()
    for sid, row in merged.items():
        if row.get('character_specific'):
            continue
        ids = {a['id'][8:] for a in record_accounts(row)
               if a['platform'] == 'youtube' and re.fullmatch(r'channel/UC[\w-]{22}', a['id'])}
        if len(ids) != 1:
            continue
        cid = next(iter(ids))
        candidates = [target for target in channels.get(cid, [])
                      if name_keys(row) & name_keys(merged[target])]
        # Keep ambiguous matches and immutable base entries separate.
        if len(candidates) != 1 or sid in base_ids:
            channels.setdefault(cid, []).append(sid)
            continue
        target = candidates[0]
        old = merged[target]
        combined = {**row, **old}
        for field, value in row.items():
            if not combined.get(field):
                combined[field] = copy.deepcopy(value)
        for field in ('aliases', 'source_profiles', 'platform_accounts', 'audience_metrics', 'aivnav_ids'):
            values = [*old.get(field, []), *row.get(field, [])]
            if field == 'aliases':
                values.append(row['display_name'])
                values = [v for v in values if v != old['display_name']]
            if field == 'source_profiles':
                values += [r['source_url'] for r in (old, row) if r.get('source_url')]
            combined[field] = []
            for value in values:
                if value not in combined[field]:
                    combined[field].append(value)
        combined['platform_sources'] = {**row.get('platform_sources', {}), **old.get('platform_sources', {})}
        combined['source_id'] = target
        merged[target] = combined
        extra[target] = combined
        removed.add(sid)
    return [r for sid, r in extra.items() if sid not in removed]
