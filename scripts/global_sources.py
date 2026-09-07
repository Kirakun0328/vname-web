"""Bulk public rosters with debut/video evidence and account-based identity.

These sources establish past activity, not current availability. Historical
snapshots retain their date; account counts are never described as people.
"""
import datetime
import io
import json
import re
import tarfile
import urllib.request
from broad_sources import preparing

TAIWAN_ARCHIVE = 'https://codeload.github.com/TaiwanVtuberData/TaiwanVTuberTrackingDataJson/tar.gz/refs/heads/master'
TAIWAN_RAW = 'https://raw.githubusercontent.com/TaiwanVtuberData/TaiwanVTuberTrackingDataJson/master/api/v2/vtubers/'
HOLOLIST_SNAPSHOT = 'https://github.com/xoltia/vtuber-database/releases/download/2024-09-14/vtubers-detailed-with-youtube.json'
HOLOLIST_DATE = datetime.date(2024, 9, 14)
PREPARING = re.compile(r'準備中|准备中|未出道|出道前|데뷔\s*준비|pre[\s-]?debut', re.I)
CID = re.compile(r'UC[\w-]{22}')


def download(url, cap=25*1024*1024):
    request = urllib.request.Request(url, headers={'User-Agent':'VName-dictionary-updater/3.0 (+https://github.com/Kirakun0328/vname-web)'})
    with urllib.request.urlopen(request, timeout=40) as response:
        data = response.read(cap+1)
    if len(data)>cap:
        raise ValueError('Source exceeds size limit')
    return data


def date_of(value, fmt=None):
    try:
        return datetime.datetime.strptime(value,fmt).date() if fmt else datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def valid_name(name):
    return isinstance(name,str) and 0<len(name.strip())<=300 and not preparing(name) and not PREPARING.search(name)


def individual_profile(url):
    return isinstance(url,str) and bool(re.fullmatch(r'https://hololist\.net/[a-zA-Z0-9_-]+/',url) or re.fullmatch(re.escape(TAIWAN_RAW)+r'[\w-]+\.json',url))


def parse_taiwan_records(records, today=None):
    today = today or datetime.date.today()
    rows = []
    skipped = 0
    for r in records:
        name, rid = r.get('name'), r.get('id')
        if not isinstance(rid,str) or not re.fullmatch(r'[\w-]{1,64}',rid):
            raise ValueError('Invalid Taiwan VTuber identity')
        debut = date_of(r.get('debutDate'))
        video = r.get('popularVideo') or {}
        has_video = (video.get('type')=='YouTube' and bool(re.fullmatch(r'[\w-]{11}',str(video.get('id',''))))) or (video.get('type')=='Twitch' and str(video.get('id','')).isdigit())
        if (r.get('activity') not in ('active','graduate') or not valid_name(name)
                or (debut and debut>today) or not ((debut and debut<=today) or has_video)):
            skipped += 1
            continue
        youtube, twitch = r.get('YouTube') or {}, r.get('Twitch') or {}
        cid, login = youtube.get('id'), twitch.get('id')
        if cid and not CID.fullmatch(cid):
            raise ValueError('Invalid Taiwan YouTube channel')
        if login and not re.fullmatch(r'[a-zA-Z0-9_]{1,50}',login):
            raise ValueError('Invalid Twitch channel')
        if not cid and not login:
            skipped += 1
            continue
        source = TAIWAN_RAW+rid+'.json'
        rows.append({'source_id':'taiwan:'+rid, 'display_name':name.strip(), 'source_url':source,
                     'youtube_channel_id':cid, 'twitch_login':login.lower() if login else None,
                     'activity_source':source, 'activity_evidence':'directory_past_debut' if debut else 'directory_published_video',
                     'debut_date':debut.isoformat() if debut else None,
                     'activity_status_at_source':r['activity'],
                     '_youtube_subscribers':(youtube.get('subscriber') or {}).get('count'),
                     '_twitch_followers':(twitch.get('follower') or {}).get('count')})
    return rows, {'source_records':len(records), 'eligible_records':len(rows), 'excluded_unconfirmed_or_preparing':skipped}


