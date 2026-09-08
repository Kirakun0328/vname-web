"""Additional official V-liver directories with explicit debut or streaming evidence."""
import datetime
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urljoin, urlencode, urlsplit
from broad_sources import text, preparing
from platform_sources import accounts_from, canonical_account, links, merge_platforms

RAZZ='https://razz.jp/liver'
LIVE_FEEDS={'listart':'https://listart.jp/'}
ATOMS='https://kyampus.me/atoms/liver'
UUID=re.compile(r'(?:[0-9a-f]{32}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})',re.I)


def embedded_json(document,element_id):
    m=re.search(r'<script\b[^>]*\bid=["\']'+re.escape(element_id)+r'["\'][^>]*>(.*?)</script>',document,re.S)
    if not m:raise ValueError('Public roster data missing')
    return json.loads(m[1])


def iriam_account(uid):
    if not isinstance(uid,str) or not UUID.fullmatch(uid):return None
    # The official source publishes an IRIAM app URI. Keep the real URI for
    # identity matching; do not invent a web share token from the UUID.
    return {'platform':'iriam','id':uid.lower(),'url':'iriam://p?applicationModel=profile&uid='+uid.lower()}


def parse_razz(document,today=None):
    today=today or datetime.datetime.now(datetime.timezone.utc).date()
    nodes=embedded_json(document,'__NUXT_DATA__')
    if not isinstance(nodes,list):raise ValueError('Unexpected Razz payload')
    def decode(index,depth=0):
        if not isinstance(index,int) or index<0:return None
        if index>=len(nodes) or depth>20:raise ValueError('Invalid payload reference')
        value=nodes[index]
        if isinstance(value,dict):return {key:decode(ref,depth+1) for key,ref in value.items()}
        if isinstance(value,list):return [decode(ref,depth+1) for ref in value if isinstance(ref,int)]
        return value
    rows={}
    for index,node in enumerate(nodes):
        if not isinstance(node,dict) or not {'slug','name','debut_date','iriam_info'}.issubset(node):continue
        item=decode(index)
        slug=item['slug'];name=item['name']
        if not isinstance(slug,str) or not re.fullmatch(r'[\w-]+',slug) or not isinstance(name,str) or not name.strip() or preparing(name):continue
        try:debut=datetime.date.fromisoformat(item['debut_date'][:10])
        except (ValueError,TypeError):continue
        # A date in the past on the official debut record is required.
        if debut>=today:continue
        uri=(item.get('iriam_info') or {}).get('profile_deep_link_url','')
        account=canonical_account(uri)
        if not account or account['platform']!='iriam':continue
        url=RAZZ+'/'+slug
        row={'source_id':'agency-razz:'+slug,'display_name':name.strip(),'source_url':url,'category':'VTuber',
             'activity_source':url,'activity_evidence':'official_past_debut_date','activity_snapshot_at':debut.isoformat(),
             'vliver_source':url,'platforms':['iriam'],'platform_sources':{'iriam':url},
             'primary_platforms':['iriam'],'primary_platform_source':url,'primary_platform_evidence':'official_iriam_profile',
             'platform_accounts':[account]}
        if isinstance(item.get('name_kana'),str) and item['name_kana'].strip():
            row.update(reading=item['name_kana'].strip(),reading_source=url,reading_source_kind='official')
        if isinstance(item.get('name_en'),str) and item['name_en'].strip():
            row.update(romanized_name=item['name_en'].strip(),romanized_source=url)
        xid=str(item.get('x_id') or '')
        if re.fullmatch(r'\d+',xid):row['platform_accounts'].append(canonical_account('https://x.com/i/user/'+xid))
        rows[slug]=row
    if not rows:raise ValueError('No verified Razz entries')
    return list(rows.values())


def parse_live_feed(document,agency):
    source=LIVE_FEEDS[agency];items=embedded_json(document,'iriam-broadcasters-data')
    if not isinstance(items,list) or not items:raise ValueError('Empty live roster')
    rows=[]
    for item in items:
        name=item.get('Name');account=iriam_account(item.get('UserId'))
        if not account or not isinstance(name,str) or not name.strip() or preparing(name):continue
        duration=item.get('StreamedTime',0)
        if not isinstance(duration,(int,float)) or isinstance(duration,bool):continue
        if duration<=0 and item.get('LiveStatus')!='STREAMING':continue
        row={'source_id':'iriam:'+account['id'],'display_name':name.strip(),'source_url':source,'category':'VTuber',
             'activity_source':source,'activity_evidence':'official_positive_streaming_time_or_live',
             'vliver_source':source,'platform_accounts':[account],
             'platforms':['iriam'],'platform_sources':{'iriam':source},
             'primary_platforms':['iriam'],'primary_platform_source':source,'primary_platform_evidence':'agency_iriam_streaming_record'}
        rows.append(row)
    return rows


def atoms_urls(document):
    return sorted(set(urljoin(ATOMS,u) for u in links(document) if re.fullmatch(r'/atoms/liver/[\w-]+',u) and u.rsplit('/',1)[-1] not in ('17live','Rank')))


def atoms_next(document,page):
    button=re.search(r'<button\b[^>]*data-load-more-trigger[^>]*>',document)
    if not button:return None
    attrs=dict(re.findall(r'([\w-]+)="([^"]*)"',button[0]))
    cid=attrs.get('data-next-cms-content-id');offset=attrs.get('data-next-offset')
    if not cid or not offset or not offset.isdigit():return None
    return ATOMS+'/__load-more__?'+urlencode({'uuid':'2b075714-dfc1-496a-a324-93205f86fc0f','page':page,'cmsContentId':cid,'__sd_nextOffset':offset})


