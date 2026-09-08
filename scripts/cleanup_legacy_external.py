"""Remove legacy third-party-directory records with unclear reuse terms.

Protected data:
- AIVTuber-focused records, including records carrying AIV source provenance.
- community/manual reviewed records.
- independently rechecked primary records.
- person-scoped official agency/platform records.
- external datasets with explicit reuse licenses recorded below.
- user-edited encyclopedia references (Pixiv Encyclopedia / Niconico Pedia).

The initial data.js corpus is historical directory-derived data. General
VTuber/V-liver rows from that corpus are removed unless protected above.
Additional rows are removed when their provenance is a known third-party
directory/snapshot whose reuse terms are not explicitly allowlisted.
The script is idempotent and refuses to drop protected IDs that existed before cleanup.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def read_js(path: Path, variable: str):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\." + re.escape(variable) + r"\s*=\s*(\[.*\])\s*;?\s*$", text, re.S)
    if not match:
        raise ValueError(f"Invalid JS data: {path}")
    return json.loads(match.group(1))


def write_js(path: Path, variable: str, rows, comment: str):
    text = comment + "\nwindow." + variable + " = " + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def host(url):
    try:
        return (urlsplit(url or "").hostname or "").lower().removeprefix("www.")
    except ValueError:
        return ""


REUSABLE = {
    "vdb": {
        "markers": ("vdb.vtbs.moe", "github.com/dd-center/vdb", "github.com/bilibili-dd-center/vdb"),
        "license": "CC BY-NC-SA 4.0 / VDBL v1.0",
        "condition": "noncommercial; attribution; share-alike",
    },
    "taiwan_archive": {
        "markers": ("taiwanvtuberdata/", "taiwanvtubertrackingdataarchive"),
        "license": "Unlicense",
        "condition": "reuse permitted",
    },
    "indonesia_kaggle": {
        "markers": ("ekasetyoagung/indonesian-vtuber-channel-data",),
        "license": "Apache-2.0",
        "condition": "reuse permitted subject to license/notice terms",
    },
    "legacy_2019_dataset": {
        "markers": ("imamachi-n/virtual-youtuber-api",),
        "license": "MIT",
        "condition": "retain copyright/license notice for substantial copies",
    },
}

# These are preserved as source-linked references, not classified as reusable
# database licenses by this cleanup rule.
REFERENCE_PRESERVED = {
    "user_encyclopedia": {
        "markers": ("dic.pixiv.net", "dic.nicovideo.jp"),
        "reason": "user-edited encyclopedia reference; preserve source-linked identity records",
    },
}

RISKY_HOSTS = {
    "vtuber-post.com",
    "virtual-youtuber.userlocal.jp",
    "vstats.jp",
    "liverfun.jp",
    "hololist.net",
    "scholarvtuber.com",
}

RISKY_MARKERS = ("regional_directory_", "directory-past", "directory-published")
RISKY_PREFIXES = ("liverfun:",)

AIV_MARKERS = (
    "aiv.nyagsicapp.com",
    "aituberlist.net",
    "aituber.web.fc2.com",
    "kedamasuzume",
    "aivtuber",
    "aituber",
    "aivnav",
)


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


def provenance_text(row):
    values = [str(row.get("source_id", "")), str(row.get("activity_evidence", ""))]
    for key, value in row.items():
        if key.endswith("_source") or key.endswith("_sources") or key in ("source_url", "source_profiles"):
            values.extend(strings(value))
    return "\n".join(values).lower()


def reusable_family(row):
    joined = provenance_text(row)
    return next((name for name, meta in REUSABLE.items() if any(m in joined for m in meta["markers"])), None)


def reference_family(row):
    joined = provenance_text(row)
    return next((name for name, meta in REFERENCE_PRESERVED.items() if any(m in joined for m in meta["markers"])), None)


def aiv_related(row):
    if row.get("category") == "AIVTuber":
        return True
    return any(marker in provenance_text(row) for marker in AIV_MARKERS)


def load_reviewed_ids():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from reviewed_sources import reviewed_profiles
    return {r["source_id"] for r in reviewed_profiles()}


def person_scoped_official(row):
    sid = row.get("source_id", "")
    evidence = " ".join(str(row.get(k, "")) for k in ("activity_evidence", "primary_platform_evidence"))
    if sid.startswith("agency-") and ("official" in evidence or "individual" in evidence or row.get("primary_platforms")):
        return True
    if sid.startswith(("iriam:", "reality:", "17live:", "twitch:", "x:", "showroom:", "niconico:", "mirrativ:")):
        sources = [row.get("source_url"), row.get("activity_source"), row.get("primary_platform_source")]
        official_hosts = {
            "web.iriam.app", "reality.app", "17.live", "twitch.tv", "x.com", "twitter.com",
            "showroom-live.com", "nicovideo.jp", "cas.nicovideo.jp", "mirrativ.com"
        }
        if any(host(u) in official_hosts for u in sources) and not any(host(u) in RISKY_HOSTS for u in sources):
            return True
    return False


def risky_added_record(row):
    if reusable_family(row) or reference_family(row):
        return False
    if row.get("source_id", "").startswith(RISKY_PREFIXES):
        return True
    evidence = str(row.get("activity_evidence", "")).lower()
    if any(marker in evidence for marker in RISKY_MARKERS):
        return True
    urls = []
    for key in ("source_url", "activity_source", "snapshot_source", "romanized_source", "reading_source"):
        value = row.get(key)
        if isinstance(value, str):
            urls.append(value)
    urls.extend(u for u in row.get("source_profiles", []) if isinstance(u, str))
    return any(host(url) in RISKY_HOSTS for url in urls)


def main():
    base_path = ROOT / "data.js"
    extra_path = ROOT / "extra-data.js"
    platform_path = ROOT / "platform-data.js"
    primary_path = ROOT / "primary-data.js"

    base = read_js(base_path, "VTUBER_DATA")
    extra = read_js(extra_path, "VTUBER_EXTRA")
    platforms = read_js(platform_path, "VTUBER_PLATFORMS") if platform_path.exists() else []
    primary = read_js(primary_path, "VTUBER_PRIMARY") if primary_path.exists() else []

    merged = {r["source_id"]: dict(r) for r in base}
    for rows in (extra, platforms):
        for r in rows:
            merged.setdefault(r["source_id"], {}).update(r)

    preexisting_ids = set(merged)
    reviewed_ids = load_reviewed_ids()
    primary_ids = {r["source_id"] for r in primary}
    aiv_ids = {sid for sid, r in merged.items() if aiv_related(r)}
    reusable_ids = {sid for sid, r in merged.items() if reusable_family(r)}
    reference_ids = {sid for sid, r in merged.items() if reference_family(r)}
    official_ids = {sid for sid, r in merged.items() if person_scoped_official(r)}
    protected = reviewed_ids | primary_ids | aiv_ids | reusable_ids | reference_ids | official_ids
    protected_preexisting = protected & preexisting_ids

    removed_base = {r["source_id"] for r in base if r["source_id"] not in protected}
    clean_base = [r for r in base if r["source_id"] not in removed_base]

    removed_extra = set()
    for r in extra:
        sid = r["source_id"]
        if sid in protected:
            continue
        if sid in removed_base or risky_added_record(merged.get(sid, r)):
            removed_extra.add(sid)
    clean_extra = [r for r in extra if r["source_id"] not in removed_extra]

    removed_platform = set()
    for r in platforms:
        sid = r["source_id"]
        if sid in protected:
            continue
        if sid in removed_base or sid in removed_extra or risky_added_record(merged.get(sid, r)):
            removed_platform.add(sid)
    clean_platforms = [r for r in platforms if r["source_id"] not in removed_platform]

    surviving = {r["source_id"] for r in clean_base + clean_extra + clean_platforms}
    missing_protected = sorted(protected_preexisting - surviving)
    if missing_protected:
        raise RuntimeError(f"Protected identities would be lost: {missing_protected[:20]}")

    surviving_merged = {}
    for rows in (clean_base, clean_extra, clean_platforms):
        for r in rows:
            surviving_merged.setdefault(r["source_id"], {}).update(r)
    aiv_after_ids = {sid for sid, r in surviving_merged.items() if aiv_related(r)}
    reusable_after_ids = {sid for sid, r in surviving_merged.items() if reusable_family(r)}
    reference_after_ids = {sid for sid, r in surviving_merged.items() if reference_family(r)}
    if not aiv_ids <= aiv_after_ids:
        raise RuntimeError(f"AIV-related identities would be lost: {sorted(aiv_ids - aiv_after_ids)[:20]}")
    if not reusable_ids <= reusable_after_ids:
        raise RuntimeError(f"Explicitly reusable dataset identities would be lost: {sorted(reusable_ids - reusable_after_ids)[:20]}")
    if not reference_ids <= reference_after_ids:
        raise RuntimeError(f"Encyclopedia-referenced identities would be lost: {sorted(reference_ids - reference_after_ids)[:20]}")

    reusable_counts = {}
    for sid in reusable_ids:
        family = reusable_family(merged[sid])
        reusable_counts[family] = reusable_counts.get(family, 0) + 1

    reference_counts = {}
    for sid in reference_ids:
        family = reference_family(merged[sid])
        reference_counts[family] = reference_counts.get(family, 0) + 1

    report = {
        "schema": 3,
        "policy": "remove_only_legacy_external_data_without_clear_reuse_terms",
        "protected": {
            "reviewed": len(reviewed_ids),
            "reviewed_already_materialized": len(reviewed_ids & preexisting_ids),
            "primary_rechecked": len(primary_ids),
            "aiv_related": len(aiv_ids),
            "explicitly_reusable_dataset": len(reusable_ids),
            "reusable_by_family": reusable_counts,
            "user_encyclopedia_reference": len(reference_ids),
            "reference_by_family": reference_counts,
            "person_scoped_official": len(official_ids),
            "unique_preexisting": len(protected_preexisting),
        },
        "reusable_licenses": REUSABLE,
        "reference_preservation": REFERENCE_PRESERVED,
        "before": {"base": len(base), "extra": len(extra), "platform": len(platforms), "merged": len(merged)},
        "removed": {
            "base": len(removed_base), "extra": len(removed_extra), "platform": len(removed_platform),
            "unique_identities": len(removed_base | removed_extra | removed_platform),
        },
        "after": {
            "base": len(clean_base), "extra": len(clean_extra), "platform": len(clean_platforms),
            "merged": len(surviving_merged), "aiv_related": len(aiv_after_ids),
            "explicitly_reusable_dataset": len(reusable_after_ids),
            "user_encyclopedia_reference": len(reference_after_ids),
        },
    }

    write_js(base_path, "VTUBER_DATA", clean_base, "// Retained licensed/reviewed/official/encyclopedia-referenced identity seed records; unclear legacy directory-only rows removed.")
    write_js(extra_path, "VTUBER_EXTRA", clean_extra, "// Additive source-linked records; unclear legacy directory-only rows removed.")
    if platform_path.exists():
        write_js(platform_path, "VTUBER_PLATFORMS", clean_platforms, "// Public platform metadata; unclear legacy directory-only rows removed.")
    (ROOT / "scripts" / "legacy-cleanup-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
