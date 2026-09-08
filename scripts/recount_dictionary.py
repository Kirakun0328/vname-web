"""Recount the published dictionary after late-stage imports such as SearXNG verification."""
from __future__ import annotations
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def read_js(path,variable):
    text=path.read_text(encoding='utf-8')
    m=re.search(r'window\.'+re.escape(variable)+r'\s*=\s*(\[.*\])\s*;?\s*$',text,re.S)
    if not m: raise ValueError(f'Invalid JS data: {path}')
    return json.loads(m.group(1))


def preparing(name):
    return bool(re.search(r'(?:[a-z]*v(?:irtual)?[\s-]*tuber\s*準備中|準備中\s*(?:個人勢)?\s*[a-z]*vtuber|(?<!再)デビュー準備中|(?<!再)デビュー前|(?:Vライバー|IRIAM|Avvy|REALITY)\s*準備中|準備中\s*Vライバー|未デビュー|\bpre[\s-]?debut\b)',name or '',re.I))


def main():
    merged={}
    for file,var in [('data.js','VTUBER_DATA'),('extra-data.js','VTUBER_EXTRA'),('platform-data.js','VTUBER_PLATFORMS')]:
        path=ROOT/file
        if not path.exists(): continue
        for row in read_js(path,var):
            merged.setdefault(row['source_id'],{}).update(row)
    eligible=[r for r in merged.values() if r.get('display_name') and r.get('listing_status')!='predebut' and not preparing(r.get('display_name'))]
    report_path=ROOT/'scripts/collection-report.json'
    report=json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
    report['records']={
        'stored':len(merged),
        'listed':len(eligible),
        'excluded_predebut':len(merged)-len(eligible),
        'with_activity_source':sum(bool(r.get('activity_source')) for r in eligible),
    }
    report['aivtuber_records']=sum(r.get('category')=='AIVTuber' for r in eligible)
    report['post_import_recount']=True
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'stored':len(merged),'listed':len(eligible),'aivtuber':report['aivtuber_records']},ensure_ascii=False))

if __name__=='__main__':main()
