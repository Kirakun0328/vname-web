"""Source-linked audience counts for sorting; never invent popularity scores.

Only enrich existing identities via exact public activity accounts. These are
channel counts, not a cross-platform ranking or evidence of a character's debut.
"""
import datetime
from platform_sources import record_accounts


def merge_counts(base, previous, rows):
    combined = {r['source_id']: dict(r) for r in base}
    extra = {r['source_id']: dict(r) for r in previous}
    for r in previous: combined.setdefault(r['source_id'], {}).update(r)
    index = {}
    for sid, r in combined.items():
        for a in record_accounts(r): index.setdefault((a['platform'], a['id']), set()).add(sid)
    updated = set()
    for row in rows:
        if (row.get('platform') not in ('youtube', 'twitch') or type(row.get('count')) is not int
                or row['count'] < 0 or not row.get('source', '').startswith('https://')): continue
        for sid in index.get((row['platform'], row['account_id']), set()):
            old = combined[sid]
            metrics = {(m['platform'], m['account_id']): m for m in old.get('audience_metrics', [])}
            metrics[(row['platform'], row['account_id'])] = dict(row)
            extra.setdefault(sid, {'source_id': sid})['audience_metrics'] = list(metrics.values())
            old.update(extra[sid]); updated.add(sid)
    return list(extra.values()), len(updated)


def list_counts(items):
    from platform_sources import canonical_account
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    rows = []
    for item in items:
        for platform, count, url in [('youtube', item.get('youtubeSubscribers'), 'https://www.youtube.com/channel/'+str(item.get('youtubeChannelID') or '')),
                                     ('twitch', item.get('twitchFollowers'), item.get('twitchURL'))]:
            account = canonical_account(url)
            if account and type(count) is int and count >= 0:
                rows.append({'platform': platform, 'account_id': account['id'], 'count': count,
                             'source': 'https://aituberlist.net/', 'checked_at': today, 'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    return rows


def refresh(fetch, base, previous, report):
    from broad_sources import parse_post, POST_URL
    from vstats_sources import parse_directory, DIRECTORY
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    updated = previous
    for name, url, parse in [('vtuber_post', POST_URL, lambda s: parse_post(s, 0)[0]), ('vstats', DIRECTORY, parse_directory)]:
        try:
            rows = [{'platform': 'youtube', 'account_id': 'channel/'+r['channel_id'], 'count': r['subscribers'],
                     'source': r.get('source_url', url), 'checked_at': today, 'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat()} for r in parse(fetch(url))]
            updated, count = merge_counts(base, updated, rows)
            report.setdefault('audience_counts', {})[name] = {'source_records': len(rows), 'enriched_records': count, 'checked_at': today, 'status': 'ok'}
        except (OSError, ValueError, KeyError, TypeError) as error:
            report.setdefault('audience_counts', {})[name] = {'status': 'unavailable', 'error': type(error).__name__}
    return updated
