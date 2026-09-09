"""Source-linked V-livers across platforms; a YouTube account is never required.

Only explicit broadcast destinations become primary_platforms. Account links
alone are retained as related accounts, not evidence of a primary platform.
"""
import datetime
import html
import re
from urllib.parse import urlsplit, urlunsplit, unquote, parse_qs, urlencode
from concurrent.futures import ThreadPoolExecutor
from broad_sources import preparing, text

LABELS = {'youtube':'YouTube', 'tiktok':'TikTok LIVE', 'iriam':'IRIAM', 'avvy':'Avvy',
          'reality':'REALITY', 'twitch':'Twitch', '17live':'17LIVE', 'showroom':'SHOWROOM',
          'twitcasting':'ツイキャス', 'niconico':'ニコニコ', 'mirrativ':'Mirrativ',
          'bilibili':'bilibili', 'spoon':'Spoon', 'kick':'Kick', 'soop':'SOOP', 'topia':'topia', 'palmu':'Palmu', 'mixch':'ミクチャ', 'bigo':'BIGO LIVE', 'acfun':'AcFun', 'whowatch':'ふわっち', 'pococha':'Pococha', 'colorsing':'ColorSing', 'pikapika':'ピカピカ', 'everylive':'everylive', 'standfm':'stand.fm', 'radiotalk':'Radiotalk', 'openrec':'mellow-fan（旧OPENREC.tv）', 'pokekara':'Pokekara', 'instagram':'Instagram Live', 'facebook':'Facebook Live', 'chzzk':'CHZZK', 'rplay':'RPLAY'}
AGENCIES = {'321': 'https://vliver.321.inc/liver/', 'clover': 'https://clover-live.com/liver-page/'}
AVVY_INTERVIEW = 'https://panora.tokyo/archives/137121'
ACTIVE = re.compile(r'配信(?:中(?!心|止|断)|(?:を)?(?:して(?:る|いる|います|おります|ます)|しております))|(?:雑談|歌|ゲーム)枠をしています|初配信を終|活動を始めた|活動中|デビュー済', re.I)