def parse_taiwan_archive(data, today=None):
    records = []
    snapshot = None
    total_size = 0
    # Read only the advertised public JSON records. Never extract an archive.
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
        for member in archive:
            if re.fullmatch(r'[^/]+/api/v2/vtubers/[\w-]+\.json',member.name):
                if not member.isfile() or member.size>1024*1024:
                    raise ValueError('Unexpected archive entry')
                total_size += member.size
                if total_size>60*1024*1024 or len(records)>=20000:
                    raise ValueError('Archive roster exceeds bounds')
                records.append(json.load(archive.extractfile(member))['VTuber'])
            elif re.fullmatch(r'[^/]+/api/v2/update-time\.json',member.name):
                if not member.isfile() or member.size>10000:
                    raise ValueError('Invalid snapshot metadata')
                snapshot=json.load(archive.extractfile(member))['time']['VTuberDataUpdateTime']
    if len(records)<1000 or len({r['id'] for r in records})!=len(records) or not snapshot:
        raise ValueError('Incomplete Taiwan roster')
    rows, report = parse_taiwan_records(records,today)
    for row in rows:
        row['source_snapshot_at']=snapshot
    return rows, dict(report, source=TAIWAN_ARCHIVE, source_snapshot_at=snapshot)


def parse_hololist(records):
    rows = []
    skipped = 0
    for r in records:
        name = r.get('name')
        cid = r.get('youtube','')
        debut = date_of(r.get('debutDate'),'%B %d, %Y')
        url = r.get('url','')
        if (not valid_name(name) or not CID.fullmatch(cid) or not debut or debut>HOLOLIST_DATE
                or r.get('status') not in ('Active','Retired','Hiatus','Inactive','Hiatus, Retired')):
            skipped += 1
            continue
        if not re.fullmatch(r'https://hololist\.net/[a-zA-Z0-9_-]+/',url):
            raise ValueError('Invalid HoloList source URL')
        aliases = [r.get('originalName'),r.get('youtubeName')]
        rows.append({'source_id':'youtube:'+cid, 'youtube_channel_id':cid, 'display_name':name,
                     'aliases':[n for n in aliases if valid_name(n) and n!=name],
                     'source_url':url, 'activity_source':url, 'activity_evidence':'directory_past_debut',
                     'debut_date':debut.isoformat(), 'source_snapshot_at':HOLOLIST_DATE.isoformat(),
                     'snapshot_source':HOLOLIST_SNAPSHOT, 'activity_status_at_source':r['status'],
                     'youtube_handle':r.get('youtubeHandle') if isinstance(r.get('youtubeHandle'),str) and r['youtubeHandle'].startswith('@') else None})
    return rows, {'source':HOLOLIST_SNAPSHOT,'source_snapshot_at':HOLOLIST_DATE.isoformat(),
                  'source_records':len(records),'eligible_records':len(rows),'excluded_unconfirmed_or_preparing':skipped}


