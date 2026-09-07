import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from broad_sources import parse_post, merge_post, preparing


class BroadSourceTests(unittest.TestCase):
    def entry(self, letter='a', **kwargs):
        return dict(channel_id='UC'+letter*22, display_name='小規模テスト', rank=1,
                    subscribers=12, views=30, **kwargs)

    def test_small_channels_and_identical_names_are_kept_separate(self):
        base = [{'source_id': 'youtube:UC'+'b'*22, 'display_name': '小規模テスト', 'reading': 'known', 'reading_source': 'https://official.example/'}]
        extra, counts = merge_post(base, [], [self.entry()], {})
        self.assertEqual(counts['new_records'], 1)
        self.assertEqual(counts['new_below_1000'], 1)
        self.assertEqual(extra[0]['reading'], '')
        self.assertEqual(merge_post(base, extra, [self.entry()], {})[0], extra)

    def test_same_channel_merges_with_vdb_and_preserves_reading(self):
        base = [{'source_id': 'vdb-1', 'display_name': '旧名', 'reading': 'きゅうめい', 'reading_source': 'https://official.example/'}]
        vdb = {'vtbs': [{'uuid': 'vdb-1', 'accounts': [{'platform': 'youtube', 'type': 'official', 'id': 'UC'+'a'*22}]}]}
        extra, counts = merge_post(base, [], [self.entry()], vdb)
        self.assertEqual(counts['new_records'], 0)
        self.assertEqual(extra[0]['source_id'], 'vdb-1')
        self.assertNotIn('reading', extra[0])
        self.assertIn('小規模テスト', extra[0]['aliases'])

    def test_predebut_and_zero_views_are_not_added(self):
        rows = [dict(self.entry(), display_name='テスト@VTuber準備中'), dict(self.entry('b'), views=0)]
        extra, counts = merge_post([], [], rows, {})
        self.assertEqual(extra, [])
        self.assertEqual(counts['skipped_without_activity_or_predebut'], 2)
        self.assertTrue(preparing('Test | pre-debut'))
        self.assertFalse(preparing('配信の機材準備中'))

    def test_wrong_page_and_malformed_html_fail_closed(self):
        for document in ('<html>Service unavailable</html>', '<p>1位</p><a onclick="FormSubmit(849)">last</a>'):
            with self.assertRaises(ValueError):
                parse_post(document, 800)

    def test_activity_confirmation_reenables_preparing_record(self):
        base = [{'source_id': 'youtube:UC'+'a'*22, 'display_name': 'テスト@VTuber準備中', 'listing_status': 'predebut'}]
        extra, _ = merge_post(base, [], [self.entry()], {})
        self.assertEqual(extra[0]['listing_status'], 'active')
        self.assertEqual(extra[0]['display_name'], '小規模テスト')


if __name__ == '__main__':
    unittest.main()
