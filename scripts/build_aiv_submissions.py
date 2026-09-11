"""Build reviewed AIV character overlays from owner-supplied rows; no network calls.

Run with --baseline JSON produced from the site's current dictionary layers.
Shared accounts alone never establish character identity. The TSV retains input
order so later explicitly supplied corrections override earlier readings.
"""
import argparse,collections,hashlib,json,re,unicodedata
from pathlib import Path
from urllib.parse import urlparse,unquote
ROOT=Path(__file__).resolve().parents[1]
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',str(s or '')).casefold() if c.isalnum())
def urlkey(s):
 try:
  u=urlparse(s);h=u.netloc.lower().removeprefix('www.');p=unquote(u.path).rstrip('/');h='x.com' if h=='twitter.com' else h
  if h in ['youtube.com','twitch.tv','tiktok.com','kick.com','x.com']:p=p.casefold()
  if h=='whowatch.tv':p=p.removeprefix('/sp')
  return h+p
 except ValueError:return ''
def urls(r):
 out=[r.get(k,'') for k in ('source_url','youtube_url','twitch_url','twitter_url','official_website','account_source')]
 out += [a.get('url','') for a in r.get('platform_accounts',[])]+r.get('source_profiles',[])
 if r.get('youtube_handle'):out.append('https://www.youtube.com/'+r['youtube_handle'])
 if r.get('youtube_channel_id'):out.append('https://www.youtube.com/channel/'+r['youtube_channel_id'])
 if r.get('twitch_login'):out.append('https://www.twitch.tv/'+r['twitch_login'])
 return [u for u in out if u.startswith('https://')]
def profile(u):
 k=urlkey(u)
 return bool(re.match(r'(youtube\.com/(?:@|channel/)|twitch\.tv/|tiktok\.com/@|kick\.com/|x\.com/[^/]+$|whowatch\.tv/(?:sp/)?profile/)',k))
def expand(s):
 prefixes={'y:':'https://www.youtube.com/@','c:':'https://www.youtube.com/channel/','w:':'https://www.twitch.tv/','x:':'https://x.com/','t:':'https://www.tiktok.com/@','k:':'https://kick.com/'}
 return prefixes.get(s[:2],'')+s[2:] if s[:2] in prefixes else s
INTRO={name:'https://x.com/kedamasuzume/status/'+post for name,post in [
 ('Maiko','2098162095934357754'),('Eilonwy','2097799710035886134'),('LUMA','2097437321616593194'),('ライちゃん','2097074932559581413'),('中国うさぎ','2096712545155641428'),('Anami','2096350156224639274'),('リリカ','2095987770552627375'),('ルゼブル','2095987770552627375'),('Aka','2095625383085260804'),('銀河盤子','2095262992866611701'),('TAERUちゃん','2094900604758045157'),('AITuberコハク','2033295926115135736')]}
