"""Opener: accelerating full-screen colour slides, the last one shrinks into a
grid, the rest pop in, a blackhole consumes the grid and explodes into the
stock Omarchy screensaver logo. Rendered offscreen; nothing is captured from
the screen.

usage: opener.py IMAGE_DIR [--out .local/video/opener] [--logo $OMARCHY_PATH/logo.txt]
                 [--cols 210 --rows 58 --cell 9x20] [--skip-video]
IMAGE_DIR holds the portraits (jpg/png/webp); files are ordered by their
leading number. The stock logo is read from OMARCHY_PATH.
outputs: OUT/frames/*.png, OUT/ansi/*.txt, OUT/timeline.json, OUT/opener.mp4
"""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import videolib as common  # noqa: E402

FPS = 60
GRID_ROWS = [4, 4, 3, 3, 3]
HOLDS = [2.0, 1.0, 0.75, 0.55, 0.42, 0.32, 0.26, 0.21, 0.18, 0.15, 0.13, 0.12, 0.11, 0.1, 0.1, 0.1, 0.1]


def ordered_images(directory):
    images = [p for p in Path(directory).iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}
              and re.match(r'\d+-', p.name)]
    return sorted(images, key=lambda p: int(p.name.split('-')[0]))


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


class Opener:
    def __init__(self, images, grid, out, logo_path=None):
        self.images, self.grid, self.out = images, grid, out
        self.cache = out / 'cache'
        self.cache.mkdir(parents=True, exist_ok=True)
        self.logo_path = logo_path
        gap = 1
        n = len(GRID_ROWS)
        self.tile_h = (grid.rows - gap * (n - 1) + 1) // n          # 58 rows -> 11-row tiles
        self.tile_w = round(self.tile_h * grid.cell_h / grid.cell_w * 1.5)  # 3:2 portraits
        self.row_top = [min(i * (self.tile_h + gap), grid.rows - self.tile_h) for i in range(n)]
        self.frames, self.timeline = [], []

    def cells(self, key, image, cols, rows):
        p = self.cache / f'{key}.json'
        if not p.exists():
            p.write_text(json.dumps(self.grid.image_cells(image, cols, rows)))
        return json.loads(p.read_text())

    def slot(self, index):
        row = 0
        while index >= GRID_ROWS[row]:
            index -= GRID_ROWS[row]
            row += 1
        n = GRID_ROWS[row]
        return round((index + .5) * self.grid.cols / n - self.tile_w / 2), self.row_top[row]

    def add(self, canvas, seconds, phase, **extra):
        self.frames.append(canvas)
        self.timeline.append({'frame': len(self.frames) - 1, 'seconds': seconds, 'phase': phase, **extra})

    def slides(self):
        holds = HOLDS[:len(self.images)] if len(self.images) <= len(HOLDS) else HOLDS + [0.1] * (len(self.images) - len(HOLDS))
        for i, (image, hold) in enumerate(zip(self.images, holds)):
            cells = self.cells(f'full-{i:02d}', image, self.grid.cols, self.grid.rows)
            canvas = self.grid.blank()
            self.grid.paste(canvas, cells, (self.grid.cols - len(cells[0])) // 2, (self.grid.rows - len(cells)) // 2)
            self.add(canvas, hold, 'slides', image=image.name)

    def shrink_and_grid(self):
        last = len(self.images) - 1
        end_left, end_top = self.slot(last)
        steps = 42
        for k in range(1, steps + 1):
            t = ease(k / steps)
            cols = round(self.grid.cols + (self.tile_w - self.grid.cols) * t)
            rows = round(self.grid.rows + (self.tile_h - self.grid.rows) * t)
            cells = self.cells(f'shrink-{cols}x{rows}', self.images[last], cols, rows)
            w, h = len(cells[0]), len(cells)
            left = round(((self.grid.cols - w) / 2) * (1 - t) + end_left * t)
            top = round(((self.grid.rows - h) / 2) * (1 - t) + end_top * t)
            canvas = self.grid.blank()
            self.grid.paste(canvas, cells, left, top)
            self.add(canvas, 1 / FPS, 'shrink')
        canvas = self.grid.blank()
        self.grid.paste(canvas, self.cells(f'tile-{last:02d}', self.images[last], self.tile_w, self.tile_h), end_left, end_top)
        for i in range(last):
            canvas = [row[:] for row in canvas]
            left, top = self.slot(i)
            self.grid.paste(canvas, self.cells(f'tile-{i:02d}', self.images[i], self.tile_w, self.tile_h), left, top)
            self.add(canvas, 3 / FPS, 'pop')
        self.timeline[-1]['seconds'] = 0.7
        return canvas

    def blackhole(self, gallery):
        frames_dir = self.cache / 'blackhole'
        if not (frames_dir / 'phases.json').exists():
            montage = self.cache / 'montage.txt'
            logo = self.cache / 'logo.json'
            montage.write_text(self.grid.to_ansi(gallery))
            logo.write_text(json.dumps(common.doubled_logo(self.logo_path)))
            subprocess.run([common.venv_python(), str(common.ROOT / 'video/blackhole.py'), str(montage), str(logo),
                            str(frames_dir), '--cols', str(self.grid.cols), '--rows', str(self.grid.rows)],
                           check=True, stdout=subprocess.DEVNULL)
        files = sorted(frames_dir.glob('*.txt'))
        for k, f in enumerate(files):        # TTE simulates 120 frames per second; keep every second one
            if k % 2 == 0:
                self.add(self.grid.from_ansi(f.read_text()), 1 / FPS, 'blackhole')
        self.timeline[-1]['seconds'] = 2.5

    def build(self, video=True):
        self.add(self.grid.blank(), 0.4, 'lead-in')
        self.slides()
        gallery = self.shrink_and_grid()
        self.blackhole(gallery)
        total = sum(e['seconds'] for e in self.timeline)
        (self.out / 'timeline.json').write_text(json.dumps(
            {'fps': FPS, 'seconds': round(total, 2), 'frames': len(self.frames), 'grid': self.grid.args(),
             'entries': self.timeline}, indent=1))
        ansi = self.out / 'ansi'
        ansi.mkdir(exist_ok=True)
        for i, canvas in enumerate(self.frames):
            (ansi / f'{i:05d}.txt').write_text(self.grid.to_ansi(canvas))
        self.grid.render_canvases(self.frames, self.out / 'frames')
        if video:
            entries = [(self.out / 'frames' / ('%05d.png' % e['frame']), e['seconds']) for e in self.timeline]
            common.encode(entries, self.out / 'opener.mp4', FPS)
        return total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('images')
    ap.add_argument('--out', default=str(common.ROOT / '.local/video/opener'))
    ap.add_argument('--logo', help='logo text file (default: $OMARCHY_PATH/logo.txt)')
    ap.add_argument('--cols', type=int, default=210)
    ap.add_argument('--rows', type=int, default=58)
    ap.add_argument('--cell', default='9x20', help='cell pixels at 1920x1200 (9x20 is Foot size 11)')
    ap.add_argument('--skip-video', action='store_true')
    a = ap.parse_args()
    images = ordered_images(a.images)
    if not images:
        sys.exit('no numbered images found')
    cw, ch = (int(v) for v in a.cell.split('x'))
    opener = Opener(images, common.Grid(a.cols, a.rows, cw, ch), Path(a.out), Path(a.logo) if a.logo else None)
    total = opener.build(video=not a.skip_video)
    print(f'{len(opener.frames)} frames, {total:.1f} s -> {opener.out}')


if __name__ == '__main__':
    main()
