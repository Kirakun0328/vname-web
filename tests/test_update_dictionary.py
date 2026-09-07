import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('updater', Path(__file__).parents[1] / 'scripts/update_dictionary.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)

class UpdateTests(unittest.TestCase):
    def dataset(self, *entries):
        return {'vtbs': [{'type': 'group'} for _ in range(5000)] + list(entries)}

    def test_aliases_preserve_reading_and_deduplicate_channel(self):
        base = [{'source_id': 'youtube:UC1', 'display_name': '兎田ぺこら', 'reading': 'うさだぺこら'}]
        v = {'type': 'vtuber', 'uuid': 'vdb-1', 'name': {'jp': '兎田ぺこら', 'en': 'Usada Pekora', 'extra': []}, 'accounts': [{'platform': 'youtube', 'type': 'official', 'id': 'UC1'}]}
        result = u.expand(base, [], self.dataset(v), [])
        self.assertEqual(result[0]['source_id'], 'youtube:UC1')
        self.assertEqual(result[0]['aliases'], ['Usada Pekora'])
        self.assertEqual(result[0]['romanized_source'], 'https://vdb.vtbs.moe/')
        self.assertEqual(base[0]['reading'], 'うさだぺこら')
        self.assertEqual(u.expand(base, result, self.dataset(v), []), result)

    def test_new_name_has_unknown_reading_and_old_records_survive(self):
        old = [{'source_id': 'userlocal:old', 'display_name': 'Old Name', 'reading': ''}]
        result = u.expand([], old, self.dataset(), [('new', 'New Name')])
        self.assertEqual(result[0], old[0])
        self.assertEqual(result[1]['reading'], '')
        self.assertEqual(u.expand([], result, self.dataset(), [('new', 'New Name')]), result)

    def test_partial_or_broken_source_is_rejected(self):
        with self.assertRaises(ValueError):
            u.expand([], [], {'vtbs': []}, [])
        with self.assertRaises(ValueError):
            u.parse_ranking('<html>Service unavailable</html>')

    def test_fetch_failure_leaves_file_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data.js').write_text('window.VTUBER_DATA = [];')
            path = root / 'extra-data.js'
            original = 'window.VTUBER_EXTRA = [];'
            path.write_text(original)
            with patch.object(u, 'ROOT', root), patch.object(u, 'fetch', side_effect=OSError('offline')), patch('sys.argv', ['updater']):
                with self.assertRaises(OSError):
                    u.main()
            self.assertEqual(path.read_text(), original)

if __name__ == '__main__':
    unittest.main()
