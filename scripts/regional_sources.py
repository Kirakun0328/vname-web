"""Regional public rosters with recorded publishing activity."""
import datetime
import csv
import io
import json
import re
import zipfile
from global_sources import CID, download, merge_global, valid_name

THAI_LIST = 'https://storage.googleapis.com/thaivtuberranking.appspot.com/v2/channel_data/simple_list.json'
THAI_PREDEBUT = re.compile(r'เตรียมเดบิวต์|ยังไม่เดบิวต์|ก่อนเดบิวต์|pre[\s-]?debut',re.I)
INDONESIA_PAGE = 'https://www.kaggle.com/datasets/ekasetyoagung/indonesian-vtuber-channel-data'
INDONESIA_ARCHIVE = 'https://www.kaggle.com/api/v1/datasets/download/ekasetyoagung/indonesian-vtuber-channel-data?datasetVersionNumber=1'
INDONESIA_DATE = '2024-06-13'
INDONESIA_ROLE = re.compile(r'vtuber|virtual\s*(?:youtuber|streamer)|バーチャル(?:YouTuber|ユーチューバー)',re.I)
INDONESIA_PREDEBUT = re.compile(r'pre[\s-]?debut|debut\s*(?:soon|coming)|(?:will|going to)\s+debut|(?:belum|ga|gak|nggak|tidak)\s+(?:\w+\s+){0,3}debut|calon\s+vtuber|pengen\s+jadi\s+vtuber|bukan\s+["\s]*vtuber|準備中|デビュー予定',re.I)
INDONESIA_NONPERSON = re.compile(r'clips?|clipper|切り抜き|切抜き|compilation|translation|\bofficial agency\b',re.I)


def parse_indonesia(records):
    rows=[]
    ids=set()
    for r in records:
        cid,name=r.get('channel_id',''),r.get('channel_name','')
        if not CID.fullmatch(cid) or cid in ids:
            raise ValueError('Invalid or duplicate Indonesian channel ID')
        ids.add(cid)
        description=r.get('description') or ''
        # Tags can describe other creators. Require a self-description, not tags.
        if (not valid_name(name) or not INDONESIA_ROLE.search(name+'\n'+description)
                or INDONESIA_PREDEBUT.search(name+'\n'+description)
                or INDONESIA_NONPERSON.search(name)
                or not str(r.get('video_count','')).isdigit() or int(r['video_count'])<=0
                or not str(r.get('views_count','')).isdigit() or int(r['views_count'])<=0):
            continue
        handle=r.get('costum_id','')
        rows.append({'source_id':'youtube:'+cid,'youtube_channel_id':cid,'display_name':name,
                     'source_url':'https://www.youtube.com/channel/'+cid,'activity_source':INDONESIA_PAGE,
                     'activity_evidence':'snapshot_self_description_and_published_videos',
                     'source_snapshot_at':INDONESIA_DATE,'snapshot_source':INDONESIA_ARCHIVE,
                     'youtube_handle':handle if re.fullmatch(r'@[^\s/?#]{1,100}',handle) else None,
                     '_youtube_subscribers':int(r['subs_count']) if str(r.get('subs_count','')).isdigit() else None})
    return rows,{'source':INDONESIA_PAGE,'source_snapshot_at':INDONESIA_DATE,'license':'Apache-2.0',
                 'source_records':len(records),'eligible_records':len(rows),
                 'excluded_unconfirmed_or_preparing':len(records)-len(rows)}


def indonesia_snapshot(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names=archive.namelist()
        if names!=['vtuber id database.csv'] or archive.getinfo(names[0]).file_size>5*1024*1024:
            raise ValueError('Unexpected Indonesian snapshot archive')
        records=list(csv.DictReader(io.StringIO(archive.read(names[0]).decode('utf-8-sig'))))
    if not 1000<=len(records)<=2000:
        raise ValueError('Incomplete Indonesian snapshot')
    return parse_indonesia(records)


def timestamp(value):
    try:
        parsed=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=datetime.timezone.utc)
    except (ValueError,TypeError,AttributeError):
        return None


def parse_thai(document, now=None):
    now=now or datetime.datetime.now(datetime.timezone.utc)
    records=document.get('result')
    if not isinstance(records,list) or not 100<=len(records)<=20000:
        raise ValueError('Incomplete Thai VTuber roster')
    rows=[]
    ids=set()
    for r in records:
        cid,name=r.get('channel_id',''),r.get('title','')
        if not CID.fullmatch(cid) or cid in ids:
            raise ValueError('Invalid or duplicate Thai channel ID')
        ids.add(cid)
        published=timestamp(r.get('last_published_video_at'))
        views=r.get('views')
        if (not valid_name(name) or THAI_PREDEBUT.search(name)
                or not published or published>now or not isinstance(views,int) or views<=0):
            continue
        updated=r.get('updated_at')
        snapshot=datetime.datetime.fromtimestamp(updated/1000,datetime.timezone.utc).isoformat() if isinstance(updated,(int,float)) else None
        rows.append({'source_id':'youtube:'+cid,'youtube_channel_id':cid,'display_name':name,
                     'source_url':'https://www.youtube.com/channel/'+cid,'activity_source':THAI_LIST,
                     'activity_evidence':'regional_directory_published_video_and_views',
                     'activity_published_at':published.isoformat(),'source_snapshot_at':snapshot,
                     '_youtube_subscribers':r.get('subscribers')})
    return rows,{'source':THAI_LIST,'source_records':len(records),'eligible_records':len(rows),
                 'excluded_unconfirmed_or_preparing':len(records)-len(rows)}


def refresh_regional(base, previous, vdb, report):
    updated=previous
    try:
        rows,info=parse_thai(json.loads(download(THAI_LIST)))
        updated,counts=merge_global(base,updated,rows,vdb)
        report['thai_vtuber']=dict(info,**counts,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
        print('thai_vtuber',counts,flush=True)
    except (OSError,ValueError,KeyError,TypeError,OverflowError) as error:
        print('Thai roster unavailable; previous records retained:',type(error).__name__,flush=True)
    if report.get('indonesia_snapshot',{}).get('imported_version')!=1:
        try:
            rows,info=indonesia_snapshot(download(INDONESIA_ARCHIVE,cap=5*1024*1024))
            updated,counts=merge_global(base,updated,rows,vdb)
            report['indonesia_snapshot']=dict(info,**counts,imported_version=1,checked_at=datetime.date.today().isoformat())
            print('indonesia_snapshot',counts,flush=True)
        except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile) as error:
            print('Indonesian snapshot unavailable; previous records retained:',type(error).__name__,flush=True)
    return updated
