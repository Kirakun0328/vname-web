"""Checkpoint a finite primary-source collection campaign toward a record target."""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'scripts/collection-goal.json'
STATE = ROOT / 'scripts/target-campaign-report.json'
OUTPUTS = ['extra-data.js', 'platform-data.js', 'scripts/searxng-candidates.json',
           'scripts/search-discovery-report.json', 'scripts/searxng-verification-report.json',
           'scripts/collection-report.json', 'scripts/target-campaign-report.json',
           'scripts/profile-fetch-backoff.json', 'index.html']
TERMINAL = {'target_reached', 'query_budget_reached', 'deadline_reached',
            'paused_no_growth', 'paused_search_unavailable', 'disabled'}


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def listed_count():
    from recount_dictionary import read_js, preparing
    merged = {}
    for filename, variable in [('data.js', 'VTUBER_DATA'), ('extra-data.js', 'VTUBER_EXTRA'),
                               ('platform-data.js', 'VTUBER_PLATFORMS')]:
        for row in read_js(ROOT / filename, variable):
            merged.setdefault(row['source_id'], {}).update(row)
    return sum(bool(row.get('display_name')) and row.get('listing_status') != 'predebut'
               and not preparing(row.get('display_name')) for row in merged.values())


def stopping_reason(config, state, current_count, timestamp):
    if not config.get('enabled'):
        return 'disabled'
    if current_count >= config['target_records']:
        return 'target_reached'
    if state.get('status') in TERMINAL - {'query_budget_reached'}:
        return state['status']
    if state.get('query_families_attempted', 0) >= config['query_budget']:
        return 'query_budget_reached'
    if state.get('deadline_at') and timestamp >= datetime.datetime.fromisoformat(state['deadline_at']):
        return 'deadline_reached'
    if state.get('consecutive_runs_without_growth', 0) >= config['max_runs_without_growth']:
        return 'paused_no_growth'
    return None


def save(state, commit):
    state['updated_at'] = now().isoformat()
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(STATE)
    if not commit:
        return
    from collection_checkpoint import refresh_asset_version, push_checkpoint
    refresh_asset_version()
    for filename in ('extra-data.js', 'platform-data.js'):
        run('node', '--check', filename)
    run('git', 'add', *OUTPUTS)
    diff = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT)
    if diff.returncode == 1:
        run('git', 'commit', '-m', 'Save verified progress toward 60000 records')
        push_checkpoint()
        # Publication may also have incorporated independently submitted names.
        state.update(read_json(STATE))
    elif diff.returncode:
        raise RuntimeError('Could not inspect campaign changes')


def verify(seconds, limit=3000):
    run(sys.executable, 'scripts/verify_searxng_candidates.py', '--limit', str(limit),
        '--workers', '6', '--seconds', str(seconds), '--recheck-classification')
    result = read_json(ROOT / 'scripts/searxng-verification-report.json')
    run(sys.executable, 'scripts/update_dictionary.py', '--reviewed-only')
    run(sys.executable, 'scripts/recount_dictionary.py')
    return result


