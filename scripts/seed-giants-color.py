"""Convert every Giants background into colour block text from a clean Git checkout.

Portraits keep their full composition, including the painted names. The
wordmark has its parchment margins trimmed first so it fills the width. Output
targets the stock size-18 Foot screensaver grid (137x36 cells at 1920x1200)
and is validated with the colour preparer before the manifest is written.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from common import COLOR_PREPARER, ROOT, prepare

CONVERTER = ROOT / 'scripts/convert-color.py'
NOTICE = ROOT / 'examples/giants/ARTWORK-NOTICE.md'
COLS, ROWS, CELL = 137, 36, '14x33'
WORDMARK_TRIM = 20


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'examples/giants-color')
    args = parser.parse_args()
    checkout = args.checkout.expanduser().resolve()
    revision = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    remote = subprocess.check_output(['git', '-C', str(checkout), 'config', '--get', 'remote.origin.url'], text=True).strip()
    if subprocess.check_output(['git', '-C', str(checkout), 'status', '--porcelain']):
        parser.error('use a clean checkout so source provenance is reproducible')
    destination = args.output.expanduser().absolute()
    if destination.exists() and any(destination.iterdir()):
        parser.error('output must be empty; generate into a new directory and compare before replacing a collection')
    destination.mkdir(parents=True, exist_ok=True)
    sources = [p for p in (checkout / 'backgrounds').iterdir()
               if not p.is_symlink() and p.is_file() and p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}]

    def order(path):
        match = re.match(r'(\d+)-', path.name)
        return (int(match.group(1)) if match else 10000, path.name)
    sources.sort(key=order)
    if not sources:
        parser.error('no background images found')

    def convert(item):
        index, source = item
        output = destination / f'{index:02d}-{source.stem}.txt'
        trim = WORDMARK_TRIM if source.stem == 'omarchy' else 0
        result = subprocess.run([sys.executable, str(CONVERTER), str(source), str(output),
                                 '--cols', str(COLS), '--rows', str(ROWS), '--cell', CELL,
                                 '--mode', 'quadrant', '--trim', str(trim)],
                                check=True, capture_output=True, text=True, timeout=180)
        width, height = re.search(r': (\d+)x(\d+) cells', result.stdout).groups()
        return {'source': 'backgrounds/' + source.name, 'output': output.name,
                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                'width': int(width), 'height': int(height), 'trim_fuzz': trim or None}

    with ThreadPoolExecutor(max_workers=2) as workers:
        artworks = list(workers.map(convert, enumerate(sources, 1)))
    with prepare(destination, COLOR_PREPARER) as files:
        if len(files) != len(sources):
            raise RuntimeError('not every conversion passed the colour playback limits')
    manifest = {'source_repository': re.sub(r'\.git$', '', remote),
                'source_commit': revision,
                'format': 'truecolor quadrant block elements with SGR colour',
                'conversion': {'converter': CONVERTER.name, 'mode': 'quadrant', 'cols': COLS, 'rows': ROWS,
                               'terminal_cell_aspect': CELL.replace('x', ':'),
                               'resample': 'ImageMagick Lanczos to 2x2 samples per cell',
                               'cell_fit': 'best two-colour quadrant partition by squared RGB error',
                               'wordmark_trim_fuzz': f'{WORDMARK_TRIM}%', 'portraits_trimmed': False,
                               'requires': 'ttfx --existing-color-handling always|dynamic and an SGR-aware preparer'},
                'artworks': artworks,
                'converter_sha256': hashlib.sha256(CONVERTER.read_bytes()).hexdigest(),
                'imagemagick_version': subprocess.check_output(['magick', '-version'], text=True).splitlines()[0]}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (destination / 'SOURCE-CREDITS.md').write_bytes((checkout / 'CREDITS.md').read_bytes())
    notice = NOTICE.read_text().replace('image-to-braille conversion, preserving the source compositions at reduced detail',
                                        'image-to-colour-block conversion, preserving the source compositions and colours at reduced detail')
    (destination / 'ARTWORK-NOTICE.md').write_text(notice)
    print(f'Seeded and validated {len(artworks)} artworks at {destination}')


if __name__ == '__main__':
    main()