def canonical_account(url):
    """Return a platform-scoped identity for a public account, never a generic URL."""
    if not isinstance(url, str):
        return None
    try:
        u = urlsplit(html.unescape(url))
        if u.scheme=='iriam' and u.netloc=='p' and u.path in ('','/'):
            query=parse_qs(u.query);uid=query.get('uid',[''])[0]
            if query.get('applicationModel')==['profile'] and re.fullmatch(r'(?:[0-9a-f]{32}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})',uid,re.I):
                return {'platform':'iriam','id':uid.lower(),'url':'iriam://p?applicationModel=profile&uid='+uid.lower()}
            return None
        if u.scheme not in ('http', 'https') or u.username or u.password or u.port:
            return None
    except ValueError:
        return None
    host = (u.hostname or '').lower().removeprefix('www.')
    path = unquote(u.path).rstrip('/')
    if host in ('x.com','twitter.com') and re.fullmatch(r'/i/user/\d+',path):
        return {'platform':'x','id':'uid:'+path.rsplit('/',1)[-1],'url':'https://x.com'+path}
    if host == 'mirrativ.page.link':
        target = parse_qs(u.query).get('link', [''])[0]
        parsed = urlsplit(target)
        if parsed.hostname in ('www.mirrativ.com', 'mirrativ.com'):
            return canonical_account(target)
        return None
    if host == 'web.colorsing.com' and path == '/share/user':
        uid = parse_qs(u.query).get('user_id', [''])[0]
        if re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', uid):
            return {'platform':'colorsing','id':uid,'url':'https://web.colorsing.com/share/user?user_id='+uid}
        return None
    patterns = [
        ('youtube', ('youtube.com', 'm.youtube.com'), r'/(channel/UC[\w-]{22}|@[\w.\-]+)'),
        ('tiktok', ('tiktok.com',), r'/(@[\w.\-]+)(?:/live)?'),
        ('twitch', ('twitch.tv', 'm.twitch.tv'), r'/([\w]+)'),
        ('avvy', ('s.avvy.live',), r'/u/([0-9a-hjkmnp-tv-z]{26})'),
        ('iriam', ('web.iriam.app',), r'/s/user/([\w-]+)'),
        ('reality', ('reality.app',), r'/profile/([\w-]+)'),
        ('17live', ('17.live',), r'/s/u/([\w-]+)'),
        ('17live', ('17.live',), r'/(?:[a-z]{2}/)?profile/(?:[ur]/)?([\w-]+)'),
        ('showroom', ('showroom-live.com',), r'/(?:r/)?([\w-]+)'),
        ('twitcasting', ('twitcasting.tv',), r'/([\w:.-]+)'),
        ('niconico', ('nicovideo.jp', 'sp.nicovideo.jp', 'cas.nicovideo.jp'), r'/user/(\d+)'),
        ('niconico', ('com.nicovideo.jp',), r'/community/(co\d+)'),
        ('mirrativ', ('mirrativ.com',), r'/user/(\d+)'),
        ('acfun', ('acfun.cn',), r'/u/(\d+)'),
        ('bilibili', ('space.bilibili.com',), r'/(\d+)'),
        ('spoon', ('spooncast.net',), r'/(?:[a-z]{2}/)?profile/([\w-]+)'),
        ('spoon', ('spooncast.net',), r'/(?:[a-z]{2}/)?channel/(\d+)(?:/tab/home)?'),
        ('whowatch', ('whowatch.tv',), r'/profile/(w:[\w.-]+)'),
        ('pococha', ('pococha.com',), r'/app/users/([\w-]+)'),
        ('pikapika', ('pikapika.live',), r'/index/roomuser/uid/(\d+)'),
        ('standfm', ('stand.fm',), r'/channels/([a-f0-9]{24})'),
        ('radiotalk', ('radiotalk.jp',), r'/program/(\d+)'),
        ('openrec', ('openrec.tv', 'mellow-fan.com'), r'/(?:m/)?user/([\w-]+)'),
        ('pokekara', ('u.pokekara.com',), r'/user/(\d+)'),
        ('instagram', ('instagram.com',), r'/([\w.]+)'),
        ('facebook', ('facebook.com',), r'/([\w.]+)'),
        ('topia', ('topia.tv',), r'/p/([\w-]+)'),
        ('topia', ('user.topia.tv',), r'/([\w-]+)'),
        ('palmu', ('palmu.me', 'app.palmu.jp'), r'/users/([\w-]+)'),
        ('mixch', ('mixch.tv',), r'/u/(\d+)'),
        ('bigo', ('bigo.tv',), r'/([\w-]+)'),
        ('kick', ('kick.com',), r'/([\w-]+)'),
        ('soop', ('ch.sooplive.co.kr', 'bj.afreecatv.com'), r'/([\w-]+)'),
        ('chzzk', ('chzzk.naver.com', 'm.chzzk.naver.com'), r'/([a-f0-9]{32})'),
        ('rplay', ('rplay.live',), r'/(c/[\w.-]+|creatorhome/[a-f0-9]{24})'),
        ('x', ('x.com', 'twitter.com'), r'/@?([\w]+)'),
    ]
    for platform, hosts, pattern in patterns:
        if host not in hosts:
            continue
        m = re.fullmatch(pattern, path)
        if not m:
            continue
        if m[1].lower() in ('home','explore','directory','search','login','signup','i','intent'):
            return None
        ident = m[1]
        if platform in ('tiktok','twitch','twitcasting','kick','x','soop') or (platform=='youtube' and ident.startswith('@')):
            ident = ident.lower()
        clean = urlunsplit(('https',host,u.path.rstrip('/'),'',''))
        if platform == 'whowatch': clean = 'https://whowatch.tv/profile/'+ident
        if platform == 'x': clean = 'https://x.com/'+ident
        if platform == 'tiktok': clean = 'https://www.tiktok.com/'+ident
        if platform == 'niconico' and ident.isdigit(): clean = 'https://www.nicovideo.jp/user/'+ident
        return {'platform':platform, 'id':ident, 'url':clean}
    # The source sometimes uses IRIAM's official deep link instead of /s/user/.
    if host == 'web.iriam.app' and path == '/s/user':
        ident = parse_qs(u.query).get('id', [''])[0]
        if re.fullmatch(r'[\w-]+', ident):
            return {'platform':'iriam','id':ident,'url':'https://web.iriam.app/s/user?'+urlencode({'id':ident})}
    return None


