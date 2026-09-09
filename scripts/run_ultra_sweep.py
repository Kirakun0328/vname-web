"""Run a bounded search campaign with verified commits after every batch."""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'scripts/ultra-discovery-report.json'
OUTPUTS = ['extra-data.js', 'platform-data.js', 'scripts/searxng-candidates.json',
           'scripts/search-discovery-report.json', 'scripts/searxng-verification-report.json',
           'scripts/collection-report.json', 'scripts/ultra-discovery-report.json']


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def read_report(name):
    return json.loads((ROOT / 'scripts' / name).read_text(encoding='utf-8'))


def save(report, commit):
    report['updated_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    tmp = REPORT.with_suffix('.tmp')
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(REPORT)
    if commit:
        for filename in ('extra-data.js', 'platform-data.js'):
            run('node', '--check', filename)
        run('git', 'add', *OUTPUTS)
        diff = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT)
        if diff.returncode == 1:
            run('git', 'commit', '-m', 'Save verified SearXNG discovery batch')
            # Never force or automatically resolve competing dictionary changes.
            run('git', 'push', 'origin', 'HEAD:main')
        elif diff.returncode:
            raise RuntimeError('Could not inspect dictionary changes')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=1800)
    parser.add_argument('--pages', type=int, default=3)
    parser.add_argument('--batch', type=int, default=120)
    parser.add_argument('--seconds', type=int, default=7800)
    parser.add_argument('--commit', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.limit <= 6000 or not 1 <= args.pages <= 5 or not 1 <= args.batch <= 300:
        raise ValueError('Invalid campaign scale')
    import ultra_searxng_discovery as ultra
    target = min(args.limit, len(ultra.discovery.QUERIES))
    deadline = time.monotonic() + args.seconds
    report = {'run_id': os.environ.get('GITHUB_RUN_ID', 'local'), 'status': 'running',
              'requested_query_families': target, 'pages_per_query': args.pages,
              'query_families_attempted': 0, 'query_requests': 0,
              'new_candidates': 0, 'new_public_records': 0,
              'existing_records_enriched': 0, 'batches': [],
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    completed = 0
    while completed < target and time.monotonic() < deadline - 120:
        remaining = int(deadline - time.monotonic())
        limit = min(args.batch, target - completed)
        run(sys.executable, 'scripts/ultra_searxng_discovery.py', '--limit', str(limit),
            '--pages', str(args.pages), '--seconds', str(min(600, remaining - 90)))
        discovery = read_report('search-discovery-report.json')
        done = discovery.get('query_families_attempted', 0) if discovery.get('status') != 'not_configured' else 0
        completed += done
        report['query_families_attempted'] += done
        for key in ('query_requests', 'new_candidates'):
            report[key] += discovery.get(key, 0) if done else 0
        verification = {}
        if done and discovery.get('status') != 'source_unavailable':
            run(sys.executable, 'scripts/verify_searxng_candidates.py', '--limit', '750',
                '--workers', '3', '--seconds', str(max(30, min(360, int(deadline - time.monotonic()) - 60))))
            verification = read_report('searxng-verification-report.json')
            run(sys.executable, 'scripts/update_dictionary.py', '--reviewed-only')
            run(sys.executable, 'scripts/recount_dictionary.py')
        batch = {'number':len(report['batches']) + 1, 'search':discovery, 'verification':verification}
        report['batches'].append(batch)
        for key in ('new_public_records', 'existing_records_enriched'):
            report[key] += verification.get(key, 0)
        if discovery.get('status') in ('source_unavailable', 'not_configured') or not done:
            report['status'] = 'paused_search_unavailable'
        elif completed >= target:
            report['status'] = 'completed'
        save(report, args.commit)
        print(json.dumps({k:v for k,v in report.items() if k != 'batches'}, ensure_ascii=False), flush=True)
        if report['status'] != 'running':
            break
    if report['status'] == 'running':
        report['status'] = 'time_budget_reached'
        save(report, args.commit)
    print(json.dumps({k:v for k,v in report.items() if k != 'batches'}, ensure_ascii=False), flush=True)
    if report['status'] == 'paused_search_unavailable':
        raise SystemExit('SearXNG unavailable; partial results saved, no completed collection claimed.')


if __name__ == '__main__':
    main()
