"""Official active V-liver roster and person-scoped broadcast accounts."""
import datetime
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import unquote
from directory_sources import Document
from platform_sources import canonical_account
from broad_sources import preparing

ROSTER = 'https://vliver.321.inc/liver/'

def has_class(node, cls):
    return cls in node.attrs.get('class', '').split()

def roster_urls(document):
    root = Document(document).root
    if '活躍中の321所属Vライバー' not in root.content():
        raise ValueError('Active V-liver roster evidence missing')
    return sorted({a.attrs['href'] for a in root.all('a')
                   if re.fullmatch(r'https://vliver\.321\.inc/liver/[^/]+/', a.attrs.get('href', ''))
                   and a.content().strip()})

def parse_profile(document, url):
    root = Document(document).root
    names = [n for n in root.all('h1') if n.content().strip() and has_class(n.parent, 'catch-name')]
    if len(names) != 1:
        raise ValueError('Profile name missing')
    name = names[0].content().strip()
    regions = [n for n in root.all('div') if has_class(n, 'liver-profile')]
    if len(regions) != 1 or preparing(name) or preparing(regions[0].content()):
        return None
    region = regions[0]
    broadcast = [n for n in region.all('div') if has_class(n, 'delivery-account')]
    if len(broadcast) != 1:
        return None
    primary = {a['platform'] for n in broadcast[0].all('a')
               if (a := canonical_account(n.attrs.get('href'))) and a['platform'] in ('reality','iriam','17live','tiktok')}
    if not primary:
        return None
    accounts = {}
    for n in region.all('a'):
        a = canonical_account(n.attrs.get('href'))
        if a: accounts[(a['platform'],a['id'])] = a
    return {'source_id':'agency-321:'+unquote(url.rstrip('/').rsplit('/',1)[-1]),
            'display_name':name,'source_url':url,'activity_source':ROSTER,
            'activity_evidence':'official_active_vliver_roster_and_person_profile',
            'activity_checked_at':datetime.date.today().isoformat(),
            'vliver_source':ROSTER,'primary_platforms':sorted(primary),
            'primary_platform_source':url,'primary_platform_evidence':'official_broadcast_destination',
            'platform_accounts':list(accounts.values())}

def collect(fetch, urls):
    def get(url):
        try:return url,parse_profile(fetch(url),url),None
        except (OSError,ValueError,UnicodeError) as error:return url,None,type(error).__name__
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(get,urls))
    return [r for _,r,_ in results if r], [u for u,_,e in results if e]
