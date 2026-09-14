"""Convert a raster image into colour block-element text for ttfx playback.

Each terminal cell becomes one Unicode quadrant block (or a half block) with a
24-bit foreground and background colour, so a 137x36 cell terminal shows a
274x72 pixel picture. Output uses only SGR colour sequences; no cursor movement
or other terminal controls are emitted. Decoding and resampling use ImageMagick
with restricted coders and resource limits, matching refine-giants.py.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

# Bits: 1 top-left, 2 top-right, 4 bottom-left, 8 bottom-right.
QUADRANTS = {1: '▘', 2: '▝', 3: '▀', 4: '▖', 5: '▌',
             6: '▞', 7: '▛', 8: '▗', 9: '▚', 10: '▐',
             11: '▜', 12: '▄', 13: '▙', 14: '▟', 15: '█'}
MAGICK_LIMITS = ['-limit', 'memory', '256MiB', '-limit', 'map', '512MiB',
                 '-limit', 'width', '16KP', '-limit', 'height', '16KP']


def trim_args(trim):
    """Optional edge trim (fuzz percent) so a wordmark on parchment fills the grid."""
    return ['-fuzz', '%d%%' % trim, '-trim', '+repage'] if trim else []


def raw_rgb(image, width, height, background='black', trim=0):
    """Return width*height*3 bytes of 8-bit RGB, resampled to exactly that size."""
    environment = dict(os.environ, MAGICK_CONFIGURE_PATH='/nonexistent')
    command = ['magick', *MAGICK_LIMITS, str(image) + '[0]', '-auto-orient',
               '-background', background, '-alpha', 'remove', '-alpha', 'off',
               '-colorspace', 'sRGB', *trim_args(trim),
               '-filter', 'Lanczos', '-resize', '%dx%d!' % (width, height),
               '-depth', '8', 'rgb:-']
    data = subprocess.run(command, check=True, capture_output=True, timeout=120,
                          env=environment).stdout
    if len(data) != width * height * 3:
        raise ValueError('unexpected raster size from ImageMagick')
    return data


def image_size(image, background='black', trim=0):
    command = ['magick', *MAGICK_LIMITS, str(image) + '[0]', '-auto-orient',
               '-background', background, '-alpha', 'remove', '-alpha', 'off',
               *trim_args(trim), '-format', '%w %h', 'info:']
    out = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120).stdout
    width, height = (int(v) for v in out.split())
    return width, height


def fit_cells(width, height, cols, rows, cell_w, cell_h):
    """Largest cell grid that keeps the image aspect inside cols x rows."""
    scale = min(cols * cell_w / width, rows * cell_h / height)
    return (max(1, round(width * scale / cell_w)), max(1, round(height * scale / cell_h)))


def mean(colors):
    n = len(colors)
    return tuple(sum(c[i] for c in colors) // n for i in range(3))


def error(colors, center):
    return sum((c[i] - center[i]) ** 2 for c in colors for i in range(3))


def best_quadrant(samples):
    """samples: four RGB tuples (tl, tr, bl, br). Returns (glyph, fg, bg)."""
    whole = mean(samples)
    best = (error(samples, whole), 15, whole, whole)
    if best[0] == 0:
        return QUADRANTS[15], whole, whole
    for mask in range(1, 15):
        on = [samples[i] for i in range(4) if mask & (1 << i)]
        off = [samples[i] for i in range(4) if not mask & (1 << i)]
        fg, bg = mean(on), mean(off)
        err = error(on, fg) + error(off, bg)
        if err < best[0]:
            best = (err, mask, fg, bg)
    _, mask, fg, bg = best
    return QUADRANTS[mask], fg, bg


def cells_from_raw(data, cells_w, cells_h, mode):
    sub_w, sub_h = (2, 2) if mode == 'quadrant' else (1, 2)
    width = cells_w * sub_w
    def px(x, y):
        i = (y * width + x) * 3
        return data[i], data[i + 1], data[i + 2]
    rows = []
    for cy in range(cells_h):
        row = []
        for cx in range(cells_w):
            if mode == 'quadrant':
                samples = [px(cx * 2, cy * 2), px(cx * 2 + 1, cy * 2),
                           px(cx * 2, cy * 2 + 1), px(cx * 2 + 1, cy * 2 + 1)]
                row.append(best_quadrant(samples))
            else:
                row.append((QUADRANTS[3], px(cx, cy * 2), px(cx, cy * 2 + 1)))
        rows.append(row)
    return rows


def render(rows):
    lines = []
    for row in rows:
        out = []
        current = (None, None)
        for glyph, fg, bg in row:
            if (fg, bg) != current:
                out.append('\x1b[38;2;%d;%d;%d;48;2;%d;%d;%dm' % (fg + bg))
                current = (fg, bg)
            out.append(glyph)
        out.append('\x1b[0m')
        lines.append(''.join(out))
    return '\n'.join(lines) + '\n'


def convert(image, cols=137, rows=36, cell='14x33', mode='quadrant', background='black', trim=0):
    cell_w, cell_h = (int(v) for v in cell.split('x'))
    width, height = image_size(image, background, trim)
    cells_w, cells_h = fit_cells(width, height, cols, rows, cell_w, cell_h)
    sub_w, sub_h = (2, 2) if mode == 'quadrant' else (1, 2)
    data = raw_rgb(image, cells_w * sub_w, cells_h * sub_h, background, trim)
    text = render(cells_from_raw(data, cells_w, cells_h, mode))
    return text, cells_w, cells_h


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image')
    parser.add_argument('output')
    parser.add_argument('--cols', type=int, default=137, help='terminal columns available')
    parser.add_argument('--rows', type=int, default=36, help='terminal rows available')
    parser.add_argument('--cell', default='14x33', help='cell pixel aspect, width x height')
    parser.add_argument('--mode', choices=('quadrant', 'half'), default='quadrant')
    parser.add_argument('--background', default='black', help='colour behind transparent pixels')
    parser.add_argument('--trim', type=int, default=0, metavar='FUZZ',
                        help='trim near-uniform edges first, with this fuzz percent')
    args = parser.parse_args()
    try:
        text, w, h = convert(args.image, args.cols, args.rows, args.cell, args.mode,
                             args.background, args.trim)
    except (OSError, ValueError, subprocess.SubprocessError) as err:
        print(f'convert-color: {err}', file=sys.stderr)
        return 1
    Path(args.output).write_text(text, encoding='utf-8')
    print(f'{args.output}: {w}x{h} cells, {len(text.encode())} bytes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
