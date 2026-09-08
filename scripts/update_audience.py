"""Hourly public audience refresh, independent of slower discovery."""
import json,datetime
from pathlib import Path
from update_dictionary import read_js
from popularity_sources import refresh, merge_counts, list_counts
from reading_sources import fetch_reading
ROOT=Path(__file__).resolve().parents[1]

def main():
    records={}
    for file,var in [('data.js','VTUBER_DATA'),('extra-data.js','VTUBER_EXTRA'),('platform-data.js','VTUBER_PLATFORMS')]:
        for r in read_js(ROOT/file,var):records.setdefault(r['source_id'],{}).update(r)
    base=list(records.values());report_path=ROOT/'scripts/audience-report.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else {}
    # Store metrics separately so platform identity refresh cannot overwrite fresher counts.
    previous=read_js(ROOT/'audience-data.js','VTUBER_AUDIENCE') if (ROOT/'audience-data.js').exists() else []
    updated=refresh(fetch_reading,base,previous,report)
    try:
        from ai_list_sources import collect
        rows=list_counts(collect(fetch_reading));updated,count=merge_counts(base,updated,rows)
        report['aituberlist']={'source_records':len(rows),'enriched_records':count,'status':'ok'}
    except (OSError,ValueError,KeyError) as e:report['aituberlist']={'status':'unavailable','error':type(e).__name__}
    try:
        from broad_sources import collect_post
        channels,state=collect_post(batch_size=20,state=report.get('post_rotation'))
        stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        rows=[{'platform':'youtube','account_id':'channel/'+r['channel_id'],'count':r['subscribers'],'source':r.get('source_url','https://vtuber-post.com/database_detail.html?id='+r['channel_id']),'checked_at':stamp[:10],'retrieved_at':stamp} for r in channels]
        updated,count=merge_counts(base,updated,rows);report['post_rotation']={**state,'enriched_records':count}
    except (OSError,ValueError,KeyError) as e:report.setdefault('post_rotation',{})['last_error']=type(e).__name__
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['retrieved_at']=stamp
    for file,content in [(ROOT/'audience-data.js','// Public source audience snapshots.\nwindow.VTUBER_AUDIENCE = '+json.dumps(updated,ensure_ascii=False,separators=(',',':'))+';\n'),(ROOT/'audience-data.json',json.dumps(updated,ensure_ascii=False,separators=(',',':'))+'\n'),(report_path,json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
        tmp=file.with_suffix('.tmp');tmp.write_text(content);tmp.replace(file)
    print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