class Element:
    def __init__(self,tag,attrs=None,parent=None):
        self.tag=tag;self.attrs=dict(attrs or []);self.parent=parent;self.children=[]
    def content(self):
        if self.tag in ('script','style'):return ''
        return ''.join(c.content() if isinstance(c,Element) else c for c in self.children)
    def all(self,tag):
        for child in self.children:
            if isinstance(child,Element):
                if child.tag==tag:yield child
                yield from child.all(tag)


class Document(HTMLParser):
    def __init__(self,source):
        super().__init__();self.root=Element('root');self.current=self.root;self.feed(source)
    def handle_starttag(self,tag,attrs):
        node=Element(tag,attrs,self.current);self.current.children.append(node)
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.current=node
    def handle_endtag(self,tag):
        node=self.current
        while node.parent:
            if node.tag==tag:self.current=node.parent;break
            node=node.parent
    def handle_data(self,value):self.current.children.append(value)


def parse_atoms(document,url,today=None):
    today=today or datetime.datetime.now(datetime.timezone.utc).date()
    title=re.search(r'<title>(.*?)\| Atoms',document,re.S)
    if not title:raise ValueError('Atoms name missing')
    name=text(title[1]).strip()
    root=Document(document).root
    names=[p for p in root.all('p') if text(p.content()).strip()==name]
    if not names:raise ValueError('Atoms profile name missing')
    region=None;date=None
    for candidate in names:
        node=candidate.parent
        for _ in range(4):
            if not node or node.tag in ('body','html','root'):break
            found=re.search(r'(?:デビュー日|初配信日)[：:]\s*(\d{4})[/.年](\d{1,2})[/.月](\d{1,2})',node.content())
            if found:region=node;date=found;break
            node=node.parent
        if region:break
    if not region:return None
    if preparing(name) or preparing(region.content()):return None
    try:debut=datetime.date(*map(int,date.group(1,2,3)))
    except ValueError:return None
    if debut>=today:return None
    accounts={}
    for link in region.all('a'):
        account=canonical_account(link.attrs.get('href'))
        if account:accounts[(account['platform'],account['id'])]=account
    accounts=list(accounts.values());reality=[a for a in accounts if a['platform']=='reality']
    if len(reality)!=1:return None
    row={'source_id':'agency-atoms:'+url.rsplit('/',1)[-1],'display_name':name,'source_url':url,'category':'VTuber',
         'activity_source':url,'activity_evidence':'official_past_debut_date','activity_snapshot_at':debut.isoformat(),
         'vliver_source':url,'platform_accounts':accounts,'platforms':['reality'],'platform_sources':{'reality':url},
         'primary_platforms':['reality'],'primary_platform_source':url,'primary_platform_evidence':'official_broadcast_destination'}
    paragraphs=[text(p.content()).strip() for p in region.all('p')]
    at=paragraphs.index(name);roman=paragraphs[at+1] if at+1<len(paragraphs) else ''
    if re.fullmatch(r"[A-Za-z][A-Za-z .,'-]+",roman):row.update(romanized_name=roman,romanized_source=url)
    return row


def refresh_directories(fetch,base,previous,report,full=False):
    updated=previous
    for agency,url,parser in [('razz',RAZZ,parse_razz),*[(a,u,lambda s,a=a:parse_live_feed(s,a)) for a,u in LIVE_FEEDS.items()]]:
        try:
            rows=parser(fetch(url));updated,counts=merge_platforms(base,updated,rows)
            report[agency]={'source':url,'verified_source_records':len(rows),**counts}
            print(agency,report[agency],flush=True)
        except (OSError,ValueError,UnicodeError) as error:
            report.setdefault(agency,{})['last_error']=type(error).__name__
            print(agency,'unavailable; retained existing records',type(error).__name__,flush=True)
    try:
        doc=fetch(ATOMS);urls=set(atoms_urls(doc));seen=set()
        for page in range(2,30):
            next_url=atoms_next(doc,page)
            if not next_url:break
            if next_url in seen:raise ValueError('Repeated pagination')
            seen.add(next_url);doc=fetch(next_url);urls.update(atoms_urls(doc))
        ordered=sorted(urls)
        if len(ordered)<30:raise ValueError('Incomplete Atoms directory')
        state=report.get('atoms',{});start=0 if full else state.get('next_index',0)%len(ordered)
        limit=len(ordered) if full else 40;targets=ordered[start:start+limit]
        targets=list(dict.fromkeys(targets+[u for u in state.get('retry_urls',[]) if u in urls][:8]))
        def get(url):
            try:return url,parse_atoms(fetch(url),url),None
            except (OSError,ValueError,UnicodeError) as error:return url,None,type(error).__name__
        with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(get,targets))
        rows=[r for u,r,e in results if r];updated,counts=merge_platforms(base,updated,rows)
        report['atoms']={'source':ATOMS,'candidate_profiles':len(ordered),'checked_profiles':len(results),'verified_source_records':len(rows),
                         'next_index':(start+len(targets))%len(ordered),'retry_urls':[u for u,r,e in results if e],**counts}
        print('atoms',report['atoms'],flush=True)
    except (OSError,ValueError,UnicodeError) as error:
        report.setdefault('atoms',{})['last_error']=type(error).__name__
        print('Atoms unavailable; retained existing records',type(error).__name__,flush=True)
    from official_rosters import refresh as refresh_official
    updated=refresh_official(fetch,base,updated,report,full)
    from expanded_agencies import refresh as refresh_expanded
    return refresh_expanded(fetch,base,updated,report,full)
