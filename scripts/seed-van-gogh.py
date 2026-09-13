"""Regenerate the pinned Van Gogh collection from locally downloaded museum JPEGs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

from common import ROOT, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sources', type=Path, help='directory containing the museum object-ID JPEGs')
    parser.add_argument('--output', type=Path, default=ROOT / 'collections/van-gogh-regenerated')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'examples/van-gogh/manifest.json').read_text())
    destination = args.output.expanduser().absolute()
    if destination.exists():
        parser.error('output must not exist; generate into a new directory before comparing')
    sources = args.sources.expanduser().resolve()
    # Pin the directory and snapshot bounded regular files before image decoding.
    directory = os.open(sources, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with tempfile.TemporaryDirectory(prefix='ascii-save-van-gogh-') as temporary:
            work = Path(temporary)
            converted = work / 'converted'
            converted.mkdir()
            for art in manifest['artworks']:
                name = art['source']
                if not re.fullmatch(r'[0-9]+\.jpg', name) or not re.fullmatch(r'[0-9]{2}-[a-z-]+\.txt', art['output']):
                    raise ValueError('invalid manifest filename')
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                with os.fdopen(fd, 'rb') as source:
                    before = os.fstat(source.fileno())
                    if not stat.S_ISREG(before.st_mode) or before.st_size > 12_000_000:
                        raise ValueError(f'{name}: expected a regular JPEG under 12 MB')
                    data = source.read(12_000_001)
                    after = os.fstat(source.fileno())
                if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                    raise ValueError(f'{name}: source changed while reading')
                if hashlib.sha256(data).hexdigest() != art['source_sha256']:
                    raise ValueError(f'{name}: source hash differs from the pinned museum image')
                snapshot = work / name
                snapshot.write_bytes(data)
                output = converted / art['output']
                settings = manifest['conversion']
                subprocess.run(['omarchy', 'transcode', 'ascii', str(snapshot), str(output),
                                '--width', str(settings['width']), '--height', str(settings['height']),
                                '--threshold', str(settings['threshold']), '--no-trim'],
                               check=True, capture_output=True, timeout=60,
                               env=dict(os.environ, MAGICK_THREAD_LIMIT='2'))
                output.write_text(output.read_text(encoding='utf-8') + '\n' + art['caption'] + '\n', encoding='utf-8')
                if hashlib.sha256(output.read_bytes()).hexdigest() != art['output_sha256']:
                    raise ValueError(f'{name}: conversion differs; check converter and ImageMagick versions')
            with prepare(converted) as files:
                if len(files) != len(manifest['artworks']):
                    raise ValueError('not all artworks passed playback validation')
            # No destination is created until every input and conversion passes.
            destination.mkdir(parents=True)
            for source in sorted(converted.iterdir()):
                (destination / source.name).write_bytes(source.read_bytes())
            (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    finally:
        os.close(directory)
    print(f'Regenerated and validated {len(manifest["artworks"])} artworks at {destination}')


if __name__ == '__main__':
    main()
