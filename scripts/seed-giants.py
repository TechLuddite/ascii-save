"""Convert every Giants background from an explicit, clean Git checkout."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from common import ROOT, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'examples/giants')
    args = parser.parse_args()
    checkout = args.checkout.expanduser().resolve()
    revision = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
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
        subprocess.run(['omarchy', 'transcode', 'ascii', str(source), str(output),
                        '--width', '140', '--height', '46', '--threshold', '55', '--no-trim'],
                       env=dict(os.environ, MAGICK_THREAD_LIMIT='2'), check=True, capture_output=True, timeout=60)
        return {'source': 'backgrounds/' + source.name, 'output': output.name,
                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}

    with ThreadPoolExecutor(max_workers=2) as workers:
        artworks = list(workers.map(convert, enumerate(sources, 1)))
    with prepare(destination) as files:
        if len(files) != len(sources):
            raise RuntimeError('not every conversion passed the playback limits')
    converter = Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy')) / 'bin/omarchy-transcode-ascii'
    manifest = {'source_repository': 'https://github.com/dhh/omarchy-giants-theme',
                'source_commit': revision, 'format': 'braille',
                'conversion': {'width': 140, 'height': 46, 'threshold': 55, 'trim': False},
                'artworks': artworks,
                'converter_sha256': hashlib.sha256(converter.read_bytes()).hexdigest() if converter.is_file() else None,
                'imagemagick_version': subprocess.check_output(['magick', '-version'], text=True).splitlines()[0]}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (destination / 'SOURCE-CREDITS.md').write_bytes((checkout / 'CREDITS.md').read_bytes())
    print(f'Seeded and validated {len(artworks)} artworks at {destination}')


if __name__ == '__main__':
    main()