def links(fragment):
    return [html.unescape(u) for u in re.findall(r'<a\b[^>]*\bhref=["\']([^"\']+)', fragment, re.I)]


def accounts_from(fragment):
    result = {}
    for url in links(fragment):
        a = canonical_account(url)
        if a: result[(a['platform'],a['id'])] = a
    return list(result.values())


def record_accounts(row):
    found = {}
    for a in row.get('platform_accounts', []):
        account = canonical_account(a.get('url'))
        if account: found[(account['platform'],account['id'])] = account
    for field in ('twitter_url','twitch_url','source_url','broadcast_url','youtube_url'):
        a = canonical_account(row.get(field))
        if a: found[(a['platform'],a['id'])] = a
    if re.fullmatch(r'[\w]+',row.get('twitch_login','')):
        a=canonical_account('https://www.twitch.tv/'+row['twitch_login']);found[('twitch',a['id'])]=a
    if re.fullmatch(r'@[\w.\-]+',row.get('youtube_handle','')):
        a=canonical_account('https://www.youtube.com/'+row['youtube_handle']);found[('youtube',a['id'])]=a
    cid = row.get('youtube_channel_id') or (row['source_id'][8:] if row['source_id'].startswith('youtube:') else '')
    if re.fullmatch(r'UC[\w-]{22}', cid):
        a = canonical_account('https://www.youtube.com/channel/'+cid); found[('youtube',a['id'])] = a
    return list(found.values())


def parse_agency_index(document, agency):
    base = AGENCIES[agency]
    # 321 explicitly describes this roster as active V-livers, not applicants.
    if agency == '321' and '活躍中の321所属Vライバー' not in document:
        raise ValueError('321 active roster marker missing')
    urls = list(dict.fromkeys(u for u in links(document) if u.startswith(base) and re.fullmatch(r'[^/?#]+/',u[len(base):])))
    if not 5 <= len(urls) <= 1500:
        raise ValueError('Agency roster incomplete or changed')
    return sorted(urls)


def parse_agency_profile(document, url, agency):
    main = re.search(r'<main\b[^>]*>(.*?)</main>', document, re.S)
    if not main: raise ValueError('Missing profile content')
    main = main[1]
    title = re.search(r'<h1\b[^>]*>(.*?)</h1>', main, re.S)
    if not title: raise ValueError('Missing name')
    name = text(title[1])
    if not name or len(name)>300: raise ValueError('Invalid profile name')
    body = text(main)
    if preparing(body) or re.search(r'準備中|初配信予定|デビュー予定|未デビュー', body):
        return None
    if agency == '321':
        section = re.search(r'<div class="delivery-account">(.*?)<div class="sns-account">', main, re.S)
        if not section: raise ValueError('Missing broadcast accounts')
        destinations = accounts_from(section[1])
        evidence = 'agency_active_vliver_roster'
        # The referring index establishes activity; restrict every imported URL
        # to that roster in refresh_agency, then extract person-only main content.
    else:
        if not ACTIVE.search(body): return None
        section = re.search(r'<div class="liver-footer-actions">(.*?)</div>', main, re.S)
        if not section: raise ValueError('Missing broadcast links')
        destinations = accounts_from(section[1])
        evidence = 'official_profile_explicit_broadcasting'
    primary = sorted({a['platform'] for a in destinations if a['platform'] in LABELS})
    if not primary: return None
    row = {'source_id':f'agency-{agency}:'+unquote(url.rstrip('/').rsplit('/',1)[-1]),
           'display_name':name, 'source_url':url, 'category':'VTuber',
           'activity_source':url, 'activity_evidence':evidence, 'vliver_source':url,
           'primary_platforms':primary, 'primary_platform_source':url,
           'primary_platform_evidence':'official_broadcast_destinations',
           'platform_accounts':accounts_from(main)}
    english = re.search(r'<div class="(?:en-name|liver-name-sub)">(.*?)</div>',main,re.S)
    if english:
        value = text(re.sub(r'<br\s*/?>',' ',english[1]))
        if value: row.update(romanized_name=' '.join(value.split()),romanized_source=url)
    return row


