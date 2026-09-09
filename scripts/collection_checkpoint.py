"""Publish collection checkpoints while preserving concurrent site edits."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MISSING = object()
DATA = {'extra-data.js': 'VTUBER_EXTRA', 'platform-data.js': 'VTUBER_PLATFORMS'}


def merge_value(base, collected, current):
    """Apply collection changes; a concurrent explicit correction takes priority."""
    if collected == base or collected == current:
        return current
    if current == base:
        return collected
    if all(isinstance(v, dict) for v in (base, collected, current)):
        result = {}
        for key in dict.fromkeys([*current, *collected]):
            value = merge_value(base.get(key, MISSING), collected.get(key, MISSING),
                                current.get(key, MISSING))
            if value is not MISSING:
                result[key] = value
        return result
    if all(isinstance(v, list) for v in (base, collected, current)):
        # Preserve current removals, retaining only genuinely new collected items.
        return current + [v for v in collected if v not in base and v not in current]
    return current


def merge_records(base, collected, current):
    indexes = [{r['source_id']: r for r in rows} for rows in (base, collected, current)]
    if any(len(index) != len(rows) for index, rows in zip(indexes, (base, collected, current))):
        raise ValueError('Duplicate source IDs in collection checkpoint')
    return list(merge_value(*indexes).values())


def refresh_asset_version(root=ROOT):
    path = root / 'index.html'
    if not path.exists():
        return
    version = hashlib.sha256((root / 'extra-data.js').read_bytes()).hexdigest()[:16]
    content = re.sub(r'(src=[\"\']extra-data\.js)(?:\?[^\"\']*)?([\"\'])',
                     lambda m: m[1] + '?v=' + version + m[2], path.read_text())
    path.write_text(content)


def git(*args, root=ROOT, check=True):
    return subprocess.run(['git', *args], cwd=root, check=check, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def decode_data(text, variable):
    match = re.search(r'window\.' + variable + r'\s*=\s*(\[.*\])\s*;?\s*$', text, re.S)
    if not match:
        raise ValueError('Invalid checkpoint data')
    return json.loads(match[1])


def push_checkpoint(root=ROOT):
    for attempt in range(3):
        git('fetch', 'origin', 'main', root=root)
        remote = git('rev-parse', 'FETCH_HEAD', root=root).stdout.strip()
        if git('merge-base', '--is-ancestor', remote, 'HEAD', root=root, check=False).returncode:
            merged = git('merge', '--no-commit', '--no-ff', remote, root=root, check=False)
            conflicts = git('diff', '--name-only', '--diff-filter=U', root=root).stdout.splitlines()
            safe = set(DATA) | {'index.html', 'scripts/collection-report.json'}
            try:
                if merged.returncode and not conflicts:
                    raise RuntimeError(merged.stderr)
                if set(conflicts) - safe:
                    raise RuntimeError('Concurrent collection state changed; checkpoint retained for review')
                for filename in conflicts:
                    if filename in DATA:
                        variable = DATA[filename]
                        versions = [decode_data(git('show', f':{stage}:{filename}', root=root).stdout,
                                                variable) for stage in (1, 2, 3)]
                        rows = merge_records(*versions)
                        (root / filename).write_text('// Source-linked verified collection records.\nwindow.' +
                            variable + ' = ' + json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + ';\n')
                    else:
                        # Keep concurrent page edits and report metadata, then regenerate totals/version.
                        (root / filename).write_text(git('show', ':3:' + filename, root=root).stdout)
                subprocess.run([sys.executable, 'scripts/recount_dictionary.py'], cwd=root, check=True)
                state_path = root / 'scripts/target-campaign-report.json'
                if state_path.exists():
                    state = json.loads(state_path.read_text())
                    count = json.loads((root / 'scripts/collection-report.json').read_text())['records']['listed']
                    state['current_listed_records'] = count
                    state['remaining_to_target'] = max(0, state['target_records'] - count)
                    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
                refresh_asset_version(root)
                for filename in DATA:
                    subprocess.run(['node', '--check', filename], cwd=root, check=True)
                git('add', *DATA, 'index.html', 'scripts/collection-report.json',
                    'scripts/target-campaign-report.json', root=root)
                git('commit', '--no-edit', root=root)
            except Exception:
                git('merge', '--abort', root=root, check=False)
                raise
        pushed = git('push', 'origin', 'HEAD:main', root=root, check=False)
        if pushed.returncode == 0:
            return
        if attempt == 2:
            raise RuntimeError('Could not publish checkpoint: ' + pushed.stderr)