def record_batch(state, search, verification, current_count):
    for key in ('query_families_attempted', 'query_requests', 'new_candidates'):
        state[key] += search.get(key, 0)
    for key in ('new_public_records', 'existing_records_enriched'):
        state[key] += verification.get(key, 0)
    state['current_listed_records'] = current_count
    state['remaining_to_target'] = max(0, state['target_records'] - current_count)
    state['batches_completed'] += 1
    state['last_batch'] = {
        'at': now().isoformat(), 'query_families_attempted': search.get('query_families_attempted', 0),
        'new_candidates': search.get('new_candidates', 0),
        'profiles_checked': verification.get('attempted_this_run', 0),
        'new_public_records': verification.get('new_public_records', 0),
        'verification_statuses': verification.get('statuses', {}),
        'deferred_host_backoff': verification.get('deferred_host_backoff', 0),
        'queue_statuses': verification.get('queue_statuses', {}),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=int, default=5400)
    parser.add_argument('--commit', action='store_true')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    config = read_json(CONFIG)
    if not 1 <= config['target_records'] <= 100000 or not 1 <= config['query_budget'] <= 100000:
        raise ValueError('Invalid campaign limits')
    if not 1 <= config['queries_per_batch'] <= 1000 or not 1 <= config['pages'] <= 5:
        raise ValueError('Invalid search batch limits')
    search_seconds = config.get('search_seconds_per_batch', 420)
    verification_seconds = config.get('verification_seconds_per_batch', 600)
    if not 30 <= search_seconds <= 1200:
        raise ValueError('Invalid search time budget')
    if not 30 <= verification_seconds <= 1200:
        raise ValueError('Invalid verification time budget')
    from campaign_queries import QUERIES
    # Traverse this catalogue once; exhausted searches are never reported as
    # successful completion of the independent 60000-record target.
    config['query_budget'] = min(config['query_budget'], len(QUERIES))
    current = listed_count()
    state = read_json(STATE) if STATE.exists() else {}
    reason = stopping_reason(config, state, current, now())
    if args.check_only:
        print(json.dumps({'run': reason is None, 'reason': reason, 'listed': current}))
        if os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
                output.write('run=' + ('true' if reason is None else 'false') + '\n')
        return
    if reason:
        unchanged = state.get('status') == reason and state.get('current_listed_records') == current
        state.update(status=reason, current_listed_records=current,
                     target_records=config['target_records'], remaining_to_target=max(0, config['target_records'] - current))
        if not unchanged:
            save(state, args.commit)
        print(json.dumps(state, ensure_ascii=False))
        return
    if not state:
        state = {
            'schema': 1, 'target_records': config['target_records'],
            'query_catalogue_size': len(QUERIES), 'query_budget': config['query_budget'],
            'starting_listed_records': current, 'current_listed_records': current,
            'remaining_to_target': max(0, config['target_records'] - current),
            'started_at': now().isoformat(),
            'deadline_at': (now() + datetime.timedelta(days=config['max_days'])).isoformat(),
            'query_families_attempted': 0, 'query_requests': 0, 'new_candidates': 0,
            'new_public_records': 0, 'existing_records_enriched': 0,
            'runs_completed': 0, 'batches_completed': 0, 'consecutive_runs_without_growth': 0,
            'policy': 'Count unique published records; every discovered identity requires direct creator evidence. Explicit owner-approved submissions remain separate.',
        }
    state.update(status='running', run_id=os.environ.get('GITHUB_RUN_ID', 'local'),
                 query_catalogue_size=len(QUERIES), query_budget=config['query_budget'],
                 pages_per_query=config['pages'], queries_per_batch=config['queries_per_batch'],
                 search_seconds_per_batch=search_seconds,
                 verification_seconds_per_batch=verification_seconds)
    save(state, args.commit)
    deadline = time.monotonic() + max(120, min(args.seconds, 5400))
    start_count = current
    # The first launch recovers old false exclusions. Resumed executions start
    # searching immediately and verify their queue after each search batch.
    if state['batches_completed'] == 0:
        verification = verify(min(120, max(30, int(deadline - time.monotonic()) - 60)), limit=250)
        current = listed_count()
        record_batch(state, {}, verification, current)
        save(state, args.commit)
    while time.monotonic() < deadline - 180:
        reason = stopping_reason(config, state, current, now())
        if reason:
            state['status'] = reason
            break
        limit = min(config['queries_per_batch'], config['query_budget'] - state['query_families_attempted'])
        run(sys.executable, 'scripts/campaign_queries.py', '--limit', str(limit),
            '--pages', str(config['pages']), '--seconds',
            str(min(search_seconds, max(30, int(deadline - time.monotonic()) - 150))))
        search = read_json(ROOT / 'scripts/search-discovery-report.json')
        if search.get('status') in ('source_unavailable', 'not_configured'):
            state['status'] = 'paused_search_unavailable'
            record_batch(state, search, {}, current)
            save(state, args.commit)
            break
        verification = verify(max(30, min(verification_seconds, int(deadline - time.monotonic()) - 60)))
        current = listed_count()
        record_batch(state, search, verification, current)
        save(state, args.commit)
        print(json.dumps(state, ensure_ascii=False), flush=True)
    state['runs_completed'] += 1
    state['consecutive_runs_without_growth'] = (state['consecutive_runs_without_growth'] + 1 if current <= start_count else 0)
    state['status'] = stopping_reason(config, state, current, now()) or 'waiting_next_run'
    save(state, args.commit)
    print(json.dumps(state, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