ALIASES={'Eilonwy':['てふてふ Eilonwy'],'AITuberコハク（猫音コハク）':['猫音コハク','AITuberコハク'],'Нейрона（ニューロン）':['Нейрона','ニューロン'],'Luna（Lunar Fox）':['Luna','Lunar Fox'],'Felix（F-3L1X）':['Felix','F-3L1X'],'波音（旧：朱音）':['波音','朱音'],'らんらん（RAN-073）':['らんらん','RAN-073'],'N（エヌ）':['N','エヌ'],'SAL9000／さりー':['SAL9000','さりー']}
MERGE_LATEST={'夢眠メア','音成みらね','GEMu','Stella Voyd','シロ','くらら'}
def read_submissions():
 rows=[]
 for line_no,line in enumerate((ROOT/'scripts/aiv-submissions-20260911.tsv').read_text().splitlines(),1):
  if not line.strip():continue
  name,reading,raw=line.split('\t');us=[expand(x) for x in raw.split()]
  ns=name.split('／');rs=reading.split('／')
  if len(ns)!=len(rs):ns=[name];rs=[reading]
  for n,r in zip(ns,rs):
   aliases=ALIASES.get(n,[])[:]
   old=None
   # Explicit follow-up shorthand for the same channel character.
   if n=='ヒナキ':old=next(x for x in rows if x['display_name']=='ヒナキ・オーロラマウンテン');aliases=['ヒナキ']
   elif n=='Lumi Mage':old=next(x for x in rows if x['display_name']=='Lumi' and any('darkmage4vt' in u for u in x['urls']));aliases=['Lumi']
   if old is None:
    candidates=[x for x in rows if norm(x['display_name'])==norm(n)]
    old=next((x for x in candidates if set(map(urlkey,x['urls']))&set(map(urlkey,us))),None)
    if old is None and n in MERGE_LATEST and len(candidates)==1:old=candidates[0]
   if old:
    old['urls']=list(dict.fromkeys(old['urls']+us));old['aliases']=list(dict.fromkeys(old['aliases']+aliases));old['input_lines'].append(line_no)
    if n=='Lumi Mage':old['display_name']=n
    if n!='ヒナキ':old['reading']=r
   else:rows.append(dict(display_name=n,reading=r,urls=us,aliases=aliases,input_lines=[line_no]))
 # Follow-up identifies channel labels as AI Zundamon, not different characters.
 for z in json.loads((ROOT/'scripts/zundamon-channels-20260911.json').read_text())['entries']:
  ks=set(map(urlkey,z['urls']))
  old=next((r for r in rows if ks & set(map(urlkey,r['urls'])) and r['display_name'] in ['すえ','ずんだもん','AIずんだもん']),None)
  if old is None:
   old=dict(display_name='AIずんだもん',reading='えーあいずんだもん',urls=[],aliases=[],input_lines=[]);rows.append(old)
  old['aliases']=list(dict.fromkeys(old['aliases']+[old['display_name']]+z['aliases']))
  old.update(display_name='AIずんだもん',reading='えーあいずんだもん',zundamon=z)
  old['urls']=list(dict.fromkeys(z['urls']+old['urls']))
 for r in rows:
  if r['display_name'] in ['AIずんだもん（リアルタイプ）','ずんだもんAI']:
   r['aliases']=list(dict.fromkeys(r['aliases']+['AIずんだもん','ずんだもん','えーあいずんだもん']))
 return rows

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);args=ap.parse_args()
 baseline=json.loads(Path(args.baseline).read_text());submissions=read_submissions()
 # Known channel/handle correspondences come from existing resolved sources.
 equivalences=collections.defaultdict(set)
 for r in baseline:
  cid=r.get('youtube_channel_id')
  if not cid and r['source_id'].startswith('youtube:UC'):cid=r['source_id'][8:]
  if cid:
   for u in urls(r):
    if urlkey(u).startswith('youtube.com/@'):equivalences[urlkey(u)].add('youtube.com/channel/'+cid.casefold())
 cache=json.loads((ROOT/'scripts/aivnav_channels.json').read_text())
 for v in cache.values():
  if v.get('channel_id') and v.get('youtube_url'):equivalences[urlkey(v['youtube_url'])].add('youtube.com/channel/'+v['channel_id'].casefold())
 def keys(us):
  k={urlkey(u) for u in us if profile(u)}
  for u in list(k):
   if len(equivalences[u])==1:k|=equivalences[u]
  return k
 bkeys={r['source_id']:keys(urls(r)) for r in baseline}
 skeys=[keys(r['urls']) for r in submissions]
 byname=collections.defaultdict(list);byurl=collections.defaultdict(list)
 for r in baseline:
  for n in set(map(norm,[r.get('display_name','')]+r.get('aliases',[]))):
   if n:byname[n].append(r)
  for u in bkeys[r['source_id']]:byurl[u].append(r)
 counts=collections.Counter(norm(r['display_name']) for r in submissions)
 selected=[];used=set();review=[];suppress=set();composites={}
 overrides=json.loads((ROOT/'scripts/aiv-submission-identities-20260911.json').read_text())
 bmap={r['source_id']:r for r in baseline}
 # Only supersede explicit AI multi-character rows covered by this submission.
 for r in baseline:
  if r.get('category')!='AIVTuber' or not re.search(r'[/／＆&・と]',r.get('display_name','')):continue
  children=[i for i,s in enumerate(submissions) if skeys[i]&bkeys[r['source_id']] and norm(s['display_name']) in norm(r.get('display_name',''))]
  if len(children)>1 and all(norm(submissions[i]['display_name'])!=norm(r.get('display_name','')) for i in children):composites[r['source_id']]=children
 composites['aivnav:char-V7PMYmchCfX4']=[i for i,s in enumerate(submissions) if s['display_name'] in ['真流賀レイテ','ハンナ・アクタヴィア']]
 for i,s in enumerate(submissions):
  ns=set(map(norm,[s['display_name']]+s['aliases']));account_candidates={r['source_id']:r for k in skeys[i] for r in byurl[k]}
  named={r['source_id']:r for n in ns for r in byname[n]}
  exact=[r for sid,r in named.items() if sid not in composites and bkeys[sid]&skeys[i]]
  # Some older AI records have only a directory page and no resolved account.
  if not exact and counts[norm(s['display_name'])]==1:
   exact=[r for r in named.values() if r.get('category')=='AIVTuber' and not bkeys[r['source_id']] and r['source_id'] not in composites]
  if not exact:
   exact=[r for sid,r in account_candidates.items() if sid not in composites and r.get('category')=='AIVTuber' and len(norm(s['display_name']))>=4 and norm(s['display_name']) in norm(r.get('display_name',''))]
  if s['display_name'] in overrides:exact=[bmap[overrides[s['display_name']]]]
  if s.get('zundamon',{}).get('existing_id'):exact=[bmap[s['zundamon']['existing_id']]]
  if s['display_name']=='Luna' and any('lunaxoniichan' in u.lower() for u in s['urls']):exact=[bmap['youtube:UCJ2Lj2HePDIKNJLtB3E8L9Q']]
  if s['display_name']=='東北きりたん' and any('/@aituberkiritan' in u for u in s['urls']):exact=[bmap['aivnav:char-xDOTP-Yd5IDR']]
  exact=[r for r in exact if r['source_id'] not in used]
  exact.sort(key=lambda r:(r.get('category')!='AIVTuber',norm(r.get('display_name'))!=norm(s['display_name']),r['source_id']))
  old=exact[0] if exact else None
  if old:
   sid=old['source_id'];used.add(sid)
   # Multiple established AI records for the exact same name+account are duplicate identities.
   for other in exact[1:]:
    if other.get('category')=='AIVTuber' and norm(other.get('display_name'))==norm(old.get('display_name')):suppress.add(other['source_id'])
  else:sid='ai-character:'+hashlib.sha256((urlkey(s['urls'][0])+'\n'+s['display_name']).encode()).hexdigest()[:24]
  accounts=[]
  for u in s['urls']:
   if not profile(u):continue
   k=urlkey(u);h,path=k.split('/',1);p={'youtube.com':'youtube','twitch.tv':'twitch','tiktok.com':'tiktok','x.com':'x','kick.com':'kick','whowatch.tv':'whowatch'}.get(h)
   if p:accounts.append(dict(platform=p,id=path,url=u))
  source=next((u for u in s['urls'] if 'kedamasuzume/status/' not in u),s['urls'][0])
  row=dict(source_id=sid,display_name=s['display_name'],reading=s['reading'],reading_source='owner_submission:2026-09-11',reading_source_kind='manual',category='AIVTuber',category_source='owner_submission:2026-09-11',character_specific=True,aliases=s['aliases'],source_url=source,name_source=source,activity_source=(old or {}).get('activity_source',source),activity_evidence=(old or {}).get('activity_evidence','owner_submitted_ai_character'),platform_accounts=accounts,source_profiles=s['urls'],submitted_at='2026-09-11',listing_status='user_approved')
  intro=INTRO.get(s['display_name'])
  if s.get('zundamon'):
   z=s['zundamon'];row.update(youtube_channel_id=z['channel_id'],youtube_url='https://www.youtube.com/channel/'+z['channel_id'],channel_title=z['channel_title'])
   if z.get('handle'):row['youtube_handle']='@'+z['handle']
   if z['evidence'].startswith('https://'):row.update(activity_source=z['evidence'],activity_evidence='youtube_ai_character_description',category_source=z['evidence'])
  if intro:row['introduction_source']=intro
  if old:
   siblings={norm(x['display_name']) for j,x in enumerate(submissions) if j!=i and skeys[i]&skeys[j]}
   row['aliases']=list(dict.fromkeys([a for a in old.get('aliases',[]) if not any(n==norm(a) or (len(n)>=3 and n in norm(a)) for n in siblings)]+row['aliases']))
   if old.get('display_name')!=row['display_name'] and not any(len(n)>=3 and n in norm(old.get('display_name')) for n in siblings):row['aliases'].append(old['display_name'])
  if s['display_name']=='夢眠メア':row.update(debut_date='2026-03-03',debut_source='https://prtimes.jp/main/html/rd/p/000000215.000046857.html',activity_source='https://youtube.com/live/Ec99IyA2QS0',activity_evidence='official_debut_release')
  selected.append(row)
  review.append(dict(name=s['display_name'],id=sid,action='update' if old else 'add',input_lines=s['input_lines'],account_candidates=[dict(id=r['source_id'],name=r.get('display_name'),category=r.get('category')) for r in account_candidates.values()] if not old else []))
 for sid,children in composites.items():
  if all(selected[i]['source_id']!=sid for i in children):suppress.add(sid)
 suppress-=set(r['source_id'] for r in selected)
 report=dict(input_rows=len((ROOT/'scripts/aiv-submissions-20260911.tsv').read_text().splitlines()),characters=len(selected),added=sum(r['action']=='add' for r in review),updated=sum(r['action']=='update' for r in review),superseded_ids=sorted(suppress),records=review)
 (ROOT/'scripts/aiv-submissions-review-20260911.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 payload=json.dumps(dict(records=selected,superseded_ids=sorted(suppress)),ensure_ascii=False,separators=(',',':'))
 template=(ROOT/'scripts/aiv-submissions-runtime.js').read_text()
 (ROOT/'aiv-submissions-20260911.js').write_text('// Owner-submitted AIV characters; generated by scripts/build_aiv_submissions.py.\n'+template.replace('/* PAYLOAD */',payload))
 print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False))
if __name__=='__main__':main()
