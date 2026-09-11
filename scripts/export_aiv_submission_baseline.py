"""Export effective legacy layers for build_aiv_submissions.py; no network calls."""
import json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(f):
 s=(root/f).read_text();return json.loads(s[s.index('['):].rstrip(';\n '))
def norm(x):
 import unicodedata
 return re.sub(r'\s','',unicodedata.normalize('NFKC',str(x or '')).lower())
layers=[read(f) for f in ['data.js','extra-data.js','platform-data.js']];primary=read('primary-data.js')
s=(root/'creator-submissions-20260910.js').read_text();start=s.index('[',s.index('const submissions'));subs=json.loads(s[start:s.index('\n];',start)+2])
def ak(a):return a.get('platform','')+':'+norm(a.get('id',''))
byid={};byname={};byaccount={}
for row in sum(layers,[]):
 byid.setdefault(row['source_id'],[]).append(row)
 byname.setdefault(norm(row.get('display_name')),set()).add(row['source_id'])
 for a in row.get('platform_accounts',[]):byaccount.setdefault(ak(a),set()).add(row['source_id'])
for row in primary:byid.setdefault(row['source_id'],[]).append(row)
for sub in subs:
 ids=set()
 if sub['source_id'] in byid:ids.add(sub['source_id'])
 if not sub.get('match_by_identity_only'):ids|=byname.get(norm(sub['display_name']),set())
 for a in sub.get('platform_accounts',[]):ids|=byaccount.get(ak(a),set())
 if not ids:
  layers[1].append(sub);byid[sub['source_id']]=[sub];byname.setdefault(norm(sub['display_name']),set()).add(sub['source_id'])
  for a in sub.get('platform_accounts',[]):byaccount.setdefault(ak(a),set()).add(sub['source_id'])
 else:
  for sid in ids:
   for r in byid[sid]:
    r.update(reading=sub['reading'],reading_source=sub['reading_source'],reading_source_kind='manual')
    r['aliases']=list(dict.fromkeys(r.get('aliases',[])+[sub['display_name']]+sub.get('aliases',[])))
    r['platform_accounts']=list({ak(a):a for a in r.get('platform_accounts',[])+sub.get('platform_accounts',[])}.values())
merged={}
for r in sum(layers,[])+primary:
 old=merged.get(r['source_id'],{});merged[r['source_id']]={**old,**r,'aliases':list(dict.fromkeys(old.get('aliases',[])+r.get('aliases',[]))),'platform_accounts':old.get('platform_accounts',[])+r.get('platform_accounts',[])}
Path('/tmp/aiv-baseline.json').write_text(json.dumps(list(merged.values()),ensure_ascii=False))
print('Baseline identities',len(merged),'AI',sum(r.get('category')=='AIVTuber' for r in merged.values()))
