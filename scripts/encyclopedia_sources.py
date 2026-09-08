"""Extract candidate facts from a supplied Pixiv encyclopedia Markdown copy.

This is deliberately not an approval step. Groups, shared channels, activity,
and identity must be checked before adding reviewed-encyclopedia-profiles.json.
No article prose or artwork links are included in the result.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ENTRY = re.compile(r'^- \[([^\n]+?)\]\((https://dic\.pixiv\.net/a/[^\n]+?)\)', re.M)
LINK = re.compile(r'^- \[([^\n]+?)\]\((https?://[^\s)]+)\)', re.M)


def pixiv_candidates(markdown):
    start = markdown.find('### 先駆者たち')
    end = markdown.find('## 関連イラスト', start)
    if start < 0 or end < 0:
        raise ValueError('Expected creator section boundaries are missing')
    text = markdown[start:end]
    entries = list(ENTRY.finditer(text))
    rows = []
    for i, entry in enumerate(entries):
        block = text[entry.end():entries[i + 1].start() if i + 1 < len(entries) else len(text)]
        links = []
        for label, url in LINK.findall(block):
            url = re.sub(r'\\([_*&])', r'\1', url)
            host = (urlsplit(url).hostname or '').lower()
            if host.endswith(('pixiv.net', 'pximg.net')):
                continue
            links.append({'label': re.sub(r'\\([_*])', r'\1', label).removesuffix('image'), 'url': url})
        rows.append({'name': entry[1], 'article_url': entry[2], 'links': links})
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('markdown', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(pixiv_candidates(args.markdown.read_text(encoding='utf-8')), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
