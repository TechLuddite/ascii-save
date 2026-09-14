"""Record a ttfx effect on an artwork into an asciicast v2 file with real timestamps.

Runs ttfx in a pseudo-terminal of the requested size, exactly as the
screensaver terminal would, and writes each output chunk with the time it was
produced. A cap stops long effects so a full set can be recorded in minutes.

usage: record.py OUT.cast ARTWORK EFFECT [--cols 137 --rows 36 --cap 120]
"""
import argparse
import fcntl
import json
import os
import pty
import select
import struct
import sys
import termios
import time


def record(out, artwork, effect, cols=137, rows=36, cap=120.0):
    cmd = ['ttfx', '-i', str(artwork), '--existing-color-handling', 'dynamic',
           '--frame-rate', '120', '--canvas-width', '0', '--canvas-height', '0',
           '--anchor-canvas', 'c', '--anchor-text', 'c', '--no-eol', effect]
    pid, fd = pty.fork()
    if pid == 0:
        os.environ['TERM'] = 'foot'
        os.environ['COLORTERM'] = 'truecolor'
        os.execvp(cmd[0], cmd)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
    start = time.time()
    capped = False
    total = 0
    pending = b''
    with open(out, 'w', encoding='utf-8') as f:
        f.write(json.dumps({'version': 2, 'width': cols, 'height': rows, 'timestamp': int(start),
                            'command': ' '.join(cmd)}) + '\n')
        while True:
            ready, _, _ = select.select([fd], [], [], 0.25)
            if ready:
                try:
                    data = os.read(fd, 1 << 16)
                except OSError:
                    break
                if not data:
                    break
                pending += data
                try:
                    text = pending.decode('utf-8')
                    pending = b''
                except UnicodeDecodeError as err:
                    text = pending[:err.start].decode('utf-8')
                    pending = pending[err.start:]
                if text:
                    f.write(json.dumps([round(time.time() - start, 4), 'o', text]) + '\n')
                    total += len(text)
            else:
                done, _ = os.waitpid(pid, os.WNOHANG)
                if done:
                    break
            if time.time() - start > cap:
                capped = True
                os.kill(pid, 15)
                time.sleep(0.3)
                try:
                    os.kill(pid, 9)
                except ProcessLookupError:
                    pass
                break
    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass
    os.close(fd)
    meta = {'effect': effect, 'artwork': os.path.basename(str(artwork)), 'cols': cols, 'rows': rows,
            'seconds': round(time.time() - start, 1), 'capped': capped, 'bytes': total}
    with open(out + '.meta.json', 'w') as f:
        json.dump(meta, f)
    return meta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('out')
    ap.add_argument('artwork')
    ap.add_argument('effect')
    ap.add_argument('--cols', type=int, default=137)
    ap.add_argument('--rows', type=int, default=36)
    ap.add_argument('--cap', type=float, default=120)
    a = ap.parse_args()
    meta = record(a.out, a.artwork, a.effect, a.cols, a.rows, a.cap)
    print(f"{a.out}: {meta['seconds']}s capped={meta['capped']} bytes={meta['bytes']}", file=sys.stderr)


if __name__ == '__main__':
    main()
