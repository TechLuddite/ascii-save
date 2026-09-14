"""Shared pieces for the offscreen video pipelines: cell grids, ANSI in and out,
image conversion through scripts/convert-color.py, and ffmpeg assembly.

A "canvas" is a list of ROWS rows, each a list of COLS cells; a cell is None
(black, nothing drawn) or (glyph, fg_hex, bg_hex).
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'curation'))
import frames as decoder  # noqa: E402

_spec = importlib.util.spec_from_file_location('convert_color', ROOT / 'scripts/convert-color.py')
convert_color = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(convert_color)

PARCHMENT = 'e1d5c2'


def venv_python():
    """Interpreter with Pillow, numpy and terminaltexteffects: this one if it has them, else ROOT/.venv."""
    try:
        import PIL  # noqa: F401
        import numpy  # noqa: F401
        return sys.executable
    except ImportError:
        candidate = ROOT / '.venv/bin/python'
        if candidate.exists():
            return str(candidate)
        raise SystemExit('install video/requirements.txt into a virtualenv (see video/README.md)')


class Grid:
    def __init__(self, cols, rows, cell_w, cell_h, screen=(1920, 1200)):
        self.cols, self.rows, self.cell_w, self.cell_h = cols, rows, cell_w, cell_h
        self.screen = screen
        self.off_x = (screen[0] - cols * cell_w) // 2
        self.off_y = (screen[1] - rows * cell_h) // 2

    def blank(self):
        return [[None] * self.cols for _ in range(self.rows)]

    def paste(self, canvas, cells, left, top):
        for y, row in enumerate(cells):
            if 0 <= top + y < self.rows:
                for x, cell in enumerate(row):
                    if 0 <= left + x < self.cols:
                        canvas[top + y][left + x] = cell

    def image_cells(self, image, cols, rows):
        """Quadrant colour cells for image fitted inside cols x rows of this grid's cell aspect."""
        width, height = convert_color.image_size(image)
        cw, ch = convert_color.fit_cells(width, height, cols, rows, self.cell_w, self.cell_h)
        data = convert_color.raw_rgb(image, cw * 2, ch * 2)
        grid = convert_color.cells_from_raw(data, cw, ch, 'quadrant')
        return [[(g, '%02x%02x%02x' % fg, '%02x%02x%02x' % bg) for g, fg, bg in row] for row in grid]

    def to_ansi(self, canvas):
        lines = []
        for row in canvas:
            out, cur = [], None
            for cell in row:
                if cell is None:
                    if cur is not None:
                        out.append('\x1b[0m')
                        cur = None
                    out.append(' ')
                    continue
                g, fg, bg = cell
                if (fg, bg) != cur:
                    out.append('\x1b[38;2;%d;%d;%d;48;2;%d;%d;%dm' % (
                        int(fg[0:2], 16), int(fg[2:4], 16), int(fg[4:6], 16),
                        int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)))
                    cur = (fg, bg)
                out.append(g)
            out.append('\x1b[0m')
            lines.append(''.join(out).rstrip(' '))
        return '\n'.join(lines) + '\n'

    def from_ansi(self, text):
        """Parse a frame laid out as rows top to bottom with SGR colour and no cursor movement."""
        canvas = self.blank()
        for y, line in enumerate(text.split('\n')[:self.rows]):
            fg, bg, x = 'ffffff', None, 0
            for tok in decoder.TOKEN.findall(line):
                if tok.startswith('\x1b'):
                    if tok.startswith('\x1b[') and tok.endswith('m'):
                        f, b = decoder.apply_sgr(tok[2:-1], fg, bg or '000000')
                        fg, bg = f, (None if tok[2:-1] in ('0', '') else b)
                    continue
                for ch in tok:
                    if x < self.cols and ch != ' ':
                        canvas[y][x] = (ch, fg, bg or '000000')
                    x += 1
        return canvas

    def render_canvases(self, canvases, out_dir, jobs=8):
        """Render full canvases to out_dir/NNNNN.png with parallel worker processes."""
        out_dir.mkdir(parents=True, exist_ok=True)
        cells_dir = out_dir.parent / (out_dir.name + '-cells')
        cells_dir.mkdir(exist_ok=True)
        specs = []
        for i, canvas in enumerate(canvases):
            dst = out_dir / f'{i:05d}.png'
            if dst.exists():
                continue
            src = cells_dir / f'{i:05d}.json'
            src.write_text(json.dumps(canvas))
            specs.append(f'{src} {dst}\n')
        if not specs:
            return
        chunks = [specs[i::jobs] for i in range(jobs) if specs[i::jobs]]
        procs = []
        for chunk in chunks:
            p = subprocess.Popen([venv_python(), str(ROOT / 'video/render.py'), 'canvases', *self.args()],
                                 stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
            p.stdin.write(''.join(chunk))
            p.stdin.close()
            procs.append(p)
        for p in procs:
            if p.wait():
                raise RuntimeError('render worker failed')
        for f in cells_dir.glob('*.json'):
            f.unlink()

    def args(self):
        return ['--cols', str(self.cols), '--rows', str(self.rows), '--cell', f'{self.cell_w}x{self.cell_h}',
                '--screen', f'{self.screen[0]}x{self.screen[1]}']


def stock_logo_path():
    return Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy')) / 'logo.txt'


def doubled_logo(path=None, color=PARCHMENT):
    """The stock screensaver logo (half-block text art) doubled to 2x2 cells per glyph."""
    lines = (path or stock_logo_path()).read_text(encoding='utf-8').splitlines()
    width = max(len(line) for line in lines)
    cells = []
    for line in lines:
        top, bottom = [], []
        for ch in line.ljust(width):
            if ch == '█':
                top += [['█', color]] * 2
                bottom += [['█', color]] * 2
            elif ch == '▀':
                top += [['█', color]] * 2
                bottom += [None, None]
            elif ch == '▄':
                top += [None, None]
                bottom += [['█', color]] * 2
            elif ch.strip():
                top += [[ch, color]] * 2
                bottom += [[ch, color]] * 2
            else:
                top += [None, None]
                bottom += [None, None]
        cells.append(top)
        cells.append(bottom)
    return {'cols': width * 2, 'rows': len(cells), 'cells': cells}


def encode(entries, out, fps=60):
    """entries: list of (png_path, seconds). Concatenates with exact holds into an H.264 mp4."""
    listing = Path(str(out) + '.concat.txt')
    lines = [f"file '{p}'\nduration {s:.5f}\n" for p, s in entries]
    lines.append(f"file '{entries[-1][0]}'\n")
    listing.write_text(''.join(lines))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(listing),
                    '-vf', f'fps={fps},format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
                    '-movflags', '+faststart', str(out)], check=True)
    listing.unlink()
