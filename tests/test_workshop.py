import hashlib
import json
import os
from pathlib import Path
import pty
import subprocess
import sys
import tempfile
import termios
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import prepare


class WorkshopTests(unittest.TestCase):
    def test_original_examples_and_snapshot_cleanup(self):
        with prepare(ROOT / 'examples/observatory') as files:
            self.assertEqual(len(files), 3)
            snapshot = files[0].parent
        self.assertFalse(snapshot.exists())

    def test_entire_giants_manifest_is_playable_and_unchanged(self):
        source = ROOT / 'examples/giants'
        manifest = json.loads((source / 'manifest.json').read_text())
        self.assertEqual(len(manifest['artworks']), 18)
        for art in manifest['artworks']:
            data = (source / art['output']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), art['output_sha256'])
        with prepare(source) as files:
            self.assertEqual(len(files), len(manifest['artworks']))

    def test_validate_errors_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, ROOT / 'scripts/validate.py', directory], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b'no usable text artwork', result.stderr)

    def test_van_gogh_manifest_and_playback(self):
        source = ROOT / 'examples/van-gogh'
        manifest = json.loads((source / 'manifest.json').read_text())
        self.assertEqual(len(manifest['artworks']), 8)
        self.assertEqual({p.name for p in source.glob('*.txt')},
                         {a['output'] for a in manifest['artworks']})
        for art in manifest['artworks']:
            data = (source / art['output']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), art['output_sha256'])
            self.assertTrue(data.decode().endswith(art['caption'] + '\n'))
            self.assertTrue(art['public_domain'])
        with prepare(source) as files:
            self.assertEqual(len(files), 8)

    def test_van_gogh_seeder_rejects_unsafe_sources_before_conversion(self):
        for kind in ('symlink', 'fifo', 'wrong-hash', 'oversized'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / '436535.jpg'
                if kind == 'symlink':
                    (root / 'target').write_bytes(b'not a museum JPEG')
                    source.symlink_to(root / 'target')
                elif kind == 'fifo':
                    os.mkfifo(source)
                elif kind == 'oversized':
                    with source.open('wb') as handle:
                        handle.truncate(12_000_001)
                else:
                    source.write_bytes(b'not a museum JPEG')
                output = root / 'output'
                result = subprocess.run([sys.executable, ROOT / 'scripts/seed-van-gogh.py',
                                         root, '--output', output], capture_output=True, timeout=5)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())

    def test_preview_refuses_nonterminal_without_launching_renderer(self):
        result = subprocess.run([sys.executable, ROOT / 'scripts/preview.py'], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'run the preview in a terminal', result.stderr)

    def test_key_dismissal_restores_terminal_and_reaps_only_owned_child(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            renderer = directory / 'ttfx'
            pid_file = directory / 'pid'
            renderer.write_text('#!/bin/bash\necho $$ > "$PREVIEW_TEST_PID"\nexec sleep 60\n')
            renderer.chmod(0o755)
            environment = dict(os.environ, PATH=str(directory) + ':' + os.environ['PATH'], PREVIEW_TEST_PID=str(pid_file))
            master, slave = pty.openpty()
            original = termios.tcgetattr(slave)
            unrelated = subprocess.Popen(['sleep', '60'])
            preview = subprocess.Popen([sys.executable, ROOT / 'scripts/preview.py', ROOT / 'examples/observatory'],
                                       stdin=slave, stdout=slave, stderr=subprocess.PIPE, env=environment)
            try:
                deadline = time.monotonic() + 5
                while not pid_file.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(pid_file.exists(), 'renderer started')
                child_pid = int(pid_file.read_text())
                os.write(master, b'q')
                _, errors = preview.communicate(timeout=5)
                self.assertEqual(preview.returncode, 0, errors)
                self.assertEqual(termios.tcgetattr(slave), original)
                self.assertFalse(Path(f'/proc/{child_pid}').exists())
                self.assertIsNone(unrelated.poll())
            finally:
                if preview.poll() is None:
                    preview.terminate()
                    preview.wait(timeout=5)
                unrelated.terminate()
                unrelated.wait(timeout=5)
                os.close(master)
                os.close(slave)


if __name__ == '__main__':
    unittest.main()
