"""Preview ASCII collections in this terminal; any key exits."""
import argparse
import select
import shutil
import signal
import subprocess
import sys
import termios
import time
import tty
from common import DEFAULT_COLLECTION, prepare


class Dismissed(Exception):
    pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', default=str(DEFAULT_COLLECTION))
    parser.add_argument('--seconds', type=float, default=60, help='total preview duration (1–3600)')
    parser.add_argument('--effect', choices=['highlight', 'random'], default='highlight')
    args = parser.parse_args()
    if not 1 <= args.seconds <= 3600:
        parser.error('--seconds must be between 1 and 3600')
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.error('run the preview in a terminal; use validate.py for headless checks')
    renderer = shutil.which('ttfx')
    if not renderer:
        parser.error('ttfx is required for animation')

    def dismiss(*_):
        raise Dismissed()

    def pause_until(deadline):
        while time.monotonic() < deadline:
            if select.select([sys.stdin], [], [], max(0, min(0.1, deadline - time.monotonic())))[0]:
                sys.stdin.read(1)
                raise Dismissed()

    child = None
    entered_screen = False
    old_terminal = termios.tcgetattr(sys.stdin)
    old_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
    try:
        for sig in old_handlers:
            signal.signal(sig, dismiss)
        with prepare(args.source) as artworks:
            tty.setcbreak(sys.stdin.fileno())
            print('\033[?1049h\033[?25l', end='', flush=True)
            entered_screen = True
            deadline = time.monotonic() + args.seconds
            while time.monotonic() < deadline:
                for art in artworks:
                    print('\033[2J\033[H', end='', flush=True)
                    command = [renderer, '-i', str(art), '--frame-rate', '30', '--canvas-width', '0',
                               '--canvas-height', '0', '--anchor-canvas', 'c', '--anchor-text', 'c',
                               '--reuse-canvas', '--no-eol', '--no-restore-cursor']
                    if args.effect == 'highlight':
                        command += ['highlight', '--final-gradient-stops', '97786d', 'E1D5C2',
                                    '--highlight-brightness', '1.3']
                    else:
                        command += ['--random-effect']
                    child = subprocess.Popen(command, stdin=subprocess.DEVNULL)
                    while child.poll() is None and time.monotonic() < deadline:
                        pause_until(min(time.monotonic() + 0.1, deadline))
                    if time.monotonic() >= deadline:
                        return 0
                    if child.returncode:
                        raise RuntimeError(f'ttfx exited with status {child.returncode}')
                    child = None
                    pause_until(min(time.monotonic() + 2, deadline))
                    if time.monotonic() >= deadline:
                        break
    except Dismissed:
        return 0
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        # Terminate only the renderer this preview started, never other ttfx jobs.
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_terminal)
        if entered_screen:
            print('\033[0m\033[?25h\033[?1049l', end='', flush=True)
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
