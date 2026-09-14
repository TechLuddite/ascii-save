"""Validate a collection without launching a terminal or changing config."""
import argparse
import subprocess
import sys
from common import COLOR_PREPARER, DEFAULT_COLLECTION, PREPARER, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', default=str(DEFAULT_COLLECTION))
    parser.add_argument('--color', action='store_true',
                        help='validate with the colour preparer, which passes SGR colour through')
    args = parser.parse_args()
    try:
        with prepare(args.source, COLOR_PREPARER if args.color else PREPARER) as files:
            print(f'{len(files)} playable artworks; snapshot validation passed.')
    except (OSError, subprocess.SubprocessError) as error:
        detail = getattr(error, 'stderr', b'')
        print(detail.decode(errors='replace') if detail else str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
