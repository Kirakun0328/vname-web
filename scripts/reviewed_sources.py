"""Keep individually reviewed, source-linked identities and explicit readings."""
import json
from pathlib import Path
from global_sources import valid_name


def merge_reviewed(previous,records=None):
    if records is None:
        records=json.loads(Path(__file__).with_name('reviewed-profiles.json').read_text())
    extra={r['source_id']:dict(r) for r in previous}
    seen=set()
    for row in records:
        sid=row.get('source_id','')
        if (not sid or sid in seen or not valid_name(row.get('display_name'))
                or not row.get('activity_source','').startswith('https://')):
            raise ValueError('Invalid reviewed profile')
        seen.add(sid)
        old=extra.get(sid,{})
        aliases=list(dict.fromkeys([*old.get('aliases',[]),*row.get('aliases',[])]))
        extra[sid]=dict(old,**{k:v for k,v in row.items() if v or k not in ('reading','romanized_name') or not old.get(k)})
        if aliases:
            extra[sid]['aliases']=aliases
    # Character IDs are deliberate: two AI personas can share one broadcast.
    # Never infer that a host or another persona is an alias from the URL.
    return list(extra.values())
