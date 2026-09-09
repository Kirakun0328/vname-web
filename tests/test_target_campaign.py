import datetime
import json
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import campaign_queries
import discover_primary_search as discovery
import run_target_campaign as campaign
import verify_searxng_candidates as verifier


class TargetCampaignTests(unittest.TestCase):
    def test_agency_official_profiles_are_not_individual_creators(self):
        def document(description):
            return '<meta property="og:title" content="Example VTuber">' + \
                   '<meta name="description" content="' + description + '">' + \
                   '<script>{"externalId":"UC' + 'b' * 22 + '","videoRenderer":{}}</script>'
        with patch.object(verifier, 'fetch_page', return_value=document('VTuber事務所「例」の公式アカウントです。')):
            self.assertEqual(verifier.verify_one({'url':'https://youtube.com/@example'})[2], 'organization_channel')
        with patch.object(verifier, 'fetch_page', return_value=document('VTuber事務所「例」所属のVTuberです。配信しています。')):
            self.assertEqual(verifier.verify_one({'url':'https://youtube.com/@example'})[2], 'verified')

    def test_current_youtube_header_count_proves_activity_without_recommendation_counts(self):
        def document(count):
            metadata = {'contentMetadataViewModel': {'metadataRows': [
                {'metadataParts': [{'text': {'content': count}}]}]}}
            data = {'header': {'pageHeaderRenderer': {'content': {'pageHeaderViewModel': {'metadata': metadata}}}}}
            return '<script>var ytInitialData = ' + json.dumps(data) + ';</script>'
        for count in ('916 本の動画', '1,234 videos', '1 video'):
            self.assertEqual(verifier.activity_evidence(document(count), '', 'youtube'),
                             'public_channel_header_video_count')
        for count in ('0 videos', '0 本の動画', '1000 subscribers', 'I plan to upload 10 videos'):
            self.assertIsNone(verifier.activity_evidence(document(count), '', 'youtube'))
        self.assertIsNone(verifier.activity_evidence('<script>{"lockupViewModel":{"text":"916 videos"}}</script>', '', 'youtube'))

    def test_author_hints_prioritize_distinct_people_without_removing_namesakes(self):
        rows = [{'url': 'https://youtube.com/watch?v=' + str(i), 'candidate_author': author}
                for i, author in enumerate(['Alice', 'Alice', 'Bob', '', 'Alice', 'Carol'])]
        ordered = verifier.diverse_candidates(rows)
        self.assertEqual(ordered[:4], [rows[i] for i in (0, 2, 3, 5)])
        self.assertEqual({r['url'] for r in ordered}, {r['url'] for r in rows})

    def test_fan_art_and_clip_permissions_do_not_exclude_the_creator(self):
        self.assertFalse(verifier.fan_channel('Fantasy Alice - YouTube',
                         '個人勢VTuberです。ファンアート #AliceArt。切り抜きOK。配信しています。'))
        self.assertFalse(verifier.fan_channel('Alice VTuber',
                         'English VTuber. Fanart: #AliceArt. Clips welcome! My archive is on YouTube.'))
        for title, description in [('Alice Clips', 'VTuber'), ('VTuberまとめ', '配信しています'),
                                   ('Viewer', 'I make funny vtuber clips'),
                                   ('Viewer', '非公式チャンネル。VTuber切り抜きチャンネルです。')]:
            self.assertTrue(verifier.fan_channel(title, description))

    def test_multiple_videos_fetch_their_shared_channel_only_once(self):
        with patch.object(verifier, 'fetch_page', return_value='profile') as fetch:
            with verifier.profile_cache(), ThreadPoolExecutor(max_workers=6) as pool:
                results = list(pool.map(verifier.fetch_profile, ['https://youtube.com/@same'] * 12))
            self.assertEqual(results, ['profile'] * 12)
            fetch.assert_called_once()

    def test_multilingual_profiles_still_require_upload_evidence(self):
        for identity in ('個人勢VTuber', '虛擬實況主', '虚拟主播', '버튜버', 'VSinger', 'AI streamer'):
            profile = '<meta property="og:title" content="Example - YouTube">' \
                      '<meta name="description" content="' + identity + '">' \
                      '<script>{"externalId":"UC' + 'b' * 22 + '"}</script>'
            with patch.object(verifier, 'fetch_page', return_value=profile):
                self.assertEqual(verifier.verify_one({'url': 'https://youtube.com/@example'})[2], 'activity_unconfirmed')
            with patch.object(verifier, 'fetch_page', return_value=profile + '<script>{"videoRenderer":{}}</script>'):
                self.assertEqual(verifier.verify_one({'url': 'https://youtube.com/@example'})[2], 'verified')

    def test_catalogue_covers_languages_and_media_without_counting_them_as_people(self):
        queries = campaign_queries.QUERIES
        self.assertEqual(len(queries), len(set(queries)))
        self.assertGreater(len(queries), 10000)
        first = '\n'.join(queries[:240])
        for term in ('AIVTuber', 'IRIAM', 'reality.app', 'tiktok.com', 'twitch.tv', 'VTuber español', '버튜버'):
            self.assertIn(term.lower(), first.lower())

    def test_target_budget_deadline_and_no_growth_stop_the_campaign(self):
        config = {'enabled': True, 'target_records': 60000, 'query_budget': 60000, 'max_runs_without_growth': 3}
        today = datetime.datetime.now(datetime.timezone.utc)
        self.assertEqual(campaign.stopping_reason(config, {}, 60000, today), 'target_reached')
        self.assertIsNone(campaign.stopping_reason(config, {'new_candidates': 100000}, 18000, today))
        self.assertEqual(campaign.stopping_reason(config, {'query_families_attempted': 60000}, 18000, today), 'query_budget_reached')
        self.assertEqual(campaign.stopping_reason(config, {'consecutive_runs_without_growth': 3}, 18000, today), 'paused_no_growth')
        self.assertEqual(campaign.stopping_reason(config, {'deadline_at': today.isoformat()}, 18000, today), 'deadline_reached')

    def test_live_and_short_share_links_resolve_to_video_candidates(self):
        expected = 'https://www.youtube.com/watch?v=abcdefghijk'
        self.assertEqual(discovery.candidate_url('https://youtu.be/abcdefghijk?si=share'), expected)
        self.assertEqual(discovery.candidate_url('https://www.youtube.com/live/abcdefghijk?si=share'), expected)
        self.assertIsNone(discovery.candidate_url('https://youtu.be/bad'))

    def test_reaching_record_target_skips_further_search_and_saves_actual_totals(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / 'config.json'
            state_path = Path(directory) / 'state.json'
            config_path.write_text(json.dumps({'enabled': True, 'target_records': 60000,
                'query_budget': 60000, 'queries_per_batch': 240, 'pages': 3,
                'max_days': 14, 'max_runs_without_growth': 3}))
            with patch.object(campaign, 'CONFIG', config_path), patch.object(campaign, 'STATE', state_path), \
                 patch.object(campaign, 'listed_count', side_effect=[59999, 60000]), \
                 patch.object(campaign, 'verify', return_value={'new_public_records': 1}), \
                 patch.object(campaign, 'run') as command, patch.object(sys, 'argv', ['campaign']):
                campaign.main()
            command.assert_not_called()
            state = json.loads(state_path.read_text())
            self.assertEqual(state['status'], 'target_reached')
            self.assertEqual(state['current_listed_records'], 60000)
            self.assertEqual(state['new_public_records'], 1)
            self.assertEqual(state['query_families_attempted'], 0)


if __name__ == '__main__':
    unittest.main()
