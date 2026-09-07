import sys
import json
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from reading_sources import explicit_profile_reading, official_reading

class ReadingTests(unittest.TestCase):
    def profile(self, description, other=''):
        return '<a href="https://www.youtube.com/channel/UC123">YouTube</a><meta property="og:description" content="'+description+'">'+other
    def test_explicit_self_introduction(self):
        value=explicit_profile_reading(self.profile('「癒色えも（イシキ・エモ）」と申します✨'),'癒色えも','UC123')
        self.assertEqual(value,'いしきえも')
    def test_nickname_other_person_and_video_are_not_readings(self):
        for description in ['癒色えも（えもちゃん）','別の人（いしきえも）と申します','癒色えもです']:
            self.assertEqual(explicit_profile_reading(self.profile(description, '<p>癒色えも（ゆいろえも）です</p>'),'癒色えも','UC123'),'')
        self.assertEqual(explicit_profile_reading(self.profile('癒色えも（イシキ・エモ）と申します'),'癒色えも','UC999'),'')
    def test_conflicting_readings_rejected(self):
        text='癒色えも（イシキ・エモ）と申します。癒色えも（ゆいろえも）です'
        self.assertEqual(explicit_profile_reading(self.profile(text),'癒色えも','UC123'),'')
    def test_official_ruby_requires_identity(self):
        text='<script id="__NEXT_DATA__">'+json.dumps({'props':{'pageProps':{'liverDetail':{'name':'葛葉','ruby':'くずは','enName':'Kuzuha'}}}})+'</script>'
        self.assertEqual(official_reading(text,'葛葉'),('くずは','Kuzuha'))
        with self.assertRaises(ValueError):official_reading(text,'叶')