def parse_avvy_interviews(document):
    if '実力派ライバー15名' not in document or 'メディア特集決定戦' not in document:
        raise ValueError('Avvy interview marker missing')
    rows=[]
    for heading in re.findall(r'<h2\b[^>]*>(.*?)</h2>',document,re.S):
        m = re.match(r'(\d+)位：(.+)[（(]@',text(heading))
        if not m: continue
        a = accounts_from(heading)
        social = next((x for x in a if x['platform']=='x'),None)
        if not social: raise ValueError('Missing interview identity')
        name = m[2].strip()
        rows.append({'source_id':'avvy-interview:'+social['id'],'display_name':name,
                     'source_url':social['url'],'platform_accounts':a,'category':'VTuber',
                     'activity_source':AVVY_INTERVIEW,'activity_evidence':'platform_event_winner_interview','vliver_source':AVVY_INTERVIEW,
                     'activity_snapshot_at':'2026-04-27',
                     'platforms':['avvy'],'platform_sources':{'avvy':AVVY_INTERVIEW}})
    if len(rows)!=15 or len({r['source_id'] for r in rows})!=15:
        raise ValueError('Incomplete Avvy interviews')
    return rows


def merge_platforms(base, previous, rows):
    """Use unique linked accounts to enrich identities; never fuzzy-merge names.

Shared broadcasts/AI personas remain separate. Ambiguous new imports are
skipped for review, rather than collapsing different characters.
"""
    merged={r['source_id']:dict(r) for r in base}
    extra={r['source_id']:dict(r) for r in previous}
    for r in previous: merged.setdefault(r['source_id'],{}).update(r)
    index={}
    for sid,r in merged.items():
        for a in record_accounts(r): index.setdefault((a['platform'],a['id']),set()).add(sid)
    added=matched=ambiguous=0
    for row in rows:
        if not row:continue
        name=row.get('display_name','')
        if not name or preparing(name) or not row.get('activity_source','').startswith('https://'):
            raise ValueError('Unverified platform profile')
        a=record_accounts(row)
        matches=set().union(*(index.get((x['platform'],x['id']),set()) for x in a)) if a else set()
        sid=row['source_id']
        if sid not in merged:
            if len(matches)>1:
                ambiguous+=1;continue
            if matches: sid=next(iter(matches))
        old=merged.get(sid)
        if old:
            matched+=1
            patch=extra.setdefault(sid,{'source_id':sid})
            if name!=old['display_name']:
                patch['aliases']=list(dict.fromkeys([*old.get('aliases',[]),name]))
        else:
            added+=1
            patch=extra.setdefault(sid,{'source_id':sid,'display_name':name,'reading':'','romanized_name':'',
                                         'source_url':row['source_url'],'category':'VTuber'})
            old=dict(patch);merged[sid]=old
        all_accounts={(x['platform'],x['id']):x for x in record_accounts(old)}
        all_accounts.update({(x['platform'],x['id']):x for x in a})
        patch['platform_accounts']=list(all_accounts.values())
        known=set(old.get('platforms',[]))|set(row.get('platforms',[]))|{x['platform'] for x in all_accounts.values() if x['platform'] in LABELS}
        patch['platforms']=sorted(known)
        patch['platform_sources']={**old.get('platform_sources',{}),**row.get('platform_sources',{}),
                                   **{x['platform']:row['activity_source'] for x in a if x['platform'] in LABELS}}
        # Preserve prior identity, AI category and better readings.
        for f in ('primary_platforms','primary_platform_source','primary_platform_evidence','activity_snapshot_at','vliver_source'):
            if row.get(f): patch[f]=row[f]
        if row.get('reading_source') and row.get('reading_source_kind')=='official' and not old.get('reading_source'):
            patch.update(reading=row['reading'],reading_source=row['reading_source'],reading_source_kind='official')
        if row.get('romanized_source') and not old.get('romanized_source'):
            patch.update(romanized_name=row['romanized_name'],romanized_source=row['romanized_source'])
        if not old.get('activity_source'):
            patch.update(activity_source=row['activity_source'],activity_evidence=row['activity_evidence'])
        patch['platform_checked_at']=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        for x in a:
            index.setdefault((x['platform'],x['id']),set()).add(sid)
            if x['platform']=='x':patch['twitter_url']=x['url']
            if x['platform']=='youtube' and x['id'].startswith('channel/'):
                patch['youtube_channel_id']=x['id'][8:]
        old.update(patch)
    return list(extra.values()),{'new_records':added,'matched_existing':matched,'ambiguous_skipped':ambiguous}


