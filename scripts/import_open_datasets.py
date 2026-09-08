"""Import VTuber identities only from datasets with explicit reuse licenses.

Sources added here are deliberately conservative:
- Wikidata structured data (CC0): only items explicitly typed/occupied as VTuber
  and carrying a YouTube channel ID.
- VTuber 1B Elements channel index (ODC PDDL): curated channel index from the
  public dataset; no chat/user data is imported.
- ayousanz VTuber YouTube Channel List (MIT): only label=1 rows whose public
  channel description self-identifies the channel owner as a VTuber. Fan/clip/
  reaction/archive channels are rejected by policy filters.

Only minimum public identity facts are retained. Descriptions, thumbnails,
audience metrics and chat data are never copied into the public dictionary.
"""
from __future__ import annotations

import csv
import io
import json
import re
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "scripts" / "open-datasets-report.json"

WIKIDATA_PAGE = "https://www.wikidata.org/"
WIKIDATA_LICENSE = "https://www.wikidata.org/wiki/Wikidata:Licensing"
WDQS = "https://query.wikidata.org/sparql"
VTUBER_1B_PAGE = "https://www.kaggle.com/datasets/uetchy/vtuber-livechat-elements"
VTUBER_1B_DOWNLOAD = "https://www.kaggle.com/api/v1/datasets/download/uetchy/vtuber-livechat-elements"
HF_PAGE = "https://huggingface.co/datasets/ayousanz/vtuber-youtube-list-dataset"
HF_DATA = "https://huggingface.co/datasets/ayousanz/vtuber-youtube-list-dataset/resolve/main/vtuber_channels_dataset.jsonl"

CHANNEL_RE = re.compile(r"UC[-_0-9A-Za-z]{22}$")
REJECT_CHANNEL = re.compile(
    r"(?:切り抜き|切抜|クリップ|まとめ|翻訳|ファン(?:チャンネル|ch)?|非公式|応援ch|応援チャンネル|"
    r"clips?|clipping|highlights?|compilat(?:ion|ions)|reaction|reacts?|fan\s*(?:channel|ch)?|"
    r"archive|vod\s*channel|legendadas|eng\s*sub|subbed)", re.I,
)
SELF_ID = re.compile(
    r"(?:vtuber|v-tuber|virtual\s*youtuber|バーチャルyoutuber|ＶＴｕｂｅｒ).{0,50}"
    r"(?:です|と申します|といいます|だよ|活動(?:中|して)|配信(?:中|して)|i\s*am|i['’]?m|my\s+name\s+is)"
    r"|(?:です|と申します|といいます|だよ|i\s*am|i['’]?m|my\s+name\s+is).{0,50}"
    r"(?:vtuber|v-tuber|virtual\s*youtuber|バーチャルyoutuber|ＶＴｕｂｅｒ)", re.I,
)
JP_NAME = re.compile(
    r"(?:VTuber|Vtuber|ＶＴｕｂｅｒ)(?:の|、| |　)*([^\s、。！!]{2,24})(?:です|と申します|だよ|といいます)"
)
EN_NAME = re.compile(
    r"(?:i\s*am|i['’]?m|my\s+name\s+is)\s+([A-Za-z0-9_'’ .-]{2,40}?)(?:,|\s)+(?:an?\s+)?(?:[^.!\n]{0,24}\s+)?vtuber\b",
    re.I,
)


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


def request_bytes(url: str, *, accept: str | None = None, attempts: int = 3):
    headers = {"User-Agent": "vname-web-open-dataset-import/1.0 (+https://github.com/Kirakun0328/vname-web)"}
    if accept:
        headers["Accept"] = accept
    last = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as response:
                return response.read()
        except OSError as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise last or OSError("request failed")


def youtube_account(channel_id: str):
    url = f"https://www.youtube.com/channel/{channel_id}"
    return {"platform": "youtube", "id": f"channel/{channel_id}", "url": url}


def channel_id_of(row):
    cid = row.get("youtube_channel_id")
    if isinstance(cid, str) and CHANNEL_RE.fullmatch(cid):
        return cid
    sid = row.get("source_id", "")
    if sid.startswith("youtube:") and CHANNEL_RE.fullmatch(sid[8:]):
        return sid[8:]
    for account in row.get("platform_accounts", []):
        if not isinstance(account, dict) or account.get("platform") != "youtube":
            continue
        value = str(account.get("id", ""))
        if value.startswith("channel/") and CHANNEL_RE.fullmatch(value[8:]):
            return value[8:]
    return None


