import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from deduplicate_sources import deduplicate

CID = 'UCSHXPmFvDM32bLm0OgHblsA'
def record(sid, name, **fields):
    return dict(source_id=sid, display_name=name, youtube_channel_id=CID,
                platform_accounts=[dict(platform='youtube', id='channel/'+CID,
                                        url='https://youtube.com/channel/'+CID)], **fields)

class DeduplicateTests(unittest.TestCase):
    def test_duplicate_keeps_identity_aliases_and_sources(self):
        a = record('aivnav:ima', '音紡いま', source_url='https://a.example/ima')
        b = record('aituberlist:ima', '音紡いま AI VTuber', source_url='https://b.example/ima')
        b['platform_accounts'].append(dict(platform='x', id='imaliveai', url='https://x.com/imaliveai'))
        result = deduplicate([], [a, b])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['display_name'], '音紡いま')
        self.assertIn(b['display_name'], result[0]['aliases'])
        self.assertEqual(len(result[0]['source_profiles']), 2)
        self.assertEqual(len(result[0]['platform_accounts']), 2)
        self.assertEqual(result, deduplicate([], result))
        self.assertNotIn('aliases', a)

    def test_shared_channels_and_same_names_are_not_enough(self):
        a = record('a', '音紡いま')
        for b in [record('b', '別のキャラ'), record('b', '音紡いま', character_specific=True),
                  dict(source_id='b', display_name='音紡いま', youtube_channel_id='UC'+'A'*22)]:
            self.assertEqual(len(deduplicate([], [a, b])), 2)

    def test_base_identity_wins(self):
        a = record('youtube:'+CID, '音紡いま')
        b = record('b', '音紡いま AI VTuber')
        result = deduplicate([a], [b])
        self.assertEqual([r['source_id'] for r in result], [a['source_id']])

if __name__ == '__main__':
    unittest.main()
