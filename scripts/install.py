"""Install/uninstall the Giants renderer on Lua-based Omarchy (no sudo)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import tempfile

from common import ROOT, prepare

MARKER = '-- BEGIN ascii-save managed renderer'


def digest(path):
    return hashlib.sha256(read(path)).hexdigest()


def read(path):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > 1024 * 1024:
            raise RuntimeError(f'Not a bounded regular file: {path}')
        data = stream.read(1024 * 1024 + 1)
        after = os.fstat(stream.fileno())
        if len(data) > 1024 * 1024 or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f'File changed during read: {path}')
        return data


def write(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.ascii-save-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            os.fchmod(stream.fileno(), mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def reload():
    subprocess.run(['hyprctl', 'reload'], check=True, capture_output=True, timeout=10)
    result = subprocess.run(['hyprctl', 'configerrors'], check=True, capture_output=True,
                            text=True, timeout=10)
    if result.stdout.strip():
        raise RuntimeError('Hyprland config errors: ' + result.stdout)


def block(override):
    # JSON string syntax is compatible with Lua for these restricted path characters.
    if any(ord(c) < 32 or ord(c) > 126 or c == ':' for c in str(override)):
        raise RuntimeError('Installation path must be printable ASCII without colons')
    return ('\n' + MARKER + '\n'
        'do\n'
        f'  local renderer = {json.dumps(str(override))}\n'
        '  local stock = (os.getenv("OMARCHY_PATH") or "/usr/share/omarchy") .. "/bin"\n'
        '  local paths = { renderer, stock }\n'
        '  for entry in (os.getenv("PATH") or "/usr/local/bin:/usr/bin"):gmatch("[^:]+") do\n'
        '    if entry ~= renderer and entry ~= stock then table.insert(paths, entry) end\n'
        '  end\n'
        '  hl.env("PATH", table.concat(paths, ":"))\n'
        'end\n'
        '-- END ascii-save managed renderer\n')


def install(home, activate=True):
    home = home.resolve()
    destination = home / '.local/share/ascii-save'
    state_path = home / '.local/state/ascii-save/install.json'
    config = (home / '.config/hypr/hyprland.lua').resolve(strict=True)
    original = read(config)
    if state_path.exists():
        state = json.loads(read(state_path))
        if state['block'].encode() not in original:
            raise RuntimeError('Managed configuration changed; preserve it and resolve manually')
        if any(not (destination / p).is_file() or digest(destination / p) != h
               for p, h in state['files'].items()):
            raise RuntimeError('Installed files changed; preserve them and resolve manually')
        print('Giants is already installed. Uninstall before installing an updated version.')
        return
    if destination.exists() or destination.is_symlink() or MARKER.encode() in original:
        raise RuntimeError('Unmanaged installation or configuration exists; refusing to overwrite')
    if b'require("default.hypr.omarchy")' not in original:
        raise RuntimeError('This installer requires Omarchy with Lua Hyprland configuration')
    if activate:
        for tool in ('hyprctl', 'ttfx', 'python3'):
            if not shutil.which(tool):
                raise RuntimeError(f'Missing dependency: {tool}')
        launcher = Path(os.environ.get('OMARCHY_PATH', '/usr/share/omarchy')) / 'bin/omarchy-launch-screensaver'
        if 'hl.dsp.exec_cmd' not in launcher.read_text():
            raise RuntimeError('Unsupported launcher: requires compositor dispatch environment')
        reload()  # Refuse to add changes on top of an already broken config.
    managed = block(destination / 'overrides')
    mode = stat.S_IMODE(config.stat().st_mode)
    backup = state_path.parent / 'hyprland.lua.before-install'
    write(backup, original)
    created = False
    try:
        destination.mkdir(parents=True, mode=0o700)
        created = True
        files = ['scripts/native.py', 'scripts/common.py',
                 'reference/omarchy/bin/omarchy-screensaver-prepare',
                 'reference/omarchy/LICENSE', 'LICENSE']
        for name in files:
            write(destination / name, read(ROOT / name))
        # Validate before activating; install the same bounded private snapshot.
        with prepare(ROOT / 'examples/giants-refined') as artworks:
            for art in artworks:
                write(destination / 'examples/giants-refined' / art.name, read(art))
        for name in ('ARTWORK-NOTICE.md', 'SOURCE-CREDITS.md', 'manifest.json', 'README.md'):
            write(destination / 'examples/giants-refined' / name,
                  read(ROOT / 'examples/giants-refined' / name))
        wrapper = '#!/bin/sh\nexec /usr/bin/python3 -B ' + shlex.quote(str(destination / 'scripts/native.py')) + '\n'
        write(destination / 'overrides/omarchy-screensaver', wrapper.encode(), 0o700)
        hashes = {str(p.relative_to(destination)): digest(p) for p in destination.rglob('*') if p.is_file()}
        state = {'config': str(config), 'block': managed, 'files': hashes}
        if read(config) != original:
            raise RuntimeError('Config changed during installation')
        write(config, original + managed.encode(), mode)
        if activate:
            reload()
        write(state_path, json.dumps(state, indent=2).encode())
    except BaseException:
        current = read(config)
        if current == original + managed.encode():
            write(config, original, mode)
        if created:
            shutil.rmtree(destination)
        if activate:
            reload()
        raise
    print('Installed Giants: all 18 artworks, ordered repeat, full random ttfx suite.')


def uninstall(home, activate=True):
    home = home.resolve()
    destination = home / '.local/share/ascii-save'
    state_path = home / '.local/state/ascii-save/install.json'
    if not state_path.exists():
        print('No managed installation.')
        return
    state = json.loads(read(state_path))
    config = Path(state['config'])
    current = read(config)
    managed = state['block'].encode()
    if current.count(managed) != 1:
        raise RuntimeError('Managed block was edited; preserving configuration and installation')
    mode = stat.S_IMODE(config.stat().st_mode)
    write(config, current.replace(managed, b'', 1), mode)
    try:
        if activate:
            reload()
    except BaseException:
        write(config, current, mode)
        if activate:
            reload()
        raise
    preserved = []
    for name, expected in state['files'].items():
        path = destination / name
        try:
            if digest(path) == expected:
                path.unlink()
            else:
                preserved.append(name)
        except FileNotFoundError:
            pass
        except (OSError, RuntimeError):
            preserved.append(name)
    for path in sorted(destination.rglob('*'), reverse=True):
        if path.is_dir() and not path.is_symlink():
            try:
                path.rmdir()
            except OSError:
                pass
    try:
        destination.rmdir()
    except OSError:
        pass
    state_path.unlink()
    print('Stock renderer restored. Original config backup retained at ' + str(state_path.parent))
    if preserved:
        print('Preserved modified files: ' + ', '.join(preserved))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'uninstall'])
    args = parser.parse_args()
    try:
        (install if args.action == 'install' else uninstall)(Path.home())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, str(error) + '\n')