def current_indexes(base, extra, platforms):
    merged = {}
    for row in [*base, *extra, *platforms]:
        merged.setdefault(row["source_id"], {}).update(row)
    channels = {}
    for sid, row in merged.items():
        cid = channel_id_of(row)
        if cid:
            channels.setdefault(cid, sid)
    return merged, channels


def valid_name(name):
    if not isinstance(name, str):
        return False
    name = name.strip()
    return 1 < len(name) <= 120 and not any(c in name for c in "\r\n\t")


def clean_channel_title(title):
    title = re.sub(r"\s+", " ", str(title or "")).strip()
    title = re.sub(
        r"\s*[【〖\[][^】〗\]]*(?:VTuber|Vtuber|ＶＴｕｂｅｒ|所属)[^】〗\]]*[】〗\]]\s*$",
        "",
        title,
        flags=re.I,
    ).strip()
    return title


def add_candidate(extra_by_id, merged, channels, *, channel_id, display_name, source_url,
                  license_name, license_url, evidence, reading=None, reading_kind=None,
                  aliases=None):
    if not CHANNEL_RE.fullmatch(channel_id) or not valid_name(display_name):
        return "invalid"
    target = channels.get(channel_id, f"youtube:{channel_id}")
    old = merged.get(target, {})
    patch = dict(extra_by_id.get(target, {}))
    if not old.get("display_name"):
        patch["display_name"] = display_name.strip()
    elif old.get("display_name") != display_name.strip():
        current_aliases = list(dict.fromkeys([*old.get("aliases", []), *patch.get("aliases", []), display_name.strip()]))
        patch["aliases"] = [a for a in current_aliases if a and a != old.get("display_name")]
    if aliases:
        patch["aliases"] = list(dict.fromkeys([*old.get("aliases", []), *patch.get("aliases", []), *aliases]))
    patch.setdefault("source_id", target)
    patch.setdefault("category", old.get("category") or "VTuber")
    patch.setdefault("youtube_channel_id", channel_id)
    patch.setdefault("source_url", f"https://www.youtube.com/channel/{channel_id}")
    accounts = [*old.get("platform_accounts", []), *patch.get("platform_accounts", [])]
    account = youtube_account(channel_id)
    if account not in accounts:
        accounts.append(account)
    patch["platform_accounts"] = accounts
    sources = list(dict.fromkeys([
        *old.get("licensed_dataset_sources", []),
        *patch.get("licensed_dataset_sources", []),
        source_url,
    ]))
    patch["licensed_dataset_sources"] = sources
    licenses = dict(old.get("licensed_dataset_licenses", {}))
    licenses.update(patch.get("licensed_dataset_licenses", {}))
    licenses[source_url] = {"license": license_name, "license_url": license_url}
    patch["licensed_dataset_licenses"] = licenses
    if not old.get("activity_source"):
        patch["activity_source"] = source_url
        patch["activity_evidence"] = evidence
    if reading and not old.get("reading"):
        patch["reading"] = reading
        patch["reading_source"] = source_url
        patch["reading_source_kind"] = reading_kind or "directory_explicit"
    extra_by_id[target] = patch
    merged.setdefault(target, {}).update(patch)
    channels[channel_id] = target
    return "new" if target not in old else "enriched"


def wikidata_rows():
    query = """
SELECT ?item ?youtube ?jaLabel ?enLabel ?kana WHERE {
  { ?item wdt:P106 wd:Q55155641 . }
  UNION
  { ?item wdt:P31 wd:Q55155641 . }
  ?item wdt:P2397 ?youtube .
  OPTIONAL { ?item rdfs:label ?jaLabel . FILTER(LANG(?jaLabel) = 'ja') }
  OPTIONAL { ?item rdfs:label ?enLabel . FILTER(LANG(?enLabel) = 'en') }
  OPTIONAL { ?item wdt:P1814 ?kana . }
}
""".strip()
    url = WDQS + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    raw = request_bytes(url, accept="application/sparql-results+json")
    data = json.loads(raw.decode("utf-8"))
    return data.get("results", {}).get("bindings", [])


def import_wikidata(extra_by_id, merged, channels):
    counts = {"seen": 0, "new": 0, "enriched": 0, "invalid": 0}
    for row in wikidata_rows():
        counts["seen"] += 1
        cid = row.get("youtube", {}).get("value", "")
        ja = row.get("jaLabel", {}).get("value", "").strip()
        en = row.get("enLabel", {}).get("value", "").strip()
        name = ja or en
        aliases = [x for x in (en if ja and en != ja else "",) if x]
        kana = row.get("kana", {}).get("value", "").strip()
        status = add_candidate(
            extra_by_id, merged, channels,
            channel_id=cid,
            display_name=name,
            aliases=aliases,
            source_url=WIKIDATA_PAGE,
            license_name="CC0 1.0",
            license_url=WIKIDATA_LICENSE,
            evidence="wikidata_explicit_vtuber_with_youtube_id",
            reading=kana or None,
            reading_kind="directory_explicit" if kana else None,
        )
        counts[status] = counts.get(status, 0) + 1
    return counts