def refresh_agency(fetch, agency, state=None, limit=40):
    urls=parse_agency_index(fetch(AGENCIES[agency]),agency)
    state=state or {}; start=state.get('next_index',0)%len(urls)
    targets=urls[start:start+limit]
    retries=[u for u in state.get('retry_urls',[]) if u in urls][:8]
    targets=list(dict.fromkeys(targets+retries))
    def get(url):
        try:return url,parse_agency_profile(fetch(url),url,agency),None
        except (OSError,ValueError,UnicodeError) as e:return url,None,type(e).__name__
    with ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(get,targets))
    failures=[u for u,r,e in results if e]
    succeeded={u for u,r,e in results if not e}
    return [r for u,r,e in results if r],{
        'source':AGENCIES[agency],'candidate_profiles':len(urls),'checked_profiles':len(results),
        'eligible_profiles':sum(bool(r) for u,r,e in results),'failed_profiles':len(failures),
        'next_index':(start+min(limit,len(urls)-start))%len(urls),
        'retry_urls':sorted((set(state.get('retry_urls',[]))|set(failures))-succeeded),
        'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}


def enrich_known_accounts(base, previous, vdb):
    """Enrich only already-listed identities from official directory accounts."""
    vtbs=vdb.get('vtbs',[])
    if len(vtbs)<5000:raise ValueError('Incomplete VDB; retaining platform metadata')
    merged={r['source_id']:dict(r) for r in base}
    extra={r['source_id']:dict(r) for r in previous}
    for r in previous:merged.setdefault(r['source_id'],{}).update(r)
    channels={}
    for sid,r in merged.items():
        for a in record_accounts(r):channels.setdefault((a['platform'],a['id']),set()).add(sid)
    templates={'youtube':'https://www.youtube.com/channel/{}','youtubeAt':'https://www.youtube.com/@{}',
               'twitter':'https://x.com/{}','bilibili':'https://space.bilibili.com/{}',
               'twitch':'https://www.twitch.tv/{}','tiktok':'https://www.tiktok.com/@{}',
               'niconico':'https://www.nicovideo.jp/user/{}','showroom':'https://www.showroom-live.com/r/{}',
               'acfun':'https://www.acfun.cn/u/{}'}
    count=0
    for v in vtbs:
        if v.get('type')!='vtuber':continue
        accounts=[]
        for a in v.get('accounts',[]):
            template=templates.get(a.get('platform'))
            if template and a.get('type')=='official' and isinstance(a.get('id'),str):
                account=canonical_account(template.format(a['id']))
                if account:accounts.append(account)
        matches=set().union(*(channels.get((a['platform'],a['id']),set()) for a in accounts)) if accounts else set()
        sid=v.get('uuid') if v.get('uuid') in merged else next(iter(matches)) if len(matches)==1 else None
        if not sid or not accounts:continue
        old=merged[sid]
        all_accounts={(a['platform'],a['id']):a for a in record_accounts(old)}
        all_accounts.update({(a['platform'],a['id']):a for a in accounts})
        patch=extra.setdefault(sid,{'source_id':sid})
        patch['platform_accounts']=list(all_accounts.values())
        patch['platforms']=sorted(set(old.get('platforms',[]))|{a['platform'] for a in all_accounts.values() if a['platform'] in LABELS})
        patch['platform_sources']={**{a['platform']:'https://vdb.vtbs.moe/' for a in accounts if a['platform'] in LABELS},**old.get('platform_sources',{})}
        old.update(patch);count+=1
    return list(extra.values()),count
