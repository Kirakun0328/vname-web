import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from aivtuber_sources import merge_aivtubers, youtube_id, collect

class AIVTests(unittest.TestCase):
    cid='UC'+'a'*22
    def entry(self, **kw):
        return dict({'id':'char-test','name':'AIテスト','name_kana':'えーあいてすと','description':'YouTubeで配信しています。','youtube_url':'https://youtube.com/channel/'+self.cid},**kw)
    def test_existing_channel_is_tagged_not_duplicated(self):
        base=[{'source_id':'youtube:'+self.cid,'display_name':'AIテスト','reading':''}]
        extra=merge_aivtubers(base,[],[self.entry()],{})
        self.assertEqual(len(extra),1)
        self.assertEqual(extra[0]['category'],'AIVTuber')
        self.assertNotIn('display_name',extra[0])
        self.assertEqual(extra[0]['reading'],'えーあいてすと')
        self.assertEqual(merge_aivtubers(base,extra,[self.entry()],{}),extra)
    def test_same_name_different_channels_are_not_merged(self):
        base=[{'source_id':'youtube:UC'+'b'*22,'display_name':'AIテスト'}]
        extra=merge_aivtubers(base,[],[self.entry()],{})
        self.assertEqual(extra[0]['source_id'],'youtube:'+self.cid)
        self.assertEqual(extra[0]['display_name'],'AIテスト')
    def test_existing_reading_and_different_character_are_not_overwritten(self):
        base=[{'source_id':'youtube:'+self.cid,'display_name':'AIテスト','reading':'てすと','reading_source':'https://example.com/','reading_source_kind':'official'}]
        extra=merge_aivtubers(base,[],[self.entry()],{})
        self.assertNotIn('reading',extra[0])
        extra=merge_aivtubers([{'source_id':'youtube:'+self.cid,'display_name':'別のキャラ'}],[],[self.entry()],{})
        self.assertNotIn('reading',extra[0])
    def test_bad_source_is_rejected(self):
        with self.assertRaises(ValueError):collect(lambda url:'{"success":false}')
        self.assertIsNone(youtube_id('https://youtube.com.evil.test/channel/'+self.cid))
        self.assertEqual(youtube_id(self.entry()['youtube_url']),self.cid)
