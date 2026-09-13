import importlib.util
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import native
spec = importlib.util.spec_from_file_location('installer', ROOT / 'scripts/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class NativeTests(unittest.TestCase):
    def test_fit_all_giants(self):
        for path in (ROOT / 'examples/giants-refined').glob('*.txt'):
            fitted = native.fit(path.read_text(), 100, 30)
            self.assertNotEqual(fitted, 'OMARCHY\n', path.name)
            self.assertLessEqual(len(fitted.splitlines()), 28)
            self.assertLessEqual(max(map(len, fitted.splitlines())), 98)
        self.assertEqual(native.fit('\u28ff\u28ff\n' * 2, 3, 3), '\u28ff\n')
        self.assertIn('--random-effect', native.command(Path('art')))
        self.assertNotIn('highlight', native.command(Path('art')))

    def test_install_uninstall_symlink_preserves_other_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / '.config/hypr/hyprland.lua'
            config.parent.mkdir(parents=True)
            target = home / 'dotfile.lua'
            original = b'require("default.hypr.omarchy")\n'
            target.write_bytes(original)
            config.symlink_to(target)
            installer.install(home, activate=False)
            installer.install(home, activate=False)
            target.write_bytes(target.read_bytes() + b'-- user edit\n')
            modified = home / '.local/share/ascii-save/scripts/native.py'
            modified.write_text('# user modification\n')
            installer.uninstall(home, activate=False)
            installer.uninstall(home, activate=False)
            self.assertTrue(config.is_symlink())
            self.assertEqual(target.read_bytes(), original + b'-- user edit\n')
            self.assertEqual(modified.read_text(), '# user modification\n')

    def test_reload_failure_rolls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / '.config/hypr/hyprland.lua'
            config.parent.mkdir(parents=True)
            original = b'require("default.hypr.omarchy")\n'
            config.write_bytes(original)
            stock = home / 'stock/bin'
            stock.mkdir(parents=True)
            (stock / 'omarchy-launch-screensaver').write_text('hl.dsp.exec_cmd')
            with patch.dict(os.environ, {'OMARCHY_PATH': str(stock.parent)}), \
                 patch.object(installer.shutil, 'which', return_value='/usr/bin/true'), \
                 patch.object(installer, 'reload', side_effect=[None, RuntimeError('bad config'), None]):
                with self.assertRaises(RuntimeError):
                    installer.install(home)
            self.assertEqual(config.read_bytes(), original)
            self.assertFalse((home / '.local/share/ascii-save').exists())

    def test_native_wrap_failure_and_owned_cleanup(self):
        # Real PTY/child lifecycle; fake compositor and ttfx never reach desktop.
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / 'hyprctl').write_text('#!/bin/sh\nexit 1\n')
            (work / 'ttfx').write_text('''#!/usr/bin/python3
import hashlib, os, pathlib, sys, time
log = pathlib.Path(os.environ['TEST_LOG'])
with log.open('a') as out:
    out.write(hashlib.sha256(pathlib.Path(sys.argv[sys.argv.index('-i')+1]).read_bytes()).hexdigest() + '\\n')
if len(log.read_text().splitlines()) >= 20:
    sys.exit(1)
time.sleep(.02)
''')
            for name in ('hyprctl', 'ttfx'):
                (work / name).chmod(0o700)
            master, slave = pty.openpty()
            import fcntl, struct, termios
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 30, 100, 0, 0))
            env = dict(os.environ, PATH=str(work) + ':' + os.environ['PATH'],
                       XDG_RUNTIME_DIR=str(work), TEST_LOG=str(work / 'log'))
            unrelated = subprocess.Popen(['sleep', '30'])
            process = subprocess.Popen([sys.executable, str(ROOT / 'scripts/native.py')],
                                       stdin=slave, stdout=slave, stderr=slave, env=env)
            os.close(slave)
            try:
                deadline = time.monotonic() + 15
                records = []
                while time.monotonic() < deadline:
                    if select.select([master], [], [], .1)[0]:
                        os.read(master, 65536)
                    records = list((work / 'ascii-save').glob('*.json'))
                    if records:
                        import json
                        if json.loads(records[0].read_text())['sequence'] >= 19:
                            break
                self.assertTrue(records)
                import json
                self.assertGreaterEqual(json.loads(records[0].read_text())['sequence'], 19)
                time.sleep(1.2)
                self.assertIsNone(process.poll(), 'render failure must leave the window alive')
                entries = (work / 'log').read_text().splitlines()
                self.assertEqual(entries[0], entries[18])
                self.assertNotEqual(entries[0], entries[1])
                os.write(master, b'x')
                process.wait(timeout=5)
                self.assertEqual(process.returncode, 0)
                self.assertIsNone(unrelated.poll())
                self.assertFalse(list((work / 'ascii-save').iterdir()))
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait()
                unrelated.terminate()
                unrelated.wait()
                os.close(master)