def import_vtuber_1b(extra_by_id, merged, channels):
    counts = {"seen": 0, "new": 0, "enriched": 0, "invalid": 0}
    raw = request_bytes(VTUBER_1B_DOWNLOAD)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        name = next((n for n in zf.namelist() if n.lower().endswith("channels.csv")), None)
        if not name:
            raise ValueError("VTuber 1B Elements archive does not contain channels.csv")
        text = zf.read(name).decode("utf-8-sig")
    for row in csv.DictReader(io.StringIO(text)):
        counts["seen"] += 1
        cid = str(row.get("channelId") or "").strip()
        display = str(row.get("name") or row.get("englishName") or "").strip()
        aliases = [str(row.get("englishName") or "").strip()]
        aliases = [a for a in aliases if a and a != display]
        status = add_candidate(
            extra_by_id, merged, channels,
            channel_id=cid,
            display_name=display,
            aliases=aliases,
            source_url=VTUBER_1B_PAGE,
            license_name="ODC PDDL 1.0",
            license_url="https://opendatacommons.org/licenses/pddl/1-0/",
            evidence="vtuber_1b_public_channel_index",
        )
        counts[status] = counts.get(status, 0) + 1
    return counts


def self_name(description, title):
    description = str(description or "")[:500]
    if not SELF_ID.search(description):
        return None
    match = JP_NAME.search(description)
    if match and valid_name(match.group(1)):
        return match.group(1).strip()
    match = EN_NAME.search(description)
    if match and valid_name(match.group(1)):
        return match.group(1).strip()
    cleaned = clean_channel_title(title)
    return cleaned if valid_name(cleaned) else None


def import_hf(extra_by_id, merged, channels):
    counts = {"seen": 0, "label_vtuber": 0, "rejected_policy": 0, "new": 0, "enriched": 0, "invalid": 0}
    raw = request_bytes(HF_DATA).decode("utf-8")
    for line in raw.splitlines():
        if not line.strip():
            continue
        counts["seen"] += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            counts["invalid"] += 1
            continue
        if row.get("label") != 1:
            continue
        counts["label_vtuber"] += 1
        title = str(row.get("title") or "")
        desc = str(row.get("description") or "")
        if REJECT_CHANNEL.search(title + "\n" + desc):
            counts["rejected_policy"] += 1
            continue
        name = self_name(desc, title)
        if not name:
            counts["rejected_policy"] += 1
            continue
        status = add_candidate(
            extra_by_id, merged, channels,
            channel_id=str(row.get("channel_id") or "").strip(),
            display_name=name,
            source_url=HF_PAGE,
            license_name="MIT",
            license_url=HF_PAGE,
            evidence="mit_dataset_plus_channel_self_identification",
        )
        counts[status] = counts.get(status, 0) + 1
    return counts


def main():
    base = read_js(ROOT / "data.js", "VTUBER_DATA")
    extra_path = ROOT / "extra-data.js"
    extra = read_js(extra_path, "VTUBER_EXTRA")
    platform_path = ROOT / "platform-data.js"
    platforms = read_js(platform_path, "VTUBER_PLATFORMS") if platform_path.exists() else []
    merged, channels = current_indexes(base, extra, platforms)
    extra_by_id = {row["source_id"]: dict(row) for row in extra}
    before = len(merged)

    sources = {}
    for name, fn in (
        ("wikidata_cc0", import_wikidata),
        ("vtuber_1b_pddl", import_vtuber_1b),
        ("ayousanz_mit", import_hf),
    ):
        try:
            sources[name] = {"status": "ok", **fn(extra_by_id, merged, channels)}
        except (OSError, ValueError, KeyError, UnicodeError, zipfile.BadZipFile) as exc:
            sources[name] = {"status": "unavailable", "error": type(exc).__name__, "message": str(exc)[:240]}

    rows = list(extra_by_id.values())
    write_js(extra_path, "VTUBER_EXTRA", rows)
    after = len(merged)
    report = {
        "schema": 1,
        "policy": "explicit_open_license_only_with_source_specific_quality_filters",
        "before_unique_identities": before,
        "after_unique_identities": after,
        "net_new_unique_identities": after - before,
        "sources": sources,
        "retained_fields": ["display_name", "reading_if_explicit", "youtube_channel_id", "public_source_and_license"],
        "excluded_fields": ["descriptions", "thumbnails", "audience_metrics", "chat_data"],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
