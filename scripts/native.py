"""Giants renderer for Omarchy's existing screensaver terminal and idle service."""
import itertools
import json
import os
from pathlib import Path
import select
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import termios
import time
import tty

from common import ROOT, prepare

DOTS = ((1, 8), (2, 16), (4, 32), (64, 128))


def fit(text, columns, rows):
    """Downsample braille dots uniformly; never crop a portrait to the viewport."""
    lines = text.splitlines()
    width, height = max(map(len, lines)), len(lines)
    scale = min(1, max(1, columns - 2) / width, max(1, rows - 2) / height)
    if scale == 1:
        return text
    if any(c != ' ' and not '\u2800' <= c <= '\u28ff' for line in lines for c in line):
        return 'OMARCHY\n'  # Do not truncate arbitrary wide text into misleading fragments.
    out_w, out_h = max(1, int(width * scale)), max(1, int(height * scale))
    result = []
    for y in range(out_h):
        row = []
        for x in range(out_w):
            value = 0
            for dy in range(4):
                for dx in range(2):
                    sy = min(height * 4 - 1, int((y * 4 + dy) * height / out_h))
                    sx = min(width * 2 - 1, int((x * 2 + dx) * width / out_w))
                    line = lines[sy // 4]
                    c = line[sx // 2] if sx // 2 < len(line) else ' '
                    bits = ord(c) - 0x2800 if c != ' ' else 0
                    if bits & DOTS[sy % 4][sx % 2]:
                        value |= DOTS[dy][dx]
            row.append(chr(0x2800 + value))
        result.append(''.join(row))
    return '\n'.join(result) + '\n'


def command(art):
    return ['ttfx', '-i', str(art), '--frame-rate', '120', '--canvas-width', '0',
            '--canvas-height', '0', '--anchor-canvas', 'c', '--anchor-text', 'c',
            '--reuse-canvas', '--no-eol', '--no-restore-cursor', '--random-effect']


def hypr(*args):
    try:
        return subprocess.run(['hyprctl', *args], capture_output=True, text=True,
                              timeout=1, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None


def stop(child):
    if child is not None and child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


class Dismissed(Exception):
    pass


def main():
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return 1
    old = termios.tcgetattr(sys.stdin)
    child = None
    bus = None
    endpoint = None
    state = None
    def terminate(*_):
        raise Dismissed()
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
        signal.signal(sig, terminate)
    try:
        tty.setcbreak(sys.stdin.fileno())
        print('\033]11;rgb:00/00/00\007\033[?25l', end='', flush=True)
        hypr('eval', 'hl.config({ cursor = { invisible = true } })')
        # Private datagrams coordinate dismissal without matching/killing processes.
        directory = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / 'ascii-save'
        try:
            directory.mkdir(mode=0o700, exist_ok=True)
            info = directory.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise OSError('unsafe runtime directory')
            endpoint = directory / f'{os.getpid()}-{os.urandom(4).hex()}.sock'
            bus = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            bus.bind(str(endpoint))
            bus.setblocking(False)
            state = endpoint.with_suffix('.json')
        except OSError:
            if bus:
                bus.close()
            bus = None
        started = time.monotonic()
        focused = False
        cursor = None
        next_check = 0

        def dismiss_all():
            if bus:
                for peer in itertools.islice(directory.glob('*.sock'), 128):
                    try:
                        bus.sendto(b'dismiss', str(peer))
                    except OSError:
                        pass
            raise Dismissed()

        def wait(seconds):
            nonlocal focused, cursor, next_check
            until = time.monotonic() + seconds
            while time.monotonic() < until:
                ready = select.select([sys.stdin] + ([bus] if bus else []), [], [], 0.1)[0]
                if sys.stdin in ready:
                    os.read(sys.stdin.fileno(), 1)
                    dismiss_all()
                if bus in ready and bus.recv(32) == b'dismiss':
                    raise Dismissed()
                now = time.monotonic()
                if now < next_check:
                    continue
                next_check = now + 0.5
                try:
                    window = json.loads(hypr('activewindow', '-j') or 'null')
                    if isinstance(window, dict) and window.get('class') == 'org.omarchy.screensaver':
                        focused = True
                    elif focused and isinstance(window, dict) and window.get('class'):
                        dismiss_all()
                    position = json.loads(hypr('cursorpos', '-j') or 'null')
                    if now - started > 2 and isinstance(position, dict):
                        if cursor is not None and position != cursor:
                            dismiss_all()
                        cursor = position
                except (ValueError, TypeError):
                    pass  # IPC failure is not evidence of user dismissal.

        with tempfile.TemporaryDirectory(prefix='ascii-save-native-') as scratch:
            target = Path(scratch) / 'frame.txt'
            try:
                with prepare(ROOT / 'examples/giants-refined') as paths:
                    artworks = [(p.name, p.read_text()) for p in paths]
            except (OSError, subprocess.SubprocessError):
                artworks = [('fallback', 'OMARCHY\n')]
            if not artworks:
                artworks = [('fallback', 'OMARCHY\n')]
            while os.get_terminal_size() == (80, 24) and time.monotonic() - started < 2:
                wait(0.05)
            for sequence, (name, text) in enumerate(itertools.cycle(artworks)):
                # Failures leave this terminal alive: idle/lock timers still apply.
                while True:
                    try:
                        size = os.get_terminal_size()
                        target.write_text(fit(text, size.columns, size.lines))
                        if state:
                            state.write_text(json.dumps({'pid': os.getpid(), 'sequence': sequence,
                                'artwork': name, 'count': len(artworks), 'columns': size.columns,
                                'rows': size.lines, 'effects': 'full random suite'}))
                        print('\033[2J\033[H', end='', flush=True)
                        child = subprocess.Popen(command(target), stdin=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL)
                        while child.poll() is None:
                            wait(0.1)
                        success = child.returncode == 0
                        child = None
                        if success:
                            break
                    except OSError:
                        stop(child)
                        child = None
                    wait(1)
    except Dismissed:
        return 0
    except (OSError, subprocess.SubprocessError):
        # Even scratch/setup failures must not look like user dismissal to idle.
        try:
            while not select.select([sys.stdin], [], [], 0.5)[0]:
                pass
        except Dismissed:
            pass
        return 0
    finally:
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
            signal.signal(sig, signal.SIG_IGN)
        stop(child)
        if bus:
            bus.close()
        if endpoint:
            endpoint.unlink(missing_ok=True)
        if state:
            state.unlink(missing_ok=True)
        hypr('eval', 'hl.config({ cursor = { invisible = false } })')
        try:
            termios.tcsetattr(sys.stdin, termios.TCSANOW, old)
            print('\033[0m\033[?25h', end='', flush=True)
        except (OSError, termios.error):
            pass


if __name__ == '__main__':
    raise SystemExit(main())
