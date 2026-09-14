"""Curate ttfx effects for a screensaver collection by watching and voting.

Subcommands (working directory defaults to .local/curation, which is ignored by git):

  record ARTWORK        record every ttfx effect on ARTWORK into DIR/casts and
                        convert each to DIR/frames (gzip alongside)
  serve                 serve the voting page for DIR on 127.0.0.1
  apply                 write the "yes" votes into the renderer's include list
  list                  print the current yes / no / undecided lists

Typical run:
  python3 curation/curate.py record examples/giants-color/03-3-ada-lovelace.txt
  python3 curation/curate.py serve          # open the printed URL, vote with y / n
  python3 curation/curate.py apply          # updates scripts/omarchy-screensaver-color
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_DIR = ROOT / '.local/curation'
RENDERER = ROOT / 'scripts/omarchy-screensaver-color'
sys.path.insert(0, str(HERE))
import frames as frames_module  # noqa: E402
import record as record_module  # noqa: E402
import serve as serve_module  # noqa: E402


def effect_names():
    out = subprocess.run(['ttfx', '--help'], check=True, capture_output=True, text=True).stdout
    names, active = [], False
    for line in out.splitlines():
        if line.startswith('Commands:'):
            active = True
            continue
        if line.startswith('Options:'):
            break
        if active and line.strip():
            name = line.split()[0]
            if name != 'help':
                names.append(name)
    return names


def cmd_record(a):
    directory = Path(a.dir)
    casts, frames = directory / 'casts', directory / 'frames'
    casts.mkdir(parents=True, exist_ok=True)
    frames.mkdir(parents=True, exist_ok=True)
    artwork = Path(a.artwork).resolve()
    if not artwork.is_file():
        sys.exit(f'artwork not found: {artwork}')
    names = a.effects or effect_names()

    def one(effect):
        cast = casts / f'{effect}.cast'
        meta = record_module.record(str(cast), artwork, effect, a.cols, a.rows, a.cap)
        data = frames_module.convert(cast, a.fps)
        data['artwork'] = artwork.name
        out = frames / f'{effect}.json'
        with open(out, 'w') as f:
            json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
        with open(out, 'rb') as src, gzip.open(str(out) + '.gz', 'wb') as dst:
            shutil.copyfileobj(src, dst)
        if not a.keep_casts:
            cast.unlink(missing_ok=True)
            Path(str(cast) + '.meta.json').unlink(missing_ok=True)
        return effect, meta['seconds'], meta['capped'], len(data['frames'])

    print(f'recording {len(names)} effects on {artwork.name} at {a.cols}x{a.rows}, cap {a.cap}s, {a.jobs} at a time')
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for effect, seconds, capped, count in pool.map(one, names):
            print(f'  {effect:16} {seconds:6.1f}s {"capped " if capped else "       "} {count} frames')
    print(f'done: {frames}')


def cmd_serve(a):
    server = serve_module.serve(a.dir, a.port)
    server.serve_forever()


def votes_of(directory):
    try:
        with open(Path(directory) / 'votes.json') as f:
            votes = json.load(f)
    except (OSError, ValueError):
        votes = {}
    yes = sorted(k for k, v in votes.items() if v == 'y')
    no = sorted(k for k, v in votes.items() if v == 'n')
    return votes, yes, no


def cmd_list(a):
    votes, yes, no = votes_of(a.dir)
    known = effect_names()
    undecided = [e for e in known if e not in votes]
    print('yes:', ' '.join(yes) or '(none)')
    print('no:', ' '.join(no) or '(none)')
    print('undecided:', ' '.join(undecided) or '(none)')


def apply_votes(renderer, yes):
    text = renderer.read_text()
    line = 'include_effects=(%s)\n' % ' '.join(yes)
    pattern = re.compile(r'^include_effects=\([^)]*\)\n', re.M)
    if pattern.search(text):
        text = pattern.sub(line, text, count=1)
    else:
        text = text.replace('playback_directory=""\n', 'playback_directory=""\n' + line, 1)
    renderer.write_text(text)
    return line.strip()


def cmd_apply(a):
    _, yes, _ = votes_of(a.dir)
    if not yes:
        sys.exit('no yes votes recorded; nothing applied')
    print(apply_votes(Path(a.renderer), yes))
    print(f'updated {a.renderer}; reinstall it where the screensaver reads it')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dir', default=str(DEFAULT_DIR), help='working directory for casts, frames and votes')
    sub = ap.add_subparsers(dest='command', required=True)
    r = sub.add_parser('record')
    r.add_argument('artwork')
    r.add_argument('--effects', nargs='*', help='subset of effects (default: all ttfx effects)')
    r.add_argument('--cols', type=int, default=137)
    r.add_argument('--rows', type=int, default=36)
    r.add_argument('--cap', type=float, default=120, help='seconds after which a recording is stopped')
    r.add_argument('--fps', type=float, default=30, help='playback frame rate kept in the clip')
    r.add_argument('--jobs', type=int, default=4)
    r.add_argument('--keep-casts', action='store_true', help='keep raw casts (hundreds of MB each)')
    r.set_defaults(func=cmd_record)
    s = sub.add_parser('serve')
    s.add_argument('--port', type=int, default=8765)
    s.set_defaults(func=cmd_serve)
    p = sub.add_parser('apply')
    p.add_argument('--renderer', default=str(RENDERER))
    p.set_defaults(func=cmd_apply)
    sub.add_parser('list').set_defaults(func=cmd_list)
    a = ap.parse_args()
    a.func(a)


if __name__ == '__main__':
    main()
