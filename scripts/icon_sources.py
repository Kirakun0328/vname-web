"""Source channel avatars by exact linked account, never by a name/image search."""
import datetime
import html
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
from platform_sources import record_accounts


def parse_channel_icon(document, url, expected_channel=None):
    channel = re.search(r'<link\b[^>]*rel="canonical"[^>]*href="https://www.youtube.com/channel/(UC[\w-]{22})"',document)
    if not channel: raise ValueError('Channel identity missing')
    if expected_channel and channel[1] != expected_channel: raise ValueError('Channel identity mismatch')
    image = re.search(r'<meta\b[^>]*property="og:image"[^>]*content="([^"]+)"',document)
    if not image: return None
    icon = html.unescape(image[1]); parsed = urlsplit(icon)
    if parsed.scheme != 'https' or parsed.hostname not in ('yt3.ggpht.com','yt3.googleusercontent.com'): return None
    return {'icon_url':icon,'icon_source':url,'icon_kind':'channel','icon_checked_at':datetime.datetime.now(datetime.timezone.utc).date().isoformat()}


def refresh(fetch, base, previous, report, limit=30):
    merged = {r['source_id']:dict(r) for r in base}
    extra = {r['source_id']:dict(r) for r in previous}
    for r in previous: merged.setdefault(r['source_id'],{}).update(r)
    # Rotate all channel-linked identities, retaining a working image on failure.
    candidates = []
    for sid,r in sorted(merged.items()):
        accounts = [a for a in record_accounts(r) if a['platform']=='youtube']
        if not accounts: continue
        channels = [a for a in accounts if a['id'].startswith('channel/')]
        if len(channels)>1: continue
        chosen = channels[0] if channels else accounts[0]
        candidates.append((sid,chosen['url'],chosen['id'][8:] if channels else None))
    if not candidates: return previous
    state = report.get('channel_icons',{}); start = state.get('next_index',0)%len(candidates)
    ordered=candidates[start:]+candidates[:start]
    missing=any(not merged[sid].get('icon_url') for sid,url,cid in ordered)
    targets=[item for item in ordered if not missing or not merged[item[0]].get('icon_url')][:limit]
    next_index=(candidates.index(targets[-1])+1)%len(candidates) if targets else 0
    def get(item):
        sid,url,cid = item
        try: return sid,parse_channel_icon(fetch(url),url,cid),None
        except (OSError,ValueError,UnicodeError) as error: return sid,None,type(error).__name__
    with ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(get,targets))
    for sid,patch,error in results:
        if patch: extra.setdefault(sid,{'source_id':sid}).update(patch)
    report['channel_icons'] = {'checked_profiles':len(results),'updated_icons':sum(bool(p) for s,p,e in results),
                                'failed_profiles':sum(bool(e) for s,p,e in results),'next_index':next_index}
    return list(extra.values())
