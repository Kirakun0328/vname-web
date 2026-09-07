"""Academic VTuber profiles, verified against their own published YouTube video."""
import datetime
import html
import json
import re
import time
from urllib.parse import urlsplit, unquote
from global_sources import CID, valid_name, merge_global
from regional_sources import timestamp
from reading_sources import kana

SCHOLAR_HOME='https://scholarvtuber.com/'
PROFILE=re.compile(r'https://scholarvtuber\.com/vtuber/(?:[a-zA-Z0-9_-]|%[a-fA-F0-9]{2})+/')


def parse_directory(document):
    match=re.search(r'const\s+allVTubers\s*=\s*',document)
    if not match:
        raise ValueError('Academic directory structure changed')
    records=json.JSONDecoder().raw_decode(document[match.end():])[0]
    urls=[r.get('detailUrl','') for r in records]
    if not 50<=len(urls)<=5000 or len(urls)!=len(set(urls)) or not all(PROFILE.fullmatch(u) for u in urls):
        raise ValueError('Incomplete academic directory')
    return urls


def parse_profile(document,url):
    if not PROFILE.fullmatch(url):
        raise ValueError('Invalid academic profile URL')
    name=re.search(r'<h1 class="vtuber-name">([^<]+)</h1>',document)
    social=re.search(r'<div class="vtuber-social-links">(.*?)</div>',document,re.S)
    videos=re.search(r'<section class="vtuber-videos">(.*?)</section>',document,re.S)
    message=re.search(r'<section class="vtuber-message">(.*?)</section>',document,re.S)
    if not name or not social or not videos:
        return None
    name=html.unescape(name[1]).strip()
    if not valid_name(name) or (message and re.search(r'準備中|デビュー予定|初配信予定|pre[\s-]?debut',message[1],re.I)):
        return None
    links=[html.unescape(u) for u in re.findall(r'href="([^"]+)"',social[1])]
    ids=list(dict.fromkeys(re.findall(r'youtube\.com/embed/([\w-]{11})(?:[?"/]|$)',videos[1])))
    return {'display_name':name,'source_url':url,'links':links,'videos':ids} if ids else None


def youtube_identity(url):
    parsed=urlsplit(url)
    if parsed.hostname not in ('www.youtube.com','youtube.com'):
        return None
    path=unquote(parsed.path).rstrip('/')
    if re.fullmatch(r'/channel/UC[\w-]{22}',path):
        return ('id',path.split('/')[-1])
    if re.fullmatch(r'/@[^/]+',path):
        return ('handle',path[1:].casefold())
    return None


def verified_video(profile,document,video_id,now=None):
    now=now or datetime.datetime.now(datetime.timezone.utc)
    match=re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*',document)
    if not match:
        return None
    player=json.JSONDecoder().raw_decode(document[match.end():])[0]
    detail=player.get('videoDetails') or {}
    meta=(player.get('microformat') or {}).get('playerMicroformatRenderer') or {}
    cid=detail.get('channelId','')
    published=timestamp(meta.get('publishDate'))
    views=str(detail.get('viewCount',''))
    if (detail.get('videoId')!=video_id or not CID.fullmatch(cid)
            or detail.get('isPrivate') or detail.get('isUpcoming')
            or not published or published>now or not views.isdigit() or int(views)<=0):
        return None
    owner=youtube_identity(meta.get('ownerProfileUrl',''))
    identities={youtube_identity(u) for u in profile['links']}
    identities.discard(None)
    # A recommended collaboration on somebody else's channel is insufficient.
    if ('id',cid) not in identities and (not owner or owner not in identities):
        return None
    row={'source_id':'youtube:'+cid,'youtube_channel_id':cid,'display_name':profile['display_name'],
         'source_url':profile['source_url'],'activity_source':'https://www.youtube.com/watch?v='+video_id,
         'activity_evidence':'directory_linked_channel_published_video','activity_published_at':published.isoformat()}
    explicit=re.fullmatch(r'(.+?)\s*[（(]([ぁ-ゖァ-ヶー\s・･]+)[）)]',profile['display_name'])
    if explicit and kana(explicit[2]):
        row.update(display_name=explicit[1].strip(),aliases=[profile['display_name']],reading=kana(explicit[2]),
                   reading_source=profile['source_url'],reading_source_kind='directory_explicit')
    if owner and owner[0]=='handle':
        row['youtube_handle']=unquote(urlsplit(meta['ownerProfileUrl']).path)[1:]
    return row


def refresh_scholar(base,previous,vdb,fetch,state=None,limit=20):
    urls=parse_directory(fetch(SCHOLAR_HOME))
    state=state or {}
    cursor=int(state.get('next_index',0))%len(urls)
    rows=[];failures=0;checked=0
    for offset in range(min(limit,len(urls))):
        index=(cursor+offset)%len(urls)
        checked+=1
        try:
            time.sleep(0.8)
            profile=parse_profile(fetch(urls[index]),urls[index])
            if not profile:
                continue
            for vid in profile['videos'][:2]:
                time.sleep(0.8)
                row=verified_video(profile,fetch('https://www.youtube.com/watch?v='+vid),vid)
                if row:
                    rows.append(row)
                    break
        except (OSError,ValueError,KeyError,TypeError) as error:
            failures+=1
            if getattr(error,'code',None) in (401,403,429) or failures>=5:
                break
    updated,counts=merge_global(base,previous,rows,vdb)
    return updated,dict(counts,source=SCHOLAR_HOME,source_records=len(urls),profiles_checked=checked,
                        verified_profiles=len(rows),failed_requests=failures,next_index=(cursor+checked)%len(urls),
                        checked_at=datetime.date.today().isoformat())
