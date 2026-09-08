"""Large SearXNG candidate discovery for direct creator/platform profiles.

SearXNG is discovery only. Search titles/snippets are never publication evidence.
Candidates must be fetched and verified by verify_searxng_candidates.py before
any public record is created.
"""
import argparse
import datetime
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from platform_sources import canonical_account

ROOT = Path(__file__).resolve().parents[1]

SPECIALTIES = [
    # medicine / wellbeing
    '医療', '医師', '看護師', '薬剤師', '歯科', '栄養士', '心理学', 'カウンセラー', 'メンタルヘルス',
    # law / business / money
    '法律', '弁護士', '行政書士', '司法書士', '税理士', '会計士', 'FP', '経営', 'マーケティング', '起業',
    # school / scholarship
    '教育', '教師', '数学', '物理', '化学', '生物', '地理', '日本史', '世界史', '英語', '日本語', '古典',
    '研究者', '科学', '宇宙', '天文', '地学', '恐竜', '昆虫', '海洋', '気象',
    # technology / making
    'エンジニア', 'プログラミング', 'AI', '機械学習', 'データサイエンス', 'サイバーセキュリティ',
    'Linux', 'VR', 'XR', 'Unity', 'Unreal Engine', 'Blender', '3DCG', '電子工作', 'ロボット',
    # creative fields
    'イラスト', '漫画', 'アニメ', '小説', '作曲', 'DTM', 'ボカロ', '音楽', 'ピアノ', 'ギター', '声優',
    # culture / humanities
    '美術', '博物館', '学芸員', '考古学', '民俗学', '神話', '哲学', '文学', '言語学',
    # hobbies / industry
    '鉄道', '航空', '船', '車', 'バイク', '旅行', '温泉', 'キャンプ', '登山', '釣り', '料理', 'お酒',
    'コーヒー', '農業', '園芸', '競馬', '麻雀', '将棋', '囲碁', 'チェス', 'TRPG', 'ボードゲーム',
    # games / niche fandoms
    'レトロゲーム', '格ゲー', 'FPS', 'RTA', '音ゲー', 'カードゲーム', 'ポケモン', 'Minecraft',
    # multilingual / regional
    '英語学習', '中国語', '韓国語', 'スペイン語', 'フランス語', 'ドイツ語', '地方創生', 'ご当地',
    'indie', 'science', 'history', 'programming', 'cybersecurity', 'medical', 'law', 'education', 'railway',
]

BASE_QUERIES = [
    'site:youtube.com/@ "VTuber"',
    'site:youtube.com/@ "新人VTuber"',
    'site:youtube.com/@ "個人勢VTuber"',
    'site:youtube.com/@ "Vライバー"',
    'site:youtube.com/@ "バーチャルYouTuber"',
    'site:youtube.com/@ "indie vtuber"',
    'site:youtube.com/channel "VTuber"',
    'site:twitch.tv "VTuber"',
    'site:tiktok.com/@ "VTuber"',
    'site:web.iriam.app/s/user "IRIAM"',
    'site:web.iriam.app/s/user "Vライバー"',
    'site:reality.app/profile "REALITY"',
    'site:s.avvy.live/u "Avvy"',
    'site:showroom-live.com "VTuber"',
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

# YouTube-engine searches find specialist videos better than channel-page-only
# web queries. Each video is only a lead; the verifier resolves it to the
# uploader channel and confirms that channel directly.
QUERIES = BASE_QUERIES + [query for specialty in SPECIALTIES for query in (
    f'!yt "{specialty}" VTuber',
    f'site:youtube.com/@ "{specialty}" VTuber',
)]

VIDEO_RE = re.compile(r'^[\w-]{11}$')


def candidate_url(value):
    if not isinstance(value, str):
        return None
    try:
        u = urllib.parse.urlsplit(value)
    except ValueError:
        return None
    host = (u.hostname or '').lower().removeprefix('www.').removeprefix('m.')
    if u.scheme != 'https' or u.username or u.password:
        return None
    if host == 'youtube.com':
        path = urllib.parse.unquote(u.path).rstrip('/')
        if path == '/watch':
            video = urllib.parse.parse_qs(u.query).get('v', [''])[0]
            return 'https://www.youtube.com/watch?v=' + video if VIDEO_RE.fullmatch(video) else None
        match = re.fullmatch(r'/shorts/([\w-]{11})', path)
        if match:
            return 'https://www.youtube.com/shorts/' + match.group(1)
    account = canonical_account(value)
    if not account:
        return None
    # X/Instagram/Facebook are useful manual leads but weak unattended primary
    # verification targets because their public HTML is frequently unavailable.
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
    parser.add_argument('--limit', type=int, default=12, help='number of query families this run')
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
                request = urllib.request.Request(url, headers={'User-Agent': 'VName-primary-discovery/3.0'})
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
        query_catalog_size=len(QUERIES),
        specialty_count=len(SPECIALTIES),
        query_requests=searched,
        query_families_attempted=limit,
        pages_per_query=pages,
        new_candidates=new_count,
        total_candidates=len(queue),
        auto_published=0,
        scope='Search/video leads only; direct creator profile fetch and identity/activity confirmation required before publication.',
    )
    for path, data in ((queue_path, list(queue.values())), (report_path, report)):
        tmp = path.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        tmp.replace(path)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
