"""Additional V-liver rosters, with person-scoped links and debut evidence."""
import datetime
import json
from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
from directory_sources import Document, embedded_json
from broad_sources import preparing, text
from platform_sources import canonical_account, merge_platforms
from reading_sources import kana

OZON = 'https://ozon.jp/v/liver/'
LINEAR = 'https://linear-v.com/'


def has_class(node, name): return name in node.attrs.get('class', '').split()


def dated_debut(node, today):
    for dl in node.all('dl'):
        terms = list(dl.all('dt')); values = list(dl.all('dd'))
        if len(terms) != len(values): continue
        for term, value in zip(terms, values):
            if text(term.content()).strip() not in ('デビュー', 'デビュー日'): continue
            m = re.fullmatch(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text(value.content()).strip())
            if not m: return None
            try: date = datetime.date(*map(int, m.groups()))
            except ValueError: return None
            return date.isoformat() if date < today else None
    return None


def person_row(node, name, source, sid, date, platform):
    accounts = {}
    for a in node.all('a'):
        account = canonical_account(a.attrs.get('href'))
        if account: accounts[(account['platform'], account['id'])] = account
    if len([a for a in accounts.values() if a['platform'] == platform]) != 1: return None
    row = {'source_id':sid, 'display_name':name, 'source_url':source,
           'activity_source':source, 'activity_evidence':'official_past_debut_date',
           'activity_snapshot_at':date, 'vliver_source':source,
           'primary_platforms':[platform], 'primary_platform_source':source,
           'primary_platform_evidence':'official_broadcast_destination',
           'platform_accounts':list(accounts.values())}
    return row


def parse_ozon(document, today=None):
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    nodes = [n for n in Document(document).root.all('div') if has_class(n, 'remodal') and n.attrs.get('data-remodal-id', '').startswith('modal-')]
    if not nodes: raise ValueError('OZON profiles missing')
    rows = {}
    for node in nodes:
        names = [n.content().strip() for n in node.all('p') if has_class(n, 'v-name-b')]
        if len(names) != 1 or preparing(names[0]): continue
        date = dated_debut(node, today)
        if not date: continue
        slug = node.attrs['data-remodal-id']; source = OZON+'#'+slug
        row = person_row(node, names[0], source, 'agency-ozon:'+slug, date, 'iriam')
        if not row: continue
        readings = [kana(n.content().strip()) for n in node.all('p') if has_class(n, 'v-name-kana')]
        if len(readings) == 1 and readings[0]: row.update(reading=readings[0], reading_source=source, reading_source_kind='official')
        icon = next((urljoin(OZON,n.attrs['src']) for n in node.all('img') if has_class(n,'plofile-img') and n.attrs.get('src')), None)
        if icon and icon.startswith('https://ozon.jp/'): row.update(icon_url=icon, icon_source=source, icon_kind='profile')
        rows[slug] = row
    if not rows: raise ValueError('No verified OZON records')
    return list(rows.values())


def linear_urls(document):
    items = embedded_json(document, 'members-data')
    urls = [r.get('permalink','') for r in items if isinstance(r,dict)]
    if len(urls) < 30 or any(not re.fullmatch(r'https://linear-v\.com/talent/\d+/',u) for u in urls): raise ValueError('Invalid Linear roster')
    if len(set(urls)) != len(urls): raise ValueError('Duplicate Linear profiles')
    return sorted(urls)


def parse_linear(document, url, today=None):
    today = today or datetime.datetime.now(datetime.timezone.utc).date()
    root = Document(document).root
    names = [n for n in root.all('h2') if has_class(n,'talent-profile__name')]
    if len(names) != 1: raise ValueError('Linear name missing')
    name = text(names[0].content()).strip()
    node = names[0].parent
    for _ in range(5):
        if not node or node.tag in ('body','html','root'): return None
        if list(node.all('dl')) and any(has_class(n,'talent-profile__sns') for n in node.all('div')): break
        node = node.parent
    else: return None
    date = dated_debut(node,today)
    if not date or preparing(node.content()): return None
    # Read the explicit broadcast badge, not unrelated platform links/footer.
    platforms = {'IRIAM':'iriam','REALITY':'reality','17LIVE':'17live','TikTok':'tiktok','TikTok LIVE':'tiktok'}
    badges = [text(n.content()).strip() for n in node.all('span') if has_class(n,'talent-profile__badge')]
    platform = next((platforms[b] for b in badges if b in platforms), None)
    if not platform:
        destinations = {a['platform'] for link in node.all('a') if 'talent-profile__sns-link--' in link.attrs.get('class','') and (a:=canonical_account(link.attrs.get('href'))) and a['platform'] in ('iriam','reality','17live','tiktok')}
        if len(destinations)==1: platform=next(iter(destinations))
    if not platform: return None
    row = person_row(node,name,url,'agency-linear:'+url.rstrip('/').rsplit('/',1)[-1],date,platform)
    if not row: return None
    # The profile's standing image is outside the biography but inside its own
    # profile container; never borrow a related member's thumbnail.
    icons = [n.attrs.get('src','') for n in root.all('img') if has_class(n,'talent-slider__img') and has_class(n,'wp-post-image')]
    if len(icons)==1 and icons[0].startswith('https://linear-v.com/'):
        row.update(icon_url=icons[0],icon_source=url,icon_kind='profile')
    return row


def refresh(fetch, base, previous, report, full=False):
    reviewed=json.loads(Path(__file__).with_name('reviewed-platforms.json').read_text())
    updated,counts=merge_platforms(base,previous,reviewed)
    report['reviewed_platforms']={'source_records':len(reviewed),**counts}
    try:
        rows = parse_ozon(fetch(OZON)); updated, counts = merge_platforms(base,updated,rows)
        report['ozon'] = {'source':OZON,'verified_source_records':len(rows),**counts}
        print('OZON',report['ozon'],flush=True)
    except (OSError,ValueError,UnicodeError) as error:
        report.setdefault('ozon',{})['last_error'] = type(error).__name__
    try:
        urls = linear_urls(fetch(LINEAR)); state = report.get('linear',{})
        start = 0 if full else state.get('next_index',0)%len(urls)
        targets = urls[start:start+(len(urls) if full else 40)]
        targets = list(dict.fromkeys(targets+[u for u in state.get('retry_urls',[]) if u in urls][:8]))
        def get(url):
            try: return url,parse_linear(fetch(url),url),None
            except (OSError,ValueError,UnicodeError) as error: return url,None,type(error).__name__
        with ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(get,targets))
        rows = [r for u,r,e in results if r]; updated,counts=merge_platforms(base,updated,rows)
        report['linear'] = {'source':LINEAR,'candidate_profiles':len(urls),'checked_profiles':len(results),
                            'verified_source_records':len(rows),'next_index':(start+len(targets))%len(urls),
                            'retry_urls':[u for u,r,e in results if e],**counts}
        print('Linear',report['linear'],flush=True)
    except (OSError,ValueError,UnicodeError) as error:
        report.setdefault('linear',{})['last_error'] = type(error).__name__
    return updated
