"""Offscreen frame renderer (needs Pillow and numpy).

  render.py canvases --cols C --rows R --cell WxH [--screen 1920x1200]
      reads "src.json dst.png" lines on stdin; each src is a full canvas
  render.py clip FRAMES.json OUT_DIR --cols C --rows R --cell WxH
      plays a curation-style cell-diff clip and writes OUT_DIR/NNNNN.png per frame

Block elements are drawn as filled rectangles, exactly as Foot draws them;
every other glyph is drawn with JetBrainsMono Nerd Font.
"""
import argparse
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf'
QUAD = {'▘': [(0, 0, .5, .5)], '▝': [(.5, 0, .5, .5)], '▀': [(0, 0, 1, .5)], '▖': [(0, .5, .5, .5)], '▌': [(0, 0, .5, 1)],
        '▞': [(.5, 0, .5, .5), (0, .5, .5, .5)], '▛': [(0, 0, 1, .5), (0, .5, .5, .5)], '▗': [(.5, .5, .5, .5)],
        '▚': [(0, 0, .5, .5), (.5, .5, .5, .5)], '▐': [(.5, 0, .5, 1)], '▜': [(0, 0, 1, .5), (.5, .5, .5, .5)],
        '▄': [(0, .5, 1, .5)], '▙': [(0, 0, .5, 1), (.5, .5, .5, .5)], '▟': [(.5, 0, .5, .5), (0, .5, 1, .5)],
        '█': [(0, 0, 1, 1)], '▁': [(0, .875, 1, .125)], '▂': [(0, .75, 1, .25)], '▃': [(0, .625, 1, .375)],
        '▅': [(0, .375, 1, .625)], '▆': [(0, .25, 1, .75)], '▇': [(0, .125, 1, .875)], '▏': [(0, 0, .125, 1)],
        '▎': [(0, 0, .25, 1)], '▍': [(0, 0, .375, 1)], '▋': [(0, 0, .625, 1)], '▊': [(0, 0, .75, 1)],
        '▉': [(0, 0, .875, 1)]}
SHADE = {'░': .25, '▒': .5, '▓': .75}


def rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


class Painter:
    def __init__(self, cols, rows, cell, screen):
        self.cw, self.ch = (int(v) for v in cell.split('x'))
        self.W, self.H = (int(v) for v in screen.split('x'))
        self.ox = (self.W - cols * self.cw) // 2
        self.oy = (self.H - rows * self.ch) // 2
        self.font = ImageFont.truetype(FONT, max(6, int(self.ch * 0.72)))
        self.img = np.zeros((self.H, self.W, 3), np.uint8)
        self.text = {}

    def clear(self):
        self.img[:] = 0
        self.text.clear()

    def cell(self, x, y, g, fg, bg):
        cw, ch = self.cw, self.ch
        X, Y = self.ox + x * cw, self.oy + y * ch
        self.img[Y:Y + ch, X:X + cw] = bg
        self.text.pop((x, y), None)
        if g in QUAD:
            for rx, ry, rw, rh in QUAD[g]:
                self.img[Y + int(ry * ch):Y + int((ry + rh) * ch), X + int(rx * cw):X + int((rx + rw) * cw)] = fg
        elif g in SHADE:
            a = SHADE[g]
            self.img[Y:Y + ch, X:X + cw] = tuple(int(bg[k] + (fg[k] - bg[k]) * a) for k in range(3))
        elif g.strip():
            self.text[(x, y)] = (g, fg)

    def save(self, path):
        im = Image.fromarray(self.img)
        if self.text:
            d = ImageDraw.Draw(im)
            for (x, y), (g, f) in self.text.items():
                d.text((self.ox + x * self.cw, self.oy + y * self.ch), g, font=self.font, fill=f)
        im.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=('canvases', 'clip'))
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--cols', type=int, required=True)
    ap.add_argument('--rows', type=int, required=True)
    ap.add_argument('--cell', required=True)
    ap.add_argument('--screen', default='1920x1200')
    a = ap.parse_args()
    painter = Painter(a.cols, a.rows, a.cell, a.screen)
    if a.mode == 'canvases':
        for spec in sys.stdin:
            src, dst = spec.split()
            painter.clear()
            for y, row in enumerate(json.load(open(src))):
                for x, cell in enumerate(row):
                    if cell is not None:
                        painter.cell(x, y, cell[0], rgb(cell[1]), rgb(cell[2]))
            painter.save(dst)
    else:
        src, out_dir = a.paths
        clip = json.load(open(src))
        palette = [(rgb(f), rgb(b)) for f, b in clip['palette']]
        painter.clear()
        for n, (_, cells) in enumerate(clip['frames']):
            for i in range(0, len(cells), 4):
                fg, bg = palette[cells[i + 3]]
                painter.cell(cells[i], cells[i + 1], cells[i + 2], fg, bg)
            painter.save(f'{out_dir}/{n:05d}.png')
        print(len(clip['frames']))


if __name__ == '__main__':
    main()
