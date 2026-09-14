"""Convert a raw ttfx asciicast into compact per-frame cell diffs for the curation player.

ttfx output structure (as captured through a pty): an initial hide-cursor,
then for each frame: ESC[<rows>A (cursor up), then <rows> lines separated by
CR LF, each a run of SGR sequences and text. This decoder assumes exactly
that; it is not a general terminal emulator. Raw casts are hundreds of
megabytes because every cell is redrawn every frame; the diff output is
typically under a few megabytes.

Output JSON: {"cols","rows","fps","seconds","capped","palette":[[fg,bg],...],
"frames":[[t, [x,y,ch,paletteIndex, x,y,ch,paletteIndex, ...]], ...]}
Only cells that changed since the previous emitted frame are listed.

usage: frames.py IN.cast OUT.json [--fps 30]
"""
import argparse
import bisect
import json
import re
import sys

TOKEN = re.compile(r'\x1b\[[0-9;]*m|\x1b[^\[]|\x1b\[[0-9;?]*[A-Za-z]|[^\x1b]+')
ANSI16 = ['000000', 'aa0000', '00aa00', 'aa5500', '0000aa', 'aa00aa', '00aaaa', 'aaaaaa',
          '555555', 'ff5555', '55ff55', 'ffff55', '5555ff', 'ff55ff', '55ffff', 'ffffff']
DEFAULT = (' ', 'ffffff', '000000')


def c256(n):
    if n < 16:
        return ANSI16[n]
    if n < 232:
        n -= 16
        r, g, b = n // 36, (n // 6) % 6, n % 6
        return '%02x%02x%02x' % tuple(0 if v == 0 else 55 + 40 * v for v in (r, g, b))
    v = 8 + 10 * (n - 232)
    return '%02x%02x%02x' % (v, v, v)


def apply_sgr(params, fg, bg):
    p = [int(x) if x else 0 for x in params.split(';')] or [0]
    j = 0
    while j < len(p):
        v = p[j]
        if v == 0:
            fg, bg = 'ffffff', '000000'
        elif 30 <= v <= 37:
            fg = ANSI16[v - 30]
        elif 90 <= v <= 97:
            fg = ANSI16[v - 90 + 8]
        elif 40 <= v <= 47:
            bg = ANSI16[v - 40]
        elif 100 <= v <= 107:
            bg = ANSI16[v - 100 + 8]
        elif v in (38, 48) and j + 1 < len(p):
            col = None
            if p[j + 1] == 2 and j + 4 < len(p):
                col = '%02x%02x%02x' % tuple(min(255, max(0, c)) for c in p[j + 2:j + 5])
                j += 4
            elif p[j + 1] == 5 and j + 2 < len(p):
                col = c256(p[j + 2])
                j += 2
            if col:
                if v == 38:
                    fg = col
                else:
                    bg = col
        elif v == 39:
            fg = 'ffffff'
        elif v == 49:
            bg = '000000'
        j += 1
    return fg, bg


def convert(cast_path, fps=30.0):
    with open(cast_path, encoding='utf-8') as f:
        header = json.loads(f.readline())
        cols, rows = header['width'], header['height']
        chunks = [json.loads(line) for line in f if line.strip()]
    up = '\x1b[%dA' % rows
    text = ''.join(chunk[2] for chunk in chunks)
    starts, times, acc = [], [], 0
    for t, _, data in chunks:
        starts.append(acc)
        times.append(t)
        acc += len(data)

    def time_at(pos):
        i = bisect.bisect_right(starts, pos) - 1
        return times[max(i, 0)] if times else 0.0

    positions = [m.start() for m in re.finditer(re.escape(up), text)]
    positions.append(len(text))
    prev = [[DEFAULT] * cols for _ in range(rows)]
    palette, pindex, frames = [], {}, []
    last_emit = -1.0
    step = 1.0 / fps
    for k in range(len(positions) - 1):
        body = text[positions[k] + len(up):positions[k + 1]]
        t = time_at(positions[k])
        is_last = k == len(positions) - 2
        if t - last_emit < step and not is_last:
            continue
        grid = [[DEFAULT] * cols for _ in range(rows)]
        fg, bg = 'ffffff', '000000'
        for y, line in enumerate(body.split('\r\n')[:rows]):
            x = 0
            row = grid[y]
            for tok in TOKEN.findall(line):
                if tok.startswith('\x1b['):
                    if tok.endswith('m'):
                        fg, bg = apply_sgr(tok[2:-1], fg, bg)
                    continue
                if tok.startswith('\x1b'):
                    continue
                for ch in tok:
                    if x < cols:
                        row[x] = (ch, fg, bg)
                    x += 1
        cells = []
        for y in range(rows):
            prow, grow = prev[y], grid[y]
            for x in range(cols):
                if prow[x] != grow[x]:
                    ch, cfg, cbg = grow[x]
                    idx = pindex.get((cfg, cbg))
                    if idx is None:
                        idx = pindex[(cfg, cbg)] = len(palette)
                        palette.append([cfg, cbg])
                    cells.extend((x, y, ch, idx))
        if cells or not frames:
            frames.append([round(t, 3), cells])
        prev = grid
        last_emit = t
    meta = {}
    try:
        with open(str(cast_path) + '.meta.json') as f:
            meta = json.load(f)
    except (OSError, ValueError):
        pass
    return {'cols': cols, 'rows': rows, 'fps': fps,
            'seconds': meta.get('seconds', frames[-1][0] if frames else 0),
            'capped': meta.get('capped', False), 'palette': palette, 'frames': frames}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('inp')
    ap.add_argument('out')
    ap.add_argument('--fps', type=float, default=30)
    a = ap.parse_args()
    out = convert(a.inp, a.fps)
    with open(a.out, 'w') as f:
        json.dump(out, f, separators=(',', ':'), ensure_ascii=False)
    updates = sum(len(c) // 4 for _, c in out['frames'])
    print(f"{a.out}: {len(out['frames'])} frames, {len(out['palette'])} colour pairs, {updates} cell updates",
          file=sys.stderr)


if __name__ == '__main__':
    main()
