"""Refresh platform sources independently, preserving records on source failure."""
import argparse
import json
from pathlib import Path
from update_dictionary import read_js, fetch
from reading_sources import fetch_reading
from platform_sources import AGENCIES, AVVY_INTERVIEW, merge_platforms, refresh_agency, parse_avvy_interviews, enrich_known_accounts

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--full',action='store_true')
    args=parser.parse_args()
    merged={r['source_id']:r for r in read_js(ROOT/'data.js','VTUBER_DATA')}
    for row in read_js(ROOT/'extra-data.js','VTUBER_EXTRA'):merged.setdefault(row['source_id'],{}).update(row)
    target=ROOT/'platform-data.js'
    previous=read_js(target,'VTUBER_PLATFORMS') if target.exists() else []
    updated=previous
    report_path=ROOT/'scripts/platform-report.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else {}
    try:
        vdb=json.loads(fetch('https://vdb.vtbs.moe/json/list.json'))
        updated,count=enrich_known_accounts(list(merged.values()),updated,vdb)
        report['vdb_accounts']={'source':'https://vdb.vtbs.moe/','enriched_existing_records':count}
    except (OSError,ValueError,UnicodeError) as error:
        print('VDB platform accounts unavailable; existing metadata retained',type(error).__name__,flush=True)
    for agency in AGENCIES:
        try:
            rows,state=refresh_agency(fetch_reading,agency,report.get(agency),limit=1500 if args.full else 40)
            updated,counts=merge_platforms(list(merged.values()),updated,rows)
            report[agency]=dict(state,**counts)
            print(agency,counts,'checked:',state['checked_profiles'],flush=True)
        except (OSError,ValueError,UnicodeError) as error:
            report.setdefault(agency,{})['last_error']=type(error).__name__
            print(agency,'unavailable; existing records retained',type(error).__name__,flush=True)
    try:
        rows=parse_avvy_interviews(fetch_reading(AVVY_INTERVIEW))
        updated,counts=merge_platforms(list(merged.values()),updated,rows)
        report['avvy_interviews']=dict(source=AVVY_INTERVIEW,source_records=len(rows),**counts)
    except (OSError,ValueError,UnicodeError) as error:
        report.setdefault('avvy_interviews',{})['last_error']=type(error).__name__
        print('Avvy interviews unavailable; existing records retained',type(error).__name__,flush=True)
    for row in updated:merged.setdefault(row['source_id'],{}).update(row)
    from broad_sources import preparing
    listed=[r for r in merged.values() if r.get('listing_status')!='predebut' and not preparing(r['display_name'])]
    from platform_sources import LABELS
    report['records']={'listed':len(listed),'platform_records':len(updated),
                       'with_primary_platforms':sum(bool(r.get('primary_platforms')) for r in listed),
                       'platform_counts':{p:sum(p in r.get('platforms',[]) for r in listed) for p in LABELS}}
    content='// Public V-liver identities and source-linked platform metadata.\nwindow.VTUBER_PLATFORMS = '+json.dumps(updated,ensure_ascii=False,separators=(',',':'))+';\n'
    for path,value in [(target,content),(report_path,json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
        temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(value,encoding='utf-8');temp.replace(path)
    print(report['records'],flush=True)

if __name__=='__main__':main()
