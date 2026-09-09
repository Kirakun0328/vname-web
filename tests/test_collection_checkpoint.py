import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import collection_checkpoint as checkpoint


class CollectionCheckpointTests(unittest.TestCase):
    def test_concurrent_corrections_and_removals_survive_collection(self):
        base = [{'source_id': 'a', 'display_name': 'Old', 'aliases': ['removed']},
                {'source_id': 'removed', 'display_name': 'Removed'}]
        collected = [{'source_id': 'a', 'display_name': 'Scraped', 'aliases': ['removed', 'new'],
                      'activity_source': 'https://example.com/a'}, *base[1:],
                     {'source_id': 'b', 'display_name': 'Discovered'}]
        current = [{'source_id': 'a', 'display_name': 'Corrected', 'aliases': []},
                   {'source_id': 'c', 'display_name': 'Submitted'}]
        merged = {r['source_id']: r for r in checkpoint.merge_records(base, collected, current)}
        self.assertEqual(set(merged), {'a', 'b', 'c'})
        self.assertEqual(merged['a']['display_name'], 'Corrected')
        self.assertEqual(merged['a']['aliases'], ['new'])
        self.assertEqual(merged['a']['activity_source'], 'https://example.com/a')

    def test_publish_keeps_parallel_submission_page_edit_and_verified_addition(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            remote, collector, editor = [folder / n for n in ('remote.git', 'collector', 'editor')]
            def git(root, *args):
                return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
            git(folder, 'init', '--bare', '--initial-branch=main', str(remote))
            git(folder, 'clone', str(remote), str(collector))
            git(collector, 'config', 'user.name', 'Test')
            git(collector, 'config', 'user.email', 'test@example.com')
            (collector / 'scripts').mkdir()
            source = Path(__file__).resolve().parents[1] / 'scripts/recount_dictionary.py'
            shutil.copy(source, collector / 'scripts/recount_dictionary.py')
            def data(root, filename, variable, rows):
                (root / filename).write_text('window.' + variable + ' = ' + json.dumps(rows) + ';\n')
            data(collector, 'data.js', 'VTUBER_DATA', [])
            data(collector, 'platform-data.js', 'VTUBER_PLATFORMS', [])
            base = [{'source_id': 'a', 'display_name': 'Old'}]
            data(collector, 'extra-data.js', 'VTUBER_EXTRA', base)
            (collector / 'index.html').write_text('<title>Original</title><script src="extra-data.js?v=old"></script>')
            (collector / 'scripts/collection-report.json').write_text('{}')
            (collector / 'scripts/target-campaign-report.json').write_text('{"target_records":60000}')
            git(collector, 'add', '.')
            git(collector, 'commit', '-m', 'Initial')
            git(collector, 'push', 'origin', 'main')
            git(folder, 'clone', str(remote), str(editor))
            git(editor, 'config', 'user.name', 'Editor')
            git(editor, 'config', 'user.email', 'editor@example.com')
            data(editor, 'extra-data.js', 'VTUBER_EXTRA', [
                {'source_id': 'a', 'display_name': 'Corrected'}, {'source_id': 'c', 'display_name': 'Submitted'}])
            (editor / 'index.html').write_text('<title>New page</title><script src="extra-data.js?v=submission"></script>')
            git(editor, 'add', '.')
            git(editor, 'commit', '-m', 'User correction and submission')
            submitted = git(editor, 'rev-parse', 'HEAD')
            git(editor, 'push', 'origin', 'main')
            data(collector, 'extra-data.js', 'VTUBER_EXTRA', base + [{'source_id': 'b', 'display_name': 'Verified'}])
            checkpoint.refresh_asset_version(collector)
            git(collector, 'add', '.')
            git(collector, 'commit', '-m', 'Collection checkpoint')
            checkpoint.push_checkpoint(collector)
            rows = checkpoint.decode_data((collector / 'extra-data.js').read_text(), 'VTUBER_EXTRA')
            self.assertEqual({r['source_id']: r['display_name'] for r in rows},
                             {'a': 'Corrected', 'b': 'Verified', 'c': 'Submitted'})
            page = (collector / 'index.html').read_text()
            self.assertIn('<title>New page</title>', page)
            self.assertNotIn('?v=submission', page)
            self.assertEqual(json.loads((collector / 'scripts/collection-report.json').read_text())['records']['listed'], 3)
            git(collector, 'merge-base', '--is-ancestor', submitted, 'HEAD')
            self.assertEqual(git(remote, 'rev-parse', 'main'), git(collector, 'rev-parse', 'HEAD'))


if __name__ == '__main__':
    unittest.main()
