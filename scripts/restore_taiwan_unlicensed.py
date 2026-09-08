"""Restore Taiwan VTuber archive identities that are explicitly reusable.

The pre-cleanup dictionary contained records sourced from
TaiwanVTuberData/TaiwanVTuberTrackingDataArchive, whose repository is released
under the Unlicense. A cleanup marker regression briefly failed to recognize
some Taiwan-only records. This script restores only that licensed family from a
pinned pre-cleanup snapshot.

It is intentionally idempotent. Once the expected provenance count is present,
it performs no network request and no data rewrite.
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "45d1f07e6d90d2c9bff0d1f62f552eb5b8ef76ac"
SOURCE_FILE = "extra-data.js"
SOURCE_URL = f"https://raw.githubusercontent.com/Kirakun0328/vname-web/{SOURCE_COMMIT}/{SOURCE_FILE}"
EXPECTED_FAMILY_COUNT = 2664
TAIWAN_MARKERS = ("taiwanvtuberdata/", "taiwanvtubertrackingdataarchive")
LICENSE_URL = "https://github.com/TaiwanVtuberData/TaiwanVTuberTrackingDataArchive/blob/master/LICENSE"
RISKY_HOSTS = {
    "vtuber-post.com",
    "virtual-youtuber.userlocal.jp",
    "vstats.jp",
    "liverfun.jp",
    "hololist.net",
    "scholarvtuber.com",
}


def read_js(path: Path, variable: str):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\." + re.escape(variable) + r"\s*=\s*(\[.*\])\s*;?\s*$", text, re.S)
    if not match:
        raise ValueError(f"Invalid JS data: {path}")
    return json.loads(match.group(1))


def parse_js(text: str, variable: str):
    match = re.search(r"window\." + re.escape(variable) + r"\s*=\s*(\[.*\])\s*;?\s*$", text, re.S)
    if not match:
        raise ValueError(f"Invalid remote JS data for {variable}")
    return json.loads(match.group(1))


def write_js(path: Path, variable: str, rows):
    text = (
        "// Additive source-linked records; unclear legacy directory-only rows removed.\n"
        + "window."
        + variable
        + " = "
        + json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
    )
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


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
        if key.endswith("_source") or key.endswith("_sources") or key in (
            "source_url",
            "source_profiles",
            "encyclopedia_sources",
        ):
            values.extend(strings(value))
    return "\n".join(values).lower()


def is_taiwan_archive(row):
    joined = provenance_text(row)
    return any(marker in joined for marker in TAIWAN_MARKERS)


def host(url):
    try:
        return (urlsplit(url or "").hostname or "").lower().removeprefix("www.")
    except ValueError:
        return ""


def safe_source_url(url):
    if not isinstance(url, str) or not url.startswith("https://"):
        return False
    return host(url) not in RISKY_HOSTS


def sanitize(row):
    """Keep identity/platform facts while avoiding unrelated unclear DB provenance."""
    result = dict(row)

    # If a value's explicit provenance points only to an unclear legacy source,
    # do not restore that derived value merely because this identity is also in
    # the Unlicensed Taiwan archive.
    for field, source_field in (
        ("reading", "reading_source"),
        ("romanized_name", "romanized_source"),
    ):
        original_source = result.get(source_field)
        if isinstance(original_source, str) and host(original_source) in RISKY_HOSTS:
            result.pop(field, None)
            result.pop(source_field, None)

    for key in list(result):
        value = result[key]
        if (key == "source_url" or key.endswith("_source")) and isinstance(value, str):
            low = value.lower()
            if not any(marker in low for marker in TAIWAN_MARKERS) and not safe_source_url(value):
                result.pop(key, None)
        elif key.endswith("_sources") and isinstance(value, list):
            kept = [
                v
                for v in value
                if isinstance(v, str)
                and (
                    any(marker in v.lower() for marker in TAIWAN_MARKERS)
                    or safe_source_url(v)
                )
            ]
            if kept:
                result[key] = kept
            else:
                result.pop(key, None)

    profiles = result.get("source_profiles")
    if isinstance(profiles, list):
        kept = [
            v
            for v in profiles
            if isinstance(v, str)
            and (
                any(marker in v.lower() for marker in TAIWAN_MARKERS)
                or safe_source_url(v)
            )
        ]
        if kept:
            result["source_profiles"] = kept
        else:
            result.pop("source_profiles", None)

    # Make the retained reuse basis explicit without copying article text/media.
    result["licensed_dataset_source"] = "https://github.com/TaiwanVtuberData/TaiwanVTuberTrackingDataArchive"
    result["licensed_dataset_license"] = "Unlicense"
    result["licensed_dataset_license_url"] = LICENSE_URL
    result["activity_evidence"] = result.get("activity_evidence") or "licensed_taiwan_archive_snapshot"
    return result


def merged_rows():
    rows = []
    for path, variable in (
        (ROOT / "data.js", "VTUBER_DATA"),
        (ROOT / "extra-data.js", "VTUBER_EXTRA"),
        (ROOT / "platform-data.js", "VTUBER_PLATFORMS"),
    ):
        if path.exists():
            rows.extend(read_js(path, variable))
    merged = {}
    for row in rows:
        merged.setdefault(row["source_id"], {}).update(row)
    return merged


def current_family_ids():
    return {sid for sid, row in merged_rows().items() if is_taiwan_archive(row)}


def download_snapshot():
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "vname-web-license-restore/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def main():
    before_ids = current_family_ids()
    report_path = ROOT / "scripts" / "licensed-legacy-restore-report.json"

    if len(before_ids) >= EXPECTED_FAMILY_COUNT:
        report = {
            "schema": 1,
            "status": "already_complete",
            "family": "TaiwanVTuberTrackingDataArchive",
            "license": "Unlicense",
            "expected": EXPECTED_FAMILY_COUNT,
            "present": len(before_ids),
            "added": 0,
            "source_commit": SOURCE_COMMIT,
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return

    remote_rows = parse_js(download_snapshot(), "VTUBER_EXTRA")
    licensed_rows = {row["source_id"]: sanitize(row) for row in remote_rows if is_taiwan_archive(row)}
    if len(licensed_rows) < EXPECTED_FAMILY_COUNT:
        raise RuntimeError(
            f"Pinned snapshot has too few Taiwan archive records: {len(licensed_rows)} < {EXPECTED_FAMILY_COUNT}"
        )

    extra_path = ROOT / "extra-data.js"
    current_extra = read_js(extra_path, "VTUBER_EXTRA")
    by_id = {row["source_id"]: dict(row) for row in current_extra}
    added = 0
    for sid, licensed_row in licensed_rows.items():
        if sid not in before_ids:
            # Current reviewed/official fields win over the historical snapshot.
            # The explicit license marker is then re-applied so cleanup can
            # always recognize why this identity is retained.
            merged = dict(licensed_row)
            merged.update(by_id.get(sid, {}))
            merged["licensed_dataset_source"] = licensed_row["licensed_dataset_source"]
            merged["licensed_dataset_license"] = licensed_row["licensed_dataset_license"]
            merged["licensed_dataset_license_url"] = licensed_row["licensed_dataset_license_url"]
            by_id[sid] = merged
            added += 1

    write_js(extra_path, "VTUBER_EXTRA", list(by_id.values()))
    after_ids = current_family_ids()
    if len(after_ids) < EXPECTED_FAMILY_COUNT:
        raise RuntimeError(
            f"Taiwan archive restore incomplete: {len(before_ids)} -> {len(after_ids)}, expected {EXPECTED_FAMILY_COUNT}"
        )

    report = {
        "schema": 1,
        "status": "restored",
        "family": "TaiwanVTuberTrackingDataArchive",
        "license": "Unlicense",
        "license_url": LICENSE_URL,
        "expected": EXPECTED_FAMILY_COUNT,
        "before": len(before_ids),
        "after": len(after_ids),
        "added": added,
        "source_commit": SOURCE_COMMIT,
        "source_file": SOURCE_FILE,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
