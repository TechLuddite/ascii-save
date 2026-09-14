"""Private playback snapshots using the pinned upstream preparer."""
from contextlib import contextmanager
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COLLECTION = ROOT / 'examples/giants'
PREPARER = ROOT / 'reference/omarchy/bin/omarchy-screensaver-prepare'
# Same rules as the pinned preparer, plus SGR colour pass-through for colour collections.
COLOR_PREPARER = ROOT / 'scripts/omarchy-screensaver-prepare-color'


@contextmanager
def prepare(source, preparer=PREPARER):
    with tempfile.TemporaryDirectory(prefix='ascii-save-') as directory:
        source = Path(source).expanduser().absolute()
        subprocess.run(['bash', str(preparer), str(source), directory],
                       check=True, timeout=5, capture_output=True)
        yield sorted(Path(directory).glob('*.txt'))
