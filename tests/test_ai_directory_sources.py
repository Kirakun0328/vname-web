import datetime
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from ai_directory_sources import parse_bundle, parse_list, parse_fc2, merge_ai
from channel_sources import youtube_profile


class AIDirectoryTests(unittest.TestCase):
    cid = 'UC' + 'a' * 22

    def listing(self, **kw):
        return dict({'name': 'AIテスト', 'description': 'AI VTuber', 'youtubeChannelID': self.cid, 'isUpcoming': False,
                     'latestVideoUrl': 'https://www.youtube.com/watch?v=' + 'a' * 11,
                     'latestVideoDate': '2026-01-01', 'imageUrl': 'https://example.com/portrait.png'}, **kw)

    def row(self, **kw):
        return dict(parse_list([self.listing()])[0][0], **kw)

    def test_json_literal_only_and_count_validation(self):
        payload = {'a': '2026-01-01', 'B': [self.listing(name="AI's test") for _ in range(100)]}
        bundle = 'var data=JSON.parse(' + repr(json.dumps(payload)) + ');'
        self.assertEqual(len(parse_bundle(bundle)), 100)
        with self.assertRaises(ValueError):
            parse_bundle('JSON.parse(loadFromSomewhere());')

    def test_no_images_or_description_imported(self):
        rows, _ = parse_list([self.listing(description='AI VTuber. A long creative biography')])
        self.assertFalse(any('image' in k or 'avatar' in k or k == 'description' for k in rows[0]))

    def test_upcoming_and_predebut_not_activity(self):
        upcoming = self.listing(isUpcoming=True, recentYoutubeVideos=[{'url': self.listing()['latestVideoUrl'], 'date': '2026-01-01'}])
        rows, _ = parse_list([upcoming, self.listing(name='新人VTuber準備中'), self.listing(latestVideoDate='2099-01-01')])
        self.assertEqual(rows, [])
        rows, _ = parse_list([self.listing(isUpcoming=True, recentYoutubeVideos=[{'url': 'https://www.youtube.com/watch?v=bbbbbbbbbbb', 'date': '2025-12-01'}])])
        self.assertEqual(len(rows), 1)

    def test_existing_match_and_idempotency(self):
        base = [{'source_id': 'youtube:' + self.cid, 'display_name': 'AIテスト'}]
        extra, counts = merge_ai(base, [], [self.row()])
        self.assertEqual(counts['new_records'], 0)
        self.assertEqual(extra[0]['category'], 'AIVTuber')
        again, _ = merge_ai(base, extra, [self.row()])
        self.assertEqual(again, extra)

    def test_same_name_different_channels_stays_separate(self):
        base = [{'source_id': 'youtube:UC' + 'b' * 22, 'display_name': 'AIテスト'}]
        extra, counts = merge_ai(base, [], [self.row()])
        self.assertEqual(counts['new_records'], 1)
        self.assertEqual(extra[0]['source_id'], 'youtube:' + self.cid)

    def test_mixed_channel_does_not_classify_human_host_as_ai(self):
        rows, _ = parse_list([self.listing(name='人間の声優', tags=['一部AITuber'])])
        extra, counts = merge_ai([], [], rows)
        self.assertEqual(extra, [])
        self.assertEqual(counts['mixed_or_unconfirmed_character'], 1)

    def test_two_personas_in_one_post_are_not_merged_with_host(self):
        base = [{'source_id': 'youtube:' + self.cid, 'display_name': '人間の開発者'}]
        chars = [self.row(source_id='reviewed:' + n, display_name=n, character_specific=True, source_url='https://x.com/kedamasuzume/status/123') for n in ('アルファ', 'ベータ')]
        extra, counts = merge_ai(base, [], chars)
        self.assertEqual(counts['new_records'], 2)
        self.assertEqual({r['display_name'] for r in extra}, {'アルファ', 'ベータ'})
        self.assertEqual(merge_ai(base, extra, chars)[0], extra)

    def test_fc2_requires_exact_roster_count(self):
        doc = '<p>1 チャンネル</p><div class="stream-row"><span style="flex:1;">AI &amp; Test</span><a href="https://www.youtube.com/channel/' + self.cid + '">YouTube</a></div>'
        self.assertEqual(parse_fc2(doc)[0]['name'], 'AI & Test')
        with self.assertRaises(ValueError):
            parse_fc2(doc.replace('1 チャンネル', '2 チャンネル'))

    def test_profile_uses_own_identity_and_header(self):
        data = {'metadata': {'channelMetadataRenderer': {'externalId': self.cid, 'title': 'AIテスト', 'channelUrl': 'https://www.youtube.com/channel/' + self.cid}},
                'header': {}, 'contents': {'recommendation': '400 videos'}}
        doc = 'var ytInitialData = ' + json.dumps(data) + ';'
        self.assertFalse(youtube_profile(doc, 'channel/' + self.cid)['published'])
        with self.assertRaises(ValueError):
            youtube_profile(doc, 'channel/UC' + 'b' * 22)
        data['header'] = {'text': '20 本の動画'}
        self.assertTrue(youtube_profile('var ytInitialData = ' + json.dumps(data, ensure_ascii=False), 'channel/' + self.cid)['published'])
