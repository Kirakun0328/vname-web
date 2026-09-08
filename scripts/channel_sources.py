"""Read public YouTube channel identity and its own publication count."""
import json
import re
from platform_sources import canonical_account


def youtube_profile(document, expected):
    match = re.search(r'(?:var ytInitialData|window\["ytInitialData"\])\s*=\s*', document)
    if not match:
        raise ValueError('YouTube channel metadata unavailable')
    data = json.JSONDecoder().raw_decode(document[match.end():])[0]
    meta = data.get('metadata', {}).get('channelMetadataRenderer', {})
    cid = meta.get('externalId', '')
    if not re.fullmatch(r'UC[\w-]{22}', cid):
        raise ValueError('YouTube channel identity unavailable')
    accounts = [canonical_account(u) for u in [meta.get('channelUrl'), *meta.get('ownerUrls', [])]]
    accounts = [a for a in accounts if a]
    if not any(a['platform'] == 'youtube' and a['id'] == expected for a in accounts):
        raise ValueError('YouTube channel identity mismatch')
    # Only the channel header's own count establishes publication; recommended
    # videos elsewhere on the page are not evidence for this channel.
    header = json.dumps(data.get('header', {}), ensure_ascii=False)
    counts = re.findall(r'([\d,]+)\s*(?:本の動画|videos\b)', header, re.I)
    published = any(int(n.replace(',', '')) > 0 for n in counts)
    return {'channel_id': cid, 'name': meta.get('title', ''), 'accounts': accounts,
            'published': published}

