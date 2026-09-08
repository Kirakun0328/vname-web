"""Discover public V-liver profiles with person-scoped activity evidence."""
import datetime
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse, unquote
from directory_sources import Document
from platform_sources import canonical_account, merge_platforms
from reading_sources import kana

AGENCIES = {
    'novel': 'https://novel-live.net/vliver/',
    'samu': 'https://samulive.net/talents/',
    'tolico': 'https://tolico.info/vliver/',
    'mvirtual': 'https://m-virtual.jp/liver/',
}

def cls(node, value): return value in node.attrs.get('class', '').split()

def discover(document, agency):
    root = Document(document).root
    base = AGENCIES[agency]; parsed = urlparse(base)
    profiles, pages = set(), set()
    for a in root.all('a'):
        url = urljoin(base, a.attrs.get('href', '')); p = urlparse(url)
        if p.scheme != 'https' or p.netloc != parsed.netloc: continue
        if re.fullmatch(re.escape(parsed.path)+r'[^/?#]+/', p.path) and not p.query:
            profiles.add(url.split('#')[0])
        if p.path == parsed.path and re.fullmatch(r'page=\d{1,2}', p.query):
            pages.add(url.split('#')[0])
    return sorted(profiles), sorted(pages)

def parse_profile(document, url, agency):
    root = Document(document).root
    if agency == 'mvirtual':
        sections = [n for n in root.all('article') if any(cls(h,'name') for h in n.all('h3'))]
        if len(sections) != 1: return None
        node = sections[0]
        heading = next(h for h in node.all('h3') if cls(h,'name'))
        roman = next((h.content().strip() for h in heading.all('span') if cls(h,'furigana')), '')
        name = heading.content().removesuffix(roman).strip()
        body = node.content()
        # Regular broadcast tags, actual event rewards or past debut date.
        active = bool(re.search(r'毎日配信|定期配信|配信中|配信してい|配信しています|イベント特典|周年', body))
        destinations = [a for a in node.all('a') if a.attrs.get('id') == 'r-prof']
    else:
        sections = [n for n in root.all('div') if cls(n,'gt3_single_team_descr')]
        if len(sections) != 1: return None
        node = sections[0]
        headings = {n.content().strip() for n in root.all('h1') if n.content().strip()}
        if len(headings) != 1: return None
        name = next(iter(headings)); body = node.content()
        # Only the agency-written biography/awards; fan letters and related members are outside.
        active = bool(re.search(r'\d+位|入賞|配信中|配信してい|配信しています|毎日配信|周年',body))
        roman = next((n.content().strip() for n in root.all('div') if cls(n,'gt3_team_title_position')), '')
        destinations = [a for a in node.all('a') if re.search('IRIAM|REALITY|TikTok|17LIVE|Mirrativ',a.content(),re.I)]
    if not name or len(name)>80 or re.search(r'準備中|未デビュー|デビュー予定',body+name) or not active: return None
    accounts = {}
    for a in node.all('a'):
        account = canonical_account(a.attrs.get('href'))
        if account: accounts[(account['platform'],account['id'])] = account
    if not accounts: return None
    primary=set()
    for a in destinations:
        account=canonical_account(a.attrs.get('href'))
        if account and account['platform'] in ('iriam','reality','tiktok','17live','mirrativ'): primary.add(account['platform'])
        elif 'IRIAM' in a.content(): primary.add('iriam')
    if not primary:return None
    row={'source_id':'agency-'+agency+':'+unquote(url.rstrip('/').rsplit('/',1)[-1]),
         'display_name':name,'source_url':url,'activity_source':url,'activity_evidence':'official_profile_broadcast_or_award',
         'vliver_source':url,'platform_accounts':list(accounts.values()),'platforms':sorted(primary),
         'platform_sources':{p:url for p in primary},'primary_platforms':sorted(primary),
         'primary_platform_source':url,'primary_platform_evidence':'official_profile_broadcast_link'}
    explicit=re.search(re.escape(name)+r'\s*[（(]([ぁ-ゖァ-ヶー\s・]+)[）)]\s*(?:です|と申します|といいます)',body)
    if explicit and kana(explicit[1]):
        row.update(reading=kana(explicit[1]),reading_source=url,reading_source_kind='official')
    if roman:
        reading=kana(roman)
        if reading:row.update(reading=reading,reading_source=url,reading_source_kind='official')
        elif re.fullmatch(r'[A-Za-z\s・.\-]+',roman):row.update(romanized_name=roman,romanized_source=url)
    return row

def collect(fetch, agency, state=None, full=False):
    state=state or {}; urls,pages=discover(fetch(AGENCIES[agency]),agency);urls=set(urls);seen=set()
    while pages:
        page=pages.pop(0)
        if page in seen:continue
        if len(seen)>=30:raise ValueError('Roster pagination limit')
        seen.add(page); found,more=discover(fetch(page),agency);urls.update(found)
        pages.extend(p for p in more if p not in seen)
    if not urls:raise ValueError('No public profile links')
    ordered=sorted(urls); old=set(state.get('known_profile_urls',[]))
    fresh=[u for u in ordered if u not in old]
    start=state.get('next_index',0)%len(ordered)
    rotated=ordered[start:]+ordered[:start]
    targets=list(dict.fromkeys(fresh+state.get('retry_urls',[])+rotated))
    targets=[u for u in targets if u in urls][:len(urls) if full else 50]
    def get(url):
        try:return url,parse_profile(fetch(url),url,agency),None
        except (OSError,ValueError,UnicodeError) as e:return url,None,type(e).__name__
    with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(get,targets))
    rows=[r for u,r,e in results if r]
    return rows,{'source':AGENCIES[agency],'candidate_profiles':len(urls),'checked_profiles':len(results),
                 'verified_source_records':len(rows),'known_profile_urls':sorted(old|{u for u,r,e in results if not e}),
                 'retry_urls':[u for u,r,e in results if e],'next_index':(start+len(targets))%len(ordered),
                 'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}

def refresh(fetch,base,previous,report,full=False):
    updated=previous
    for agency in AGENCIES:
        try:
            rows,state=collect(fetch,agency,report.get(agency),full)
            updated,counts=merge_platforms(base,updated,rows);report[agency]={**state,**counts}
            print(agency,counts,'checked',state['checked_profiles'],flush=True)
        except (OSError,ValueError,UnicodeError) as e:report.setdefault(agency,{})['last_error']=type(e).__name__
    return updated
