import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from encyclopedia_sources import pixiv_candidates


class EncyclopediaSourcesTest(unittest.TestCase):
    def test_bounded_facts_do_not_collect_prose_artists_or_related_names(self):
        text = '''- [広告](https://dic.pixiv.net/a/ad)
### 先駆者たち
- [活動者](https://dic.pixiv.net/a/creator)
  [絵](https://www.pixiv.net/artworks/123)by[作者](https://www.pixiv.net/users/456)
| 紹介本文 [友人](https://dic.pixiv.net/a/friend) |
- [公式\\_channelimage](https://youtube.com/@creator)
- [グループ](https://dic.pixiv.net/a/group)
- [所属者image](https://youtube.com/@member)
## 関連イラスト
- [無関係](https://dic.pixiv.net/a/unrelated)
'''
        rows = pixiv_candidates(text)
        self.assertEqual([r['name'] for r in rows], ['活動者', 'グループ'])
        self.assertEqual(rows[0]['links'], [{'label': '公式_channel', 'url': 'https://youtube.com/@creator'}])
        self.assertNotIn('intro', rows[0])
        self.assertNotIn('source_id', rows[1])  # Group is only a candidate.

    def test_unknown_layout_fails_closed(self):
        with self.assertRaises(ValueError):
            pixiv_candidates('- [活動者](https://dic.pixiv.net/a/creator)')


if __name__ == '__main__':
    unittest.main()
