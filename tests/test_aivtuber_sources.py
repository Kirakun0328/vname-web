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
        self.assertEqual(extra[0]['source_id'],'aivnav:char-test')
        self.assertEqual(extra[0]['display_name'],'AIテスト')
        self.assertEqual(extra[0]['youtube_channel_id'],self.cid)
    def test_unresolved_handle_is_still_linked_to_its_character(self):
        extra=merge_aivtubers([],[],[self.entry(youtube_url='https://www.youtube.com/@%E3%81%97%E3%81%9A%E3%81%8F')],{})
        self.assertEqual(extra[0]['source_id'],'aivnav:char-test')
        self.assertEqual(extra[0]['platform_accounts'][0]['id'],'@しずく')
        self.assertNotIn('youtube_channel_id',extra[0])
    def test_verified_channel_reconciles_only_same_character_stub(self):
        base=[{'source_id':'youtube:'+self.cid,'display_name':'しずく'},
              {'source_id':'youtube:UC'+'b'*22,'display_name':'しずく'}]
        stub={'source_id':'aivnav:char-test','display_name':'しずく / Shizuku','aivnav_ids':['char-test'],'category':'AIVTuber'}
        char=self.entry(name='しずく / Shizuku',name_kana='')
        extra=merge_aivtubers(base+[stub],[stub],[char],{})
        self.assertEqual(len(extra),1)
        self.assertEqual(extra[0]['source_id'],'youtube:'+self.cid)
        self.assertEqual(extra[0]['category'],'AIVTuber')
        self.assertIn('Shizuku',extra[0]['aliases'])
        self.assertEqual(merge_aivtubers(base,extra,[char],{}),extra)
    def test_shared_channel_does_not_combine_ai_personas(self):
        chars=[self.entry(id='char-one',name='アルファ'),self.entry(id='char-two',name='ベータ')]
        extra=merge_aivtubers([],[],chars,{})
        self.assertEqual(len(extra),2)
        self.assertEqual({r['display_name'] for r in extra},{'アルファ','ベータ'})
        self.assertTrue(all(len(r['aivnav_ids'])==1 for r in extra))
    def test_bad_source_is_rejected(self):
        with self.assertRaises(ValueError):collect(lambda url:'{"success":false}')
        self.assertIsNone(youtube_id('https://youtube.com.evil.test/channel/'+self.cid))
        self.assertEqual(youtube_id(self.entry()['youtube_url']),self.cid)