def merge_global(base, previous, rows, vdb):
    merged = {r['source_id']:dict(r) for r in base}
    extra = {r['source_id']:dict(r) for r in previous}
    for r in previous:
        merged.setdefault(r['source_id'],{}).update(r)
    account_ids = {}
    def associate(platform, account, sid):
        if account:
            value=account.casefold() if platform in ('twitch','youtube_handle') else account
            account_ids.setdefault((platform,value),set()).add(sid)
    for sid,r in merged.items():
        associate('youtube',r.get('youtube_channel_id') or (sid[8:] if sid.startswith('youtube:') else None),sid)
        associate('twitch',r.get('twitch_login'),sid)
        associate('youtube_handle',r.get('youtube_handle'),sid)
        for profile in r.get('source_profiles',[]):
            if individual_profile(profile):
                associate('profile',profile,sid)
    for r in vdb.get('vtbs',[]):
        if r.get('uuid') in merged:
            for a in r.get('accounts',[]):
                if a.get('type')=='official' and a.get('platform') in ('youtube','twitch'):
                    associate(a['platform'],a['id'],r['uuid'])
    added=matched=small_youtube=small_twitch=0
    for row in rows:
        if not valid_name(row.get('display_name')):
            raise ValueError('Ineligible global row')
        targets=set()
        for platform,field in [('youtube','youtube_channel_id'),('twitch','twitch_login'),('youtube_handle','youtube_handle')]:
            if row.get(field):
                value=row[field].casefold() if platform in ('twitch','youtube_handle') else row[field]
                targets.update(account_ids.get((platform,value),set()))
        if individual_profile(row['source_url']):
            targets.update(account_ids.get(('profile',row['source_url']),set()))
        if row['source_id'] in merged:
            targets.add(row['source_id'])
        if not targets:
            sid='youtube:'+row['youtube_channel_id'] if row.get('youtube_channel_id') else row['source_id']
            extra[sid]={'source_id':sid,'display_name':row['display_name'],'reading':'','romanized_name':'','source_url':row['source_url']}
            merged[sid]=dict(extra[sid]);targets={sid};added+=1
            small_youtube += isinstance(row.get('_youtube_subscribers'),int) and 0<row['_youtube_subscribers']<1000
            small_twitch += isinstance(row.get('_twitch_followers'),int) and 0<row['_twitch_followers']<1000
        else:
            matched+=1
        for sid in targets:
            old=merged[sid];patch=extra.setdefault(sid,{'source_id':sid})
            aliases=list(dict.fromkeys([*old.get('aliases',[]),row['display_name'],*row.get('aliases',[])]))
            aliases=[n for n in aliases if n!=old['display_name'] and valid_name(n)]
            if aliases:
                patch['aliases']=aliases
            if individual_profile(row['source_url']):
                patch['source_profiles']=list(dict.fromkeys([*old.get('source_profiles',[]),row['source_url']]))
            for field in ('youtube_channel_id','twitch_login','youtube_handle'):
                if row.get(field):
                    patch[field]=row[field]
            if (row.get('reading_source') and row.get('reading_source_kind')=='directory_explicit'
                    and row.get('reading') and not old.get('reading_source')
                    and row['display_name']==old['display_name']):
                for field in ('reading','reading_source','reading_source_kind'):
                    patch[field]=row[field]
            # Preserve a newer verification when importing a historical snapshot.
            if not old.get('activity_source'):
                for field in ('activity_source','activity_evidence','debut_date','source_snapshot_at','snapshot_source','activity_status_at_source','activity_published_at'):
                    if row.get(field):
                        patch[field]=row[field]
                patch['activity_checked_at']=datetime.date.today().isoformat()
            old.update(patch)
            associate('youtube',row.get('youtube_channel_id'),sid)
            associate('twitch',row.get('twitch_login'),sid)
            associate('youtube_handle',row.get('youtube_handle'),sid)
            if individual_profile(row['source_url']):
                associate('profile',row['source_url'],sid)
    return list(extra.values()),{'new_records':added,'matched_existing_accounts':matched,
                                'new_youtube_below_1000':small_youtube,'new_twitch_below_1000':small_twitch}


def refresh_global(base, previous, vdb, report):
    updated=previous
    for name,loader in [('taiwan_vtuber_data',lambda:parse_taiwan_archive(download(TAIWAN_ARCHIVE))),
                        ('hololist_snapshot',lambda:parse_hololist(json.loads(download(HOLOLIST_SNAPSHOT))))]:
        try:
            # The 2024 release is immutable; do not fetch it on every daily run.
            if name=='hololist_snapshot' and report.get(name,{}).get('imported_snapshot')==HOLOLIST_DATE.isoformat():
                continue
            rows,info=loader()
            updated,counts=merge_global(base,updated,rows,vdb)
            report[name]=dict(info,**counts,checked_at=datetime.date.today().isoformat())
            if name=='hololist_snapshot':
                report[name]['imported_snapshot']=HOLOLIST_DATE.isoformat()
            print(name,counts,flush=True)
        except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as error:
            print(name,'unavailable; previous records retained:',type(error).__name__,flush=True)
    return updated
