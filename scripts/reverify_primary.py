"""Recheck individual official profiles, retaining unresolved identities in a queue.

Candidate accounts/names are leads from the historical dictionary, NOT evidence.
Only fields actually read on an exact linked-account match receive a new source.
"""
import argparse
import datetime
import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlsplit
from directory_sources import Document, Element
from platform_sources import canonical_account, record_accounts
from reading_sources import fetch_reading, page_data, kana
from update_dictionary import read_js

ROOT = Path(__file__).resolve().parents[1]
HOLO = 'https://hololive.hololivepro.com/talents/'
NIJI = 'https://www.nijisanji.jp/talents'


def records():
    merged = {}
    for file, variable in [('data.js','VTUBER_DATA'), ('extra-data.js','VTUBER_EXTRA'), ('platform-data.js','VTUBER_PLATFORMS')]:
        for row in read_js(ROOT/file, variable):
            merged.setdefault(row['source_id'], {}).update(row)
    return merged


def holo_urls(document):
    return sorted({urljoin(HOLO,a.attrs.get('href','')) for a in Document(document).root.all('a')
                   if re.fullmatch(r'https://hololive\.hololivepro\.com/talents/[a-z0-9-]+/',urljoin(HOLO,a.attrs.get('href','')))})


def parse_holo(document, url):
    root = Document(document).root
    sections = [n for n in root.all('div') if 'right_box' in n.attrs.get('class','').split() and list(n.all('h1'))]
    if len(sections) != 1: raise ValueError('Ambiguous individual profile')
    region = sections[0]; headings = list(region.all('h1'))
    if len(headings) != 1: raise ValueError('Ambiguous name')
    heading = headings[0]
    name = ''.join(c for c in heading.children if isinstance(c,str)).strip()
    english = ' '.join(n.content().strip() for n in heading.all('span'))
    sns = [n for n in region.all('ul') if 't_sns' in n.attrs.get('class','').split()]
    accounts = [canonical_account(a.attrs.get('href')) for n in sns for a in n.all('a')]
    accounts = [a for a in accounts if a]
    channels = [a for a in accounts if a['platform']=='youtube' and a['id'].startswith('channel/')]
    if not name or len(channels)!=1: raise ValueError('Exact own-channel link required')
    debut = ''
    for section in root.all('div'):
        if 'talent_data' not in section.attrs.get('class','').split(): continue
        for dl in section.all('dl'):
            terms=list(dl.all('dt')); values=list(dl.all('dd'))
            if len(terms)!=1 or len(values)!=1 or terms[0].content().strip()!='初配信日': continue
            m=re.fullmatch(r'(\d{4})年(\d{1,2})月(\d{1,2})日',values[0].content().strip())
            if m: debut=datetime.date(*map(int,m.groups())).isoformat()
    if not debut or debut>=datetime.date.today().isoformat(): raise ValueError('Past first-stream date required')
    return {'display_name':name,'romanized_name':english,'romanized_source':url,
            'platform_accounts':accounts,'debut_date':debut,'source_url':url,'name_source':url,
            'activity_source':url,'activity_evidence':'official_past_first_stream_date'}


def account_index(all_records):
    index={}
    for sid,r in all_records.items():
        for a in record_accounts(r):
            index.setdefault((a['platform'],a['id']),set()).add(sid)
    return index


def match_patch(row, all_records, stamp, index=None):
    wanted={(a['platform'],a['id']) for a in row['platform_accounts'] if a['platform']=='youtube'}
    index=account_index(all_records) if index is None else index
    matches=list(set().union(*(index.get(a,set()) for a in wanted)))
    if len(matches)!=1: return None
    # Do not relabel unverified aliases, readings or other platforms as official.
    sid=matches[0]
    if all_records[sid]['display_name']!=row['display_name']:
        row={**row,'reading':'','reading_source':'','reading_source_kind':''}
    return {'source_id':sid,**row,'identity_checked_at':stamp,
            'verified_fields':['display_name','romanized_name','platform_accounts','debut_date'],
            'migration_status':'identity_and_activity_rechecked'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=40);parser.add_argument('--offline',action='store_true')
    args=parser.parse_args(); all_records=records()
    path=ROOT/'primary-data.js';previous=read_js(path,'VTUBER_PRIMARY') if path.exists() else []
    patches={r['source_id']:r for r in previous}
    index=account_index(all_records)
    state_path=ROOT/'scripts/primary-recheck-report.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else {}
    state.pop('youtube_api_configured',None)
    checked=state.get('profiles',{}); stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not args.offline:
        try:
            urls=holo_urls(fetch_reading(HOLO))
            if not urls: raise ValueError('Official discovery unavailable')
            targets=sorted(urls,key=lambda u:checked.get(u,{}).get('attempted_at',''))[:args.limit]
            def get(url):
                try:return url,parse_holo(fetch_reading(url),url),None
                except (OSError,ValueError,KeyError,TypeError):return url,None,'unavailable_or_unconfirmed'
            with ThreadPoolExecutor(max_workers=3) as pool:
                for url,row,error in pool.map(get,targets):
                    patch=match_patch(row,all_records,stamp,index) if row else None
                    checked[url]={'attempted_at':stamp,'status':'verified' if patch else error or 'identity_match_pending'}
                    if patch: patches[patch['source_id']]=patch
            state['holo_candidates']=len(urls)
        except (OSError,ValueError,KeyError,TypeError) as error:
            state['discovery_error']=type(error).__name__
    state.update(profiles=checked,updated_at=stamp,records_total=len(all_records),
                 individually_rechecked=len(patches),remaining_without_this_recheck=len(all_records)-len(patches),
                 scope='Hololive individual official profiles; other identities remain queued. Existing independent agency verification is not counted here.',
                 status='in_progress')
    values=list(patches.values())
    for file,value in [(path,'// Independently rechecked fields; historical provenance remains in original records.\nwindow.VTUBER_PRIMARY = '+json.dumps(values,ensure_ascii=False,separators=(',',':'))+';\n'),
                       (state_path,json.dumps(state,ensure_ascii=False,indent=2)+'\n')]:
        tmp=file.with_suffix(file.suffix+'.tmp');tmp.write_text(value,encoding='utf-8');tmp.replace(file)
    print(json.dumps({k:v for k,v in state.items() if k!='profiles'},ensure_ascii=False))

if __name__=='__main__':main()
