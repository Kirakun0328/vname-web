"""SearXNG candidate discovery only. Never grants publication approval.

Use an explicitly configured, authorized instance; do not rotate public proxies.
Search snippets are not stored as biographies or treated as verified readings.
"""
import argparse
import datetime
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
QUERIES=[
 'site:x.com "VTuber" "配信中"',
 'site:youtube.com "個人勢VTuber" "初配信"',
 'site:x.com "IRIAM" "配信ありがとう"',
 'site:x.com "REALITY" "配信ありがとう"',
 'site:x.com "AIVTuber" "配信"',
 'site:youtube.com "VTuber" "self introduction"',
 'site:x.com "Vライバー" "TikTok"',
 'site:youtube.com "Vtuber" "自我介紹"',
 'site:x.com "VTuber" "Twitch"',
 'site:x.com "Vライバー" "ミラティブ"',
 'site:x.com "Vライバー" "SHOWROOM"',
 'site:x.com "VTuber" "ニコ生"',
]


def candidate_url(value):
    if not isinstance(value,str):return None
    try:u=urllib.parse.urlsplit(value)
    except ValueError:return None
    host=(u.hostname or '').removeprefix('www.').removeprefix('m.')
    if u.scheme!='https' or u.username or u.password or host not in ('youtube.com','x.com','twitter.com'):return None
    path=urllib.parse.unquote(u.path).rstrip('/')
    if not path or path.split('/')[1] in ('search','hashtag','results','i','feed'):return None
    if host=='youtube.com':
        if path=='/watch':
            video=urllib.parse.parse_qs(u.query).get('v',[''])[0]
            if not __import__('re').fullmatch(r'[\w-]{11}',video):return None
            return 'https://www.youtube.com/watch?v='+video
        if not (path.startswith('/@') or path.startswith('/channel/UC') or path.startswith('/shorts/')):return None
        return 'https://www.youtube.com'+urllib.parse.quote(path,safe='/@_-')
    return 'https://x.com'+urllib.parse.quote(path,safe='/@_-')


def extract(results, query, stamp):
    output=[]
    for result in results:
        if not isinstance(result,dict):continue
        url=candidate_url(result.get('url'))
        if not url:continue
        output.append({'url':url,'candidate_title':str(result.get('title',''))[:240],
                       'query':query,'discovered_at':stamp,'discovery_method':'searxng',
                       'review_status':'pending_primary_confirmation','published':False})
    return output


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=4)
    args=parser.parse_args();endpoint=os.environ.get('SEARXNG_URL','').strip()
    report_path=ROOT/'scripts/search-discovery-report.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else {}
    if not endpoint:
        report.update(status='not_configured',message='Set SEARXNG_URL to an authorized JSON-enabled instance. No search ran.')
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report['message']);return
    u=urllib.parse.urlsplit(endpoint)
    if u.scheme not in ('http','https') or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise ValueError('Use an instance base URL without embedded credentials or query parameters')
    if u.scheme=='http' and u.hostname not in ('localhost','127.0.0.1','::1'):
        raise ValueError('Remote instances must use HTTPS')
    queue_path=ROOT/'scripts/searxng-candidates.json'
    previous=json.loads(queue_path.read_text()) if queue_path.exists() else []
    queue={r['url']:r for r in previous};cursor=report.get('next_query',0)%len(QUERIES)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();count=0;status='ok'
    for offset in range(max(0,min(args.limit,len(QUERIES)))):
        idx=(cursor+offset)%len(QUERIES);query=QUERIES[idx]
        url=endpoint.rstrip('/')+'/search?'+urllib.parse.urlencode({'q':query,'format':'json','pageno':1,'language':'all'})
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'VName-primary-discovery/1.0'})
            with urllib.request.urlopen(request,timeout=20) as response:
                raw=response.read(2*1024*1024+1)
            if len(raw)>2*1024*1024:raise ValueError('Response too large')
            data=json.loads(raw)
            if not isinstance(data.get('results'),list):raise ValueError('Invalid search response')
            for row in extract(data['results'][:100],query,stamp):
                if row['url'] not in queue:queue[row['url']]=row;count+=1
            report['next_query']=(idx+1)%len(QUERIES)
        except (OSError,ValueError,TypeError) as error:
            status='source_unavailable';report['error_type']=type(error).__name__
            # Stop on denial/rate limits. Do not switch hosts to evade them.
            break
    report.update(status=status,updated_at=stamp,new_candidates=count,total_candidates=len(queue),
                  auto_published=0,scope='Search leads only; individual identity/activity confirmation is still required.')
    for path, data in [(queue_path,list(queue.values())),(report_path,report)]:
        tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(path)
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
