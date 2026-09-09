"""Read only the explicitly submitted creator links; save minimal identity evidence."""
import concurrent.futures
import datetime
import html
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def fetch(item):
    result = dict(item)
    time.sleep(1)
    try:
        req=urllib.request.Request(item['url'],headers={'User-Agent':'Mozilla/5.0 (compatible; VName-submission-review/1.0)'})
        with urllib.request.urlopen(req, timeout=20) as response:
            result['resolved_url']=response.geturl()
            result['status']=response.status
            document=response.read(4*1024*1024).decode('utf-8','replace')
        for field,key in [('title','og:title'),('description','og:description')]:
            m=re.search(r'<meta\b[^>]*(?:property|name)=["\']'+key+r'["\'][^>]*content=["\']([^"\']*)',document,re.I)
            result[field]=html.unescape(m.group(1))[:700] if m else ''
        for pattern in [r'"externalId"\s*:\s*"(UC[\w-]{22})"',r'itemprop="channelId"\s+content="(UC[\w-]{22})"']:
            m=re.search(pattern,document)
            if m:
                result['youtube_channel_id']=m.group(1)
                break
        result['has_upload_ui']=bool(re.search(r'"(?:videoRenderer|gridVideoRenderer|reelItemRenderer)"\s*:',document))
    except Exception as error:
        result['error']=type(error).__name__
        result['error_code']=getattr(error,'code',None)
    return result

items=json.loads((ROOT/'scripts/submitted-links-2026-09-09.json').read_text())
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    rows=list(pool.map(fetch,items))
report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'profiles':rows}
(ROOT/'scripts/submitted-links-audit-2026-09-09.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for row in rows:
    print(json.dumps(row,ensure_ascii=False))
