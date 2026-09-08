"""Large SearXNG candidate discovery for direct creator/platform profiles.

SearXNG is discovery only. Search titles/snippets are never publication evidence.
Candidates must be fetched and verified by verify_searxng_candidates.py before
any public record is created.
"""
import argparse
import datetime
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from platform_sources import canonical_account

ROOT = Path(__file__).resolve().parents[1]

QUERIES = [
    'site:youtube.com/@ "VTuber"',
    'site:youtube.com/@ "新人VTuber"',
    'site:youtube.com/@ "個人勢VTuber"',
    'site:youtube.com/@ "Vライバー"',
    'site:youtube.com/@ "バーチャルYouTuber"',
    'site:youtube.com/@ "indie vtuber"',
    'site:youtube.com/@ "virtual youtuber"',
    'site:youtube.com/@ "EN VTuber"',
    'site:youtube.com/@ "VTuber español"',
    'site:youtube.com/@ "VTuber Indonesia"',
    'site:youtube.com/channel "VTuber"',
    'site:youtube.com/channel "virtual youtuber"',
    'site:twitch.tv "VTuber"',
    'site:twitch.tv "Vtuber streamer"',
    'site:twitch.tv "個人勢VTuber"',
    'site:tiktok.com/@ "VTuber"',
    'site:tiktok.com/@ "Vライバー"',
    'site:web.iriam.app/s/user "IRIAM"',
    'site:web.iriam.app/s/user "Vライバー"',
    'site:reality.app/profile "REALITY"',
    'site:reality.app/profile "Vライバー"',
    'site:s.avvy.live/u "Avvy"',
    'site:showroom-live.com "VTuber"',
    'site:showroom-live.com "Vライバー"',
    'site:17.live/profile "Vライバー"',
    'site:17.live/s/u "Vライバー"',
    'site:mirrativ.com/user "Vライバー"',
    'site:twitcasting.tv "VTuber"',
    'site:nicovideo.jp/user "VTuber"',
    'site:spooncast.net/profile "Vライバー"',
    'site:topia.tv/p "Vライバー"',
    'site:palmu.me/users "Vライバー"',
    'site:mixch.tv/u "Vライバー"',
    'site:pococha.com/app/users "Vライバー"',
    'site:whowatch.tv/profile "Vライバー"',
    'site:kick.com "VTuber"',
]


def candidate_url(value):
    account = canonical_account(value) if isinstance(value, str) else None
    if not account:
        return None
    # X/Instagram/Facebook are useful discovery leads but are poor automated
    # publication evidence because their public HTML is frequently unavailable.
    if account['platform'] in {'x', 'instagram', 'facebook', 'bilibili', 'acfun'}:
        return None
    return account['url']


def extract(results, query, stamp):
    output = []
    for result in results:
        if not isinstance(result, dict):
            continue
        url = candidate_url(result.get('url'))
        if not url:
            continue
        output.append({
            'url': url,
            'candidate_title': str(result.get('title', ''))[:240],
            'candidate_snippet': str(result.get('content', ''))[:500],
            'query': query,
            'discovered_at': stamp,
            'discovery_method': 'searxng',
            'review_status': 'pending_primary_confirmation',
            'published': False,
        })
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=8, help='number of query families this run')
    parser.add_argument('--pages', type=int, default=1, help='SearXNG pages per query, max 5')
    args = parser.parse_args()
    endpoint = os.environ.get('SEARXNG_URL', '').strip()
    report_path = ROOT / 'scripts/search-discovery-report.json'
    report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
    if not endpoint:
        report.update(status='not_configured', message='Set SEARXNG_URL to an authorized JSON-enabled instance. No search ran.')
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(report['message'])
        return
    u = urllib.parse.urlsplit(endpoint)
    if u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise ValueError('Use an instance base URL without embedded credentials or query parameters')
    if u.scheme == 'http' and u.hostname not in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('Remote instances must use HTTPS')

    queue_path = ROOT / 'scripts/searxng-candidates.json'
    previous = json.loads(queue_path.read_text(encoding='utf-8')) if queue_path.exists() else []
    queue = {r['url']: r for r in previous if isinstance(r, dict) and r.get('url')}
    cursor = report.get('next_query', 0) % len(QUERIES)
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    new_count = 0
    searched = 0
    status = 'ok'
    pages = max(1, min(args.pages, 5))
    limit = max(0, min(args.limit, len(QUERIES)))

    for offset in range(limit):
        idx = (cursor + offset) % len(QUERIES)
        query = QUERIES[idx]
        for pageno in range(1, pages + 1):
            url = endpoint.rstrip('/') + '/search?' + urllib.parse.urlencode({
                'q': query,
                'format': 'json',
                'pageno': pageno,
                'language': 'all',
                'safesearch': 0,
            })
            try:
                request = urllib.request.Request(url, headers={'User-Agent': 'VName-primary-discovery/2.0'})
                with urllib.request.urlopen(request, timeout=25) as response:
                    raw = response.read(3 * 1024 * 1024 + 1)
                if len(raw) > 3 * 1024 * 1024:
                    raise ValueError('Response too large')
                data = json.loads(raw)
                if not isinstance(data.get('results'), list):
                    raise ValueError('Invalid search response')
                searched += 1
                for row in extract(data['results'][:100], query, stamp):
                    if row['url'] not in queue:
                        queue[row['url']] = row
                        new_count += 1
                # Empty later pages usually mean there is nothing more to gain.
                if not data['results']:
                    break
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
                status = 'source_unavailable'
                report['error_type'] = type(error).__name__
                # Do not rotate instances or evade rate limits.
                break
        report['next_query'] = (idx + 1) % len(QUERIES)
        if status != 'ok':
            break

    report.update(
        status=status,
        updated_at=stamp,
        query_requests=searched,
        query_families_attempted=limit,
        pages_per_query=pages,
        new_candidates=new_count,
        total_candidates=len(queue),
        auto_published=0,
        scope='Search leads only; direct profile fetch and identity/activity confirmation required before publication.',
    )
    for path, data in ((queue_path, list(queue.values())), (report_path, report)):
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        tmp.replace(path)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
