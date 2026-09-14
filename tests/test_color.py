import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import COLOR_PREPARER, PREPARER, prepare

CONVERTER = ROOT / 'scripts/convert-color.py'
SGR = re.compile(r'\x1b\[[0-9;]*m')
BLOCKS = set('▘▝▀▖▌▞▛▗▚▐▜▄▙▟█')


def convert(image, output, *extra):
    return subprocess.run([sys.executable, str(CONVERTER), str(image), str(output), *extra],
                          check=True, capture_output=True, text=True, timeout=120).stdout


class ColorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.image = self.root / 'plasma.png'
        subprocess.run(['magick', '-size', '300x200', 'gradient:red-blue', '-seed', '7',
                        '+noise', 'Gaussian', str(self.image)], check=True, timeout=60)

    def tearDown(self):
        self.directory.cleanup()

    def test_convert_emits_only_block_glyphs_and_sgr_colour(self):
        output = self.root / 'plasma.txt'
        report = convert(self.image, output, '--cols', '40', '--rows', '10')
        self.assertIn(': 35x10 cells', report)  # 3:2 image, height-bound inside a 40x10 grid of 14x33 cells
        text = output.read_text(encoding='utf-8')
        lines = text.splitlines()
        self.assertEqual(len(lines), 10)
        for line in lines:
            visible = SGR.sub('', line)
            self.assertEqual(len(visible), 35)
            self.assertTrue(set(visible) <= BLOCKS, visible)
            self.assertTrue(line.endswith('\x1b[0m'))
        remaining = SGR.sub('', text)
        self.assertNotIn('\x1b', remaining)
        self.assertTrue(re.fullmatch(r'(\x1b\[38;2;\d+;\d+;\d+;48;2;\d+;\d+;\d+m|\x1b\[0m)',
                                     SGR.findall(text)[0]))
        self.assertGreater(len(set(SGR.findall(text))), 100, 'expected many distinct colour pairs')

    def test_half_mode_and_trim(self):
        framed = self.root / 'framed.png'
        subprocess.run(['magick', str(self.image), '-bordercolor', 'black', '-border', '150x0', str(framed)],
                       check=True, timeout=60)
        output = self.root / 'framed.txt'
        self.assertIn(': 35x10 cells', convert(framed, output, '--cols', '40', '--rows', '10', '--trim', '5'))
        self.assertIn(': 40x6 cells', convert(framed, output, '--cols', '40', '--rows', '10'))
        convert(self.image, output, '--cols', '40', '--rows', '10', '--mode', 'half')
        self.assertEqual(set(SGR.sub('', output.read_text()).replace('\n', '')), {'▀'})

    def test_colour_preparer_passes_sgr_and_rejects_other_controls(self):
        convert(self.image, self.root / '01-ok.txt', '--cols', '60', '--rows', '20')
        (self.root / '02-title.txt').write_text('\x1b]0;evil\x07\x1b[31mred\x1b[0m\n')
        (self.root / '03-cursor.txt').write_text('\x1b[2J\x1b[31mred\x1b[0m\n')
        (self.root / '04-plain.txt').write_text('  plain art\n  still fine\n')
        (self.root / '05-huge.txt').write_bytes(b'\x1b[31m' + b'#' * (1048576) + b'\n')
        with prepare(self.root, COLOR_PREPARER) as files:
            kept = [f.read_bytes() for f in files]
        self.assertEqual(len(kept), 2)
        self.assertEqual(kept[0], (self.root / '01-ok.txt').read_bytes())
        self.assertEqual(kept[1], (self.root / '04-plain.txt').read_bytes())

    def test_pinned_preparer_still_rejects_colour(self):
        convert(self.image, self.root / '01-ok.txt', '--cols', '60', '--rows', '20')
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            with prepare(self.root, PREPARER):
                pass
        self.assertIn(b'no usable text artwork', caught.exception.stderr)

    def test_giants_color_manifest_matches_files_and_plays(self):
        source = ROOT / 'examples/giants-color'
        manifest = json.loads((source / 'manifest.json').read_text())
        self.assertEqual(len(manifest['artworks']), 18)
        self.assertEqual({p.name for p in source.glob('*.txt')}, {a['output'] for a in manifest['artworks']})
        for art in manifest['artworks']:
            data = (source / art['output']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), art['output_sha256'])
            visible = SGR.sub('', data.decode())
            self.assertLessEqual(max(len(l) for l in visible.splitlines()), 137)
            self.assertLessEqual(len(visible.splitlines()), 36)
        with prepare(source, COLOR_PREPARER) as files:
            self.assertEqual(len(files), 18)


if __name__ == '__main__':
    unittest.main()
