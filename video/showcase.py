"""Showcase: an opener (built by opener.py) followed by one ttfx effect per
artwork, each recorded through a pty at the screensaver grid with colour kept
and rendered offscreen. Effects longer than --target seconds are
time-compressed to the target by sampling the recording; nothing exceeds --cap.

usage: showcase.py COLLECTION [--opener .local/video/opener] [--out .local/video/showcase]
                   [--effects a b c ... | --votes VOTES.json] [--target 5 --cap 10 --hold 1.5]
                   [--cols 137 --rows 36 --cell 14x33] [--jobs 4] [--limit N]
COLLECTION is a text collection (e.g. examples/giants-color). Effects are
assigned to artworks in order; with --votes, the yes votes are used in file
order and any beyond the number of artworks are unused.
outputs: OUT/segments/<nn>-<effect>/, OUT/showcase.mp4
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import videolib as common  # noqa: E402
sys.path.insert(0, str(common.ROOT / 'curation'))
import frames as decoder  # noqa: E402
import record as recorder  # noqa: E402

FPS = 60
DEFAULT_EFFECTS = ['beams', 'decrypt', 'crumble', 'fireworks', 'matrix', 'rings', 'synthgrid', 'burn', 'rain',
                   'orbittingvolley', 'thunderstorm', 'binarypath', 'unstable', 'vhstape', 'swarm', 'spray',
                   'blackhole']


def compression(seconds, target, cap):
    """Playback speed factor: 1 up to target, then just enough to land on target (never above cap)."""
    if seconds <= target:
        return 1.0
    return max(seconds / target, seconds / cap)


def segment(index, artwork, effect, out, grid, target, cap, record_cap):
    seg = out / f'{index + 1:02d}-{effect}'
    seg.mkdir(parents=True, exist_ok=True)
    meta_path = seg / 'meta.json'
    if not meta_path.exists():
        cast = seg / 'raw.cast'
        meta = recorder.record(str(cast), artwork, effect, grid.cols, grid.rows, record_cap)
        speed = compression(meta['seconds'], target, cap)
        clip = decoder.convert(cast, fps=FPS / speed)
        clip.update({'artwork': artwork.name, 'effect': effect, 'speed': speed})
        (seg / 'frames.json').write_text(json.dumps(clip, separators=(',', ':'), ensure_ascii=False))
        cast.unlink(missing_ok=True)
        Path(str(cast) + '.meta.json').unlink(missing_ok=True)
        meta.update({'speed': speed, 'frames': len(clip['frames']), 'played_seconds': len(clip['frames']) / FPS})
        meta_path.write_text(json.dumps(meta, indent=1))
    return seg, json.loads(meta_path.read_text())


def render(seg, grid):
    frames_dir = seg / 'frames'
    if frames_dir.exists() and any(frames_dir.iterdir()):
        return
    frames_dir.mkdir(exist_ok=True)
    subprocess.run([common.venv_python(), str(common.ROOT / 'video/render.py'), 'clip', str(seg / 'frames.json'),
                    str(frames_dir), *grid.args()], check=True, stdout=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('collection')
    ap.add_argument('--opener', default=str(common.ROOT / '.local/video/opener'))
    ap.add_argument('--out', default=str(common.ROOT / '.local/video/showcase'))
    ap.add_argument('--effects', nargs='*')
    ap.add_argument('--votes', help='curation votes.json; yes votes are used in listed order')
    ap.add_argument('--target', type=float, default=5.0)
    ap.add_argument('--cap', type=float, default=10.0)
    ap.add_argument('--hold', type=float, default=1.5)
    ap.add_argument('--record-cap', type=float, default=130)
    ap.add_argument('--cols', type=int, default=137)
    ap.add_argument('--rows', type=int, default=36)
    ap.add_argument('--cell', default='14x33', help='cell pixels at 1920x1200 (14x33 is Foot size 18)')
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--limit', type=int, help='only the first N artworks (smoke test)')
    ap.add_argument('--no-opener', action='store_true')
    a = ap.parse_args()
    artworks = sorted(p for p in Path(a.collection).glob('*.txt') if p.name[:2].isdigit())
    artworks = [p for p in artworks if not p.stem.endswith('omarchy')]
    if a.limit:
        artworks = artworks[:a.limit]
    if a.votes:
        votes = json.loads(Path(a.votes).read_text())
        effects = [e for e, v in votes.items() if v == 'y']
    else:
        effects = a.effects or DEFAULT_EFFECTS
    if len(effects) < len(artworks):
        sys.exit(f'{len(artworks)} artworks but only {len(effects)} effects')
    effects = effects[:len(artworks)]
    cw, ch = (int(v) for v in a.cell.split('x'))
    grid = common.Grid(a.cols, a.rows, cw, ch)
    out = Path(a.out)
    segments_dir = out / 'segments'
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        results = list(pool.map(lambda ie: segment(ie[0], artworks[ie[0]], ie[1], segments_dir, grid, a.target, a.cap,
                                                   a.record_cap), enumerate(effects)))
    for i, (seg, m) in enumerate(results):
        print(f'{i + 1:2d} {seg.name:22} recorded {m["seconds"]:6.1f}s  speed x{m["speed"]:.1f}  '
              f'played {m["played_seconds"]:.1f}s{"  CAPPED" if m["capped"] else ""}')
        assert m['played_seconds'] <= a.cap + 0.02, seg.name
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda r: render(r[0], grid), results))
    entries = []
    if not a.no_opener:
        opener = json.loads((Path(a.opener) / 'timeline.json').read_text())
        entries += [(Path(a.opener) / 'frames' / ('%05d.png' % e['frame']), e['seconds']) for e in opener['entries']]
    for seg, _ in results:
        pngs = sorted((seg / 'frames').glob('*.png'))
        entries += [(p, 1 / FPS) for p in pngs[:-1]] + [(pngs[-1], a.hold)]
    common.encode(entries, out / 'showcase.mp4', FPS)
    total = sum(s for _, s in entries)
    print(f'{total:.1f} s -> {out / "showcase.mp4"}')


if __name__ == '__main__':
    main()
