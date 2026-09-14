import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'video'))
import videolib as common  # noqa: E402
import opener  # noqa: E402
import showcase  # noqa: E402

try:
    import terminaltexteffects  # noqa: F401
    HAVE_TTE = True
except ImportError:
    HAVE_TTE = False
try:
    import PIL  # noqa: F401
    import numpy  # noqa: F401
    HAVE_RENDER = True
except ImportError:
    HAVE_RENDER = False


class VideoTests(unittest.TestCase):
    def test_logo_doubling_maps_half_blocks_exactly(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'logo.txt'
            p.write_text('▀█\n▄ \n')
            logo = common.doubled_logo(p, 'abcdef')
            self.assertEqual((logo['cols'], logo['rows']), (4, 4))
            full = ['█', 'abcdef']
            self.assertEqual(logo['cells'][0], [full, full, full, full])
            self.assertEqual(logo['cells'][1], [None, None, full, full])
            self.assertEqual(logo['cells'][2], [None, None, None, None])
            self.assertEqual(logo['cells'][3], [full, full, None, None])

    def test_ansi_round_trip(self):
        grid = common.Grid(6, 2, 9, 20)
        canvas = grid.blank()
        canvas[0][1] = ('▀', 'ff0000', '0000ff')
        canvas[1][5] = ('*', 'ffffff', '000000')
        text = grid.to_ansi(canvas)
        self.assertNotIn('\x1b[', text.replace('\x1b[38;2;255;0;0;48;2;0;0;255m', '').replace(
            '\x1b[38;2;255;255;255;48;2;0;0;0m', '').replace('\x1b[0m', ''))
        self.assertEqual(grid.from_ansi(text), canvas)

    def test_grid_slots_fit_inside_canvas(self):
        grid = common.Grid(210, 58, 9, 20)
        with tempfile.TemporaryDirectory() as d:
            op = opener.Opener([Path(d) / f'{i}-x.jpg' for i in range(1, 18)], grid, Path(d) / 'out')
            self.assertEqual((op.tile_w, op.tile_h), (37, 11))
            self.assertEqual(op.row_top, [0, 12, 24, 36, 47])
            for i in range(17):
                left, top = op.slot(i)
                self.assertGreaterEqual(left, 0)
                self.assertLessEqual(left + op.tile_w, 210)
                self.assertLessEqual(top + op.tile_h, 58)
            self.assertEqual(op.slot(16)[1], op.row_top[4])

    def test_compression_targets_and_caps(self):
        self.assertEqual(showcase.compression(3, 5, 10), 1.0)
        self.assertEqual(showcase.compression(5, 5, 10), 1.0)
        self.assertAlmostEqual(showcase.compression(45, 5, 10), 9.0)
        self.assertAlmostEqual(showcase.compression(80, 5, 10), 16.0)
        self.assertAlmostEqual(80 / showcase.compression(80, 5, 10), 5.0)

    @unittest.skipUnless(HAVE_RENDER, 'Pillow and numpy not installed in this interpreter')
    def test_renderer_paints_block_cells_and_text(self):
        with tempfile.TemporaryDirectory() as d:
            clip = {'cols': 4, 'rows': 2, 'palette': [['ff0000', '0000ff'], ['ffffff', '000000']],
                    'frames': [[0.0, [0, 0, '▀', 0]], [0.1, [3, 1, 'A', 1]]]}
            src = Path(d) / 'clip.json'
            src.write_text(json.dumps(clip))
            subprocess.run([sys.executable, str(ROOT / 'video/render.py'), 'clip', str(src), d,
                            '--cols', '4', '--rows', '2', '--cell', '10x20', '--screen', '40x40'], check=True,
                           capture_output=True)
            from PIL import Image
            im = Image.open(Path(d) / '00001.png').convert('RGB')
            self.assertEqual(im.size, (40, 40))
            self.assertEqual(im.getpixel((2, 2)), (255, 0, 0))     # top half of ▀ is the foreground
            self.assertEqual(im.getpixel((2, 15)), (0, 0, 255))    # bottom half is the background
            self.assertEqual(im.getpixel((15, 2)), (0, 0, 0))      # untouched cell stays black
            self.assertTrue(any(im.getpixel((x, y)) != (0, 0, 0) for x in range(30, 40) for y in range(20, 40)),
                            'text glyph was not drawn')

    @unittest.skipUnless(HAVE_TTE, 'terminaltexteffects not installed in this interpreter')
    def test_blackhole_override_runs_and_ends_on_logo(self):
        import blackhole
        grid = common.Grid(24, 8, 9, 20)
        canvas = grid.blank()
        for y in range(2, 6):
            for x in range(4, 20):
                canvas[y][x] = ('█', 'aa8866', '221100')
        logo = {'cols': 4, 'rows': 2, 'cells': [[['█', 'e1d5c2']] * 4, [None, ['█', 'e1d5c2'], ['█', 'e1d5c2'], None]]}
        with tempfile.TemporaryDirectory() as d:
            count, phases = blackhole.run(grid.to_ansi(canvas), logo, d, cols=24, rows=8)
            self.assertEqual([p['phase'] for p in phases], ['forming', 'consuming', 'collapsing', 'exploding', 'complete'])
            last = grid.from_ansi((Path(d) / f'{count:05d}.txt').read_text())
            drawn = {(x, y) for y, row in enumerate(last) for x, c in enumerate(row) if c}
            self.assertEqual(len(drawn), 6, 'final frame should hold exactly the six logo cells')


if __name__ == '__main__':
    unittest.main()
