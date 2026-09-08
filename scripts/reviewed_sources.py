"""Keep individually reviewed, source-linked identities and explicit readings."""
import json
from pathlib import Path
from global_sources import valid_name


def reviewed_profiles():
    records=[]
    for name in ('reviewed-profiles.json', 'reviewed-community-profiles.json'):
        records.extend(json.loads(Path(__file__).with_name(name).read_text(encoding='utf-8')))
    return records


def merge_reviewed(previous,records=None,base=None):
    if records is None:
        records=reviewed_profiles()
    known={r['source_id']:dict(r) for r in (base or [])}
    for row in previous:
        known.setdefault(row['source_id'],{}).update(row)
    extra={r['source_id']:dict(r) for r in previous}
    seen=set()
    for row in records:
        sid=row.get('source_id','')
        if (not sid or sid in seen or not valid_name(row.get('display_name'))
                or not row.get('activity_source','').startswith('https://')):
            raise ValueError('Invalid reviewed profile')
        seen.add(sid)
        old=known.get(sid,{})
        aliases=list(dict.fromkeys([*old.get('aliases',[]),*row.get('aliases',[])]))
        # A reviewed rename keeps the same account ID. Preserve the former
        # display name for searches, without merging unrelated namesakes.
        if old.get('display_name') and old['display_name'] != row['display_name']:
            aliases=list(dict.fromkeys([*aliases,old['display_name']]))
        extra[sid]=dict(extra.get(sid,{}),**{k:v for k,v in row.items() if v or k not in ('reading','romanized_name') or not old.get(k)})
        if aliases:
            extra[sid]['aliases']=aliases
    # Character IDs are deliberate: two AI personas can share one broadcast.
    # Never infer that a host or another persona is an alias from the URL.
    return list(extra.values())
