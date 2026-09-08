"""Import active AI VTuber identities from the CC0 AIVTuber.tv dataset.

AI characters sometimes share a Twitch/YouTube account with their developer.
Therefore these rows deliberately use character-specific source IDs and are
never merged solely because a broadcast account is shared.
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_URL = "https://aivtuber.tv/dataset/ai-vtubers-2026.json"
SOURCE_URL = "https://aivtuber.tv/"
LICENSE_URL = "https://aivtuber.tv/#dataset"
REPORT = ROOT / "scripts" / "aivtuber-cc0-report.json"


def read_js(path: Path, variable: str):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\." + re.escape(variable) + r"\s*=\s*(\[.*\])\s*;?\s*$", text, re.S)
    if not match:
        raise ValueError(f"Invalid JS data: {path}")
    return json.loads(match.group(1))


def write_js(path: Path, variable: str, rows):
    text = (
        "// Additive, source-linked VTuber/AIVTuber names and verified readings.\n"
        + "window."
        + variable
        + " = "
        + json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
    )
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def fetch_dataset():
    request = urllib.request.Request(
        DATA_URL,
        headers={"User-Agent": "vname-web-aivtuber-cc0-import/1.0 (+https://github.com/Kirakun0328/vname-web)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        rows = json.loads(response.read().decode("utf-8"))
    if not isinstance(rows, list) or not (5 <= len(rows) <= 500):
        raise ValueError("Unexpected AIVTuber.tv dataset shape")
    return rows


def slug(name):
    value = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not value:
        raise ValueError("Cannot create stable AI character ID")
    return value[:80]


def account(platform, url):
    if not isinstance(url, str) or not url.startswith("https://"):
        return None
    clean = url.rstrip("/")
    if platform == "twitch":
        login = clean.rsplit("/", 1)[-1].lower()
        return {"platform": "twitch", "id": login, "url": f"https://www.twitch.tv/{login}"} if login else None
    if platform == "youtube":
        ident = clean.rsplit("/", 1)[-1]
        return {"platform": "youtube", "id": ident.lower() if ident.startswith("@") else ident, "url": clean}
    if platform == "x":
        handle = clean.rsplit("/", 1)[-1]
        return {"platform": "x", "id": handle, "url": f"https://x.com/{handle}"} if handle else None
    if platform == "tiktok":
        handle = clean.rsplit("/", 1)[-1]
        return {"platform": "tiktok", "id": handle, "url": f"https://www.tiktok.com/{handle}"} if handle else None
    return None


def main():
    path = ROOT / "extra-data.js"
    rows = read_js(path, "VTUBER_EXTRA")
    by_id = {row["source_id"]: dict(row) for row in rows}
    before = len(by_id)
    dataset = fetch_dataset()
    accepted = 0
    skipped = 0

    for item in dataset:
        if not isinstance(item, dict) or item.get("status") != "active" or item.get("type") != "AI":
            skipped += 1
            continue
        name = str(item.get("name") or "").strip()
        if not (1 < len(name) <= 120):
            skipped += 1
            continue
        sid = "aivtuber-tv:" + slug(name)
        current = dict(by_id.get(sid, {}))
        accounts = list(current.get("platform_accounts", []))
        candidates = [
            account("twitch", item.get("twitch")),
            account("youtube", item.get("youtube")),
            account("x", item.get("twitter")),
            account("tiktok", item.get("tiktok")),
        ]
        for candidate in candidates:
            if candidate and candidate not in accounts:
                accounts.append(candidate)
        if not accounts:
            skipped += 1
            continue
        current.update({
            "source_id": sid,
            "display_name": name,
            "category": "AIVTuber",
            "character_specific": True,
            "platform_accounts": accounts,
            "source_url": DATA_URL,
            "activity_source": DATA_URL,
            "activity_evidence": "cc0_active_aivtuber_dataset",
            "licensed_dataset_sources": list(dict.fromkeys([
                *current.get("licensed_dataset_sources", []), SOURCE_URL
            ])),
            "licensed_dataset_licenses": {
                **current.get("licensed_dataset_licenses", {}),
                SOURCE_URL: {"license": "CC0 1.0", "license_url": LICENSE_URL},
            },
        })
        if item.get("developer"):
            current["developer_name"] = str(item["developer"])[:120]
        by_id[sid] = current
        accepted += 1

    write_js(path, "VTUBER_EXTRA", list(by_id.values()))
    report = {
        "schema": 1,
        "source": SOURCE_URL,
        "dataset": DATA_URL,
        "license": "CC0 1.0",
        "dataset_rows": len(dataset),
        "accepted_active_ai_characters": accepted,
        "skipped": skipped,
        "extra_rows_before": before,
        "extra_rows_after": len(by_id),
        "net_new_extra_rows": len(by_id) - before,
        "identity_policy": "character_specific; shared developer/broadcast accounts never imply identity merge",
        "excluded_fields": ["description", "appearance", "tags", "images"],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
