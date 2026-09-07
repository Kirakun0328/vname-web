"""2019 public channel snapshot, requiring self-description and posted videos."""
import datetime
import json
import re
from global_sources import download, valid_name, CID, merge_global

SNAPSHOT_COMMIT = 'cfa62639e60af5904b4faf5ae5d9a1702a80c4a7'
SNAPSHOT_DATE = '2019-10-27'
ROOT = 'https://raw.githubusercontent.com/Imamachi-n/Virtual-Youtuber-API/'+SNAPSHOT_COMMIT+'/Batch/data/'
STATS_URL = ROOT+'VTuber_alldata.json'
META_FILES = ['basic_channel_VTuber_1.json', 'basic_channel_VTuber_2.json']
ROLE = re.compile(r'(?:個人勢|新人|系|バーチャル)[a-z]*vtuber|(?:vtuber|バーチャル(?:YouTuber|ユーチューバー))\s*(?:です|として|の[^。\n]{1,40}です|[、。！!｜|￤])',re.I)
EXCLUDE = re.compile(r'切り抜き|切抜き|まとめ|クリップ|最高の瞬間|に挑む顔出し|システム|翻訳|字幕|clips?|compilation|translation|夫婦|[&＆]|project|どうぶつ|Hoonie friends',re.I)


def parse_legacy(stats, metadata):
    rows = []
    for r in stats:
        cid, name = r.get('channelId',''), r.get('channelTitle','')
        meta = metadata.get(cid,{})
        description = meta.get('desc','')
        videos, views = str(r.get('videoCount','')), str(r.get('viewCount',''))
        if (not CID.fullmatch(cid) or not valid_name(name) or EXCLUDE.search(name)
                or not isinstance(description,str) or not ROLE.search(description)
                or re.search(r'準備中|デビュー予定|初配信予定',description)
                or not videos.isdigit() or int(videos)<=0 or not views.isdigit() or int(views)<=0):
            continue
        source = meta['source_url']
        rows.append({'source_id':'youtube:'+cid, 'youtube_channel_id':cid,
                     'display_name':name, 'source_url':source, 'activity_source':source,
                     'activity_evidence':'snapshot_self_description_and_published_videos',
                     'source_snapshot_at':SNAPSHOT_DATE, 'snapshot_source':STATS_URL,
                     '_youtube_subscribers':int(r['subscriberCount']) if str(r.get('subscriberCount','')).isdigit() else None})
    return rows, {'source':STATS_URL,'source_snapshot_at':SNAPSHOT_DATE,'source_records':len(stats),
                  'eligible_records':len(rows),'excluded_unconfirmed_or_preparing':len(stats)-len(rows)}


def refresh_legacy(base, previous, vdb, report):
    if report.get('legacy_2019',{}).get('imported_snapshot')==SNAPSHOT_COMMIT:
        return previous
    try:
        stats=json.loads(download(STATS_URL))['channels']
        metadata={}
        for name in META_FILES:
            for row in json.loads(download(ROOT+name))['channels']:
                metadata[row['channelId']]=dict(row,source_url=ROOT+name)
        if len(stats)<600 or len(metadata)<300:
            raise ValueError('Incomplete historical roster')
        rows,info=parse_legacy(stats,metadata)
        updated,counts=merge_global(base,previous,rows,vdb)
        report['legacy_2019']=dict(info,**counts,imported_snapshot=SNAPSHOT_COMMIT,checked_at=datetime.date.today().isoformat())
        print('legacy_2019',counts,flush=True)
        return updated
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('2019 snapshot unavailable; previous records retained:',type(error).__name__,flush=True)
        return previous
