"""Audit old general VTuber/V-liver provenance without changing published data.

This report is intentionally compact: it records counts and a few source IDs,
not a second copy of the dictionary.
"""
import collections
import json
import re
from pathlib import Path

from update_dictionary import ROOT, read_js
from reviewed_sources import reviewed_profiles

FILES = (
    ('data.js', 'VTUBER_DATA'),
    ('extra-data.js', 'VTUBER_EXTRA'),
    ('platform-data.js', 'VTUBER_PLATFORMS'),
)

# AIVTuber-focused sources are deliberately outside this cleanup scope.
AIV_MARKERS = (
    'aiv.nyagsicapp.com', 'aituberlist.net', 'aituber.web.fc2.com',
    'kedamasuzume', 'aivtuber', 'aituber', 'aivnav',
)

# Only old GENERAL VTuber/V-liver datasets/directories are classified here.
LEGACY = {
    'vtuber_post': ('vtuber-post.com',),
    'vdb': ('vdb.vtbs.moe', 'github.com/dd-center/vdb'),
    'userlocal': ('virtual-youtuber.userlocal.jp',),
    'vstats': ('vstats.jp',),
    'liverfun': ('liverfun.jp',),
    'hololist': ('hololist.net', 'xoltia/vtuber-database'),
    'taiwan_dataset': ('taiwanvtuberdata/',),
    'thai_ranking_dataset': ('thaivtuberranking', 'vtuber.chuysan.com'),
    'indonesia_kaggle': ('ekasetyoagung/indonesian-vtuber-channel-data',),
    'legacy_2019_dataset': ('imamachi-n/virtual-youtuber-api',),
    'scholar_directory': ('scholarvtuber.com',),
}

SOURCE_FIELDS = {
    'source_url', 'activity_source', 'reading_source', 'romanized_source',
    'snapshot_source', 'name_source', 'primary_platform_source',
    'vliver_source', 'listing_status_source', 'report_source',
}


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def provenance_strings(row):
    values = []
    for key, value in row.items():
        if key in SOURCE_FIELDS or key.endswith('_source') or key.endswith('_sources') or key in ('source_profiles',):
            values.extend(strings(value))
    values.append(str(row.get('source_id', '')))
    values.append(str(row.get('activity_evidence', '')))
    return [v.lower() for v in values if v]


def is_aiv(row):
    if row.get('category') == 'AIVTuber':
        return True
    joined = '\n'.join(provenance_strings(row))
    return any(marker in joined for marker in AIV_MARKERS)


def legacy_families(row):
    if is_aiv(row):
        return set()
    joined = '\n'.join(provenance_strings(row))
    return {name for name, markers in LEGACY.items() if any(marker in joined for marker in markers)}


def source_prefix(source_id):
    if ':' in source_id:
        return source_id.split(':', 1)[0]
    if re.fullmatch(r'[0-9a-f-]{32,36}', source_id, re.I):
        return 'uuid-like'
    return 'other'


def audit():
    rows_by_file = {}
    by_sid = collections.defaultdict(list)
    for file, variable in FILES:
        rows = read_js(ROOT / file, variable)
        rows_by_file[file] = rows
        for row in rows:
            by_sid[row['source_id']].append((file, row))

    reviewed_ids = {r['source_id'] for r in reviewed_profiles()}
    primary_path = ROOT / 'primary-data.js'
    primary_ids = {r['source_id'] for r in read_js(primary_path, 'VTUBER_PRIMARY')} if primary_path.exists() else set()

    family_ids = collections.defaultdict(set)
    file_family_ids = {file: collections.defaultdict(set) for file, _ in FILES}
    prefixes = collections.Counter()
    aiv_ids = set()
    no_source_ids = set()
    samples = collections.defaultdict(list)

    for sid, variants in by_sid.items():
        prefixes[source_prefix(sid)] += 1
        families = set()
        has_source = False
        aiv = False
        for file, row in variants:
            aiv = aiv or is_aiv(row)
            row_families = legacy_families(row)
            families |= row_families
            for family in row_families:
                file_family_ids[file][family].add(sid)
            if any(row.get(k) for k in SOURCE_FIELDS):
                has_source = True
        if aiv:
            aiv_ids.add(sid)
        if not has_source:
            no_source_ids.add(sid)
        for family in families:
            family_ids[family].add(sid)
            if len(samples[family]) < 3:
                samples[family].append(sid)

    legacy_ids = set().union(*family_ids.values()) if family_ids else set()
    independently_anchored = reviewed_ids | primary_ids | aiv_ids
    report = {
        'schema': 1,
        'scope': 'audit_only_general_legacy_sources; AIVTuber sources excluded',
        'unique_ids': len(by_sid),
        'files': {file: len(rows) for file, rows in rows_by_file.items()},
        'reviewed_ids': len(reviewed_ids),
        'primary_rechecked_ids': len(primary_ids),
        'aivtuber_preserved_ids': len(aiv_ids),
        'legacy_general_ids_any_evidence': len(legacy_ids),
        'legacy_general_ids_also_reviewed_primary_or_aiv': len(legacy_ids & independently_anchored),
        'legacy_general_ids_without_reviewed_primary_or_aiv': len(legacy_ids - independently_anchored),
        'ids_without_source_fields': len(no_source_ids),
        'legacy_families': {name: len(ids) for name, ids in sorted(family_ids.items())},
        'legacy_by_file': {file: {name: len(ids) for name, ids in sorted(groups.items())} for file, groups in file_family_ids.items()},
        'source_id_prefixes_top': prefixes.most_common(30),
        'samples': dict(samples),
    }
    return report


def main():
    report = audit()
    path = ROOT / 'scripts/legacy-data-audit.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
