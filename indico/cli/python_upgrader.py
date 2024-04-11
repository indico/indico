# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# XXX: This script will be executed standalone, outside the indico virtualenv.
# It must not use anything that's not part of the standard library of Python
# 3.12.2 (since that's the lowest version from which it may get executed).

import itertools
import os
import subprocess
import sys
from pathlib import Path
from venv import EnvBuilder


class PythonUpgrader:
    def __init__(self, venv_path: Path):
        self.venv_path = venv_path
        self.has_uwsgi = (self.venv_path / 'bin' / 'uwsgi').exists()

    def check(self):
        clear, upgrade = self._prepare()
        print(f'check mode - not performing actions ({clear=}, {upgrade=})')
        sys.exit(0)

    def upgrade(self):
        clear, upgrade = self._prepare()

        if upgrade:
            self._update_symlinks(sys.executable)

        builder = EnvBuilder(
            system_site_packages=False,
            clear=clear,
            symlinks=True,
            upgrade=upgrade,
            with_pip=True,
            upgrade_deps=True,
            prompt='indico',
        )
        builder.create(self.venv_path)
        subprocess.run([str(self.venv_path / 'bin' / 'pip'), 'install', '-U', 'wheel'], check=True)

    def reinstall_uwsgi(self):
        if not self.has_uwsgi:
            print('No uWSGI installed; reinstall not needed')
            return
        print('Rebuilding uWSGI for the current python version')
        subprocess.run([str(self.venv_path / 'bin' / 'pip'), 'install', '--force-reinstall', '--no-cache', 'uwsgi'],
                       check=True)

    def _prepare(self):
        pyenv_root = Path('~/.pyenv/').expanduser()
        pyenv_shim = pyenv_root / 'shims/python'

        if not sys.executable.startswith(str(pyenv_root)):
            # we can't run inside a virtualenv as this would result in some of the
            # symlinks pointing there instead of the actual pyenv python binaries
            if os.environ.get('_PYTHON_UPGRADER_REEXEC'):
                print(f'Still not executed via venv ({sys.executable}); aborting')
                sys.exit(1)
            print(f'Not executed via pyenv (probably inside virtualenv); re-executing with {pyenv_shim}')
            os.environ['_PYTHON_UPGRADER_REEXEC'] = '1'
            os.execl(pyenv_shim, pyenv_shim, *sys.argv)  # noqa: S606

        pyenv_global_python_version = Path('~/.pyenv/version').expanduser().read_text().strip()
        pyenv_local_python_version = subprocess.run(['pyenv', 'version-name'], capture_output=True,
                                                    encoding='utf-8').stdout.strip()
        if pyenv_global_python_version != pyenv_local_python_version:
            print(f'Warning: global pyenv version: {pyenv_global_python_version}; '
                  f'local version: {pyenv_local_python_version}')
        print(f'Python version: {".".join(map(str, sys.version_info[:3]))}; wanted: {pyenv_local_python_version}')
        print(f'Venv path: {self.venv_path}')
        config_file = self.venv_path / 'pyvenv.cfg'
        if not self.venv_path.exists() or not config_file.exists():
            print('Venv not found, creating new one')
            upgrade = False
            clear = True
        else:
            config = self._parse_venv_config(config_file)
            print(f'Venv found; python version {config["version"]} from {config["home"]}')
            if config['version'] == pyenv_local_python_version:
                print('Venv is up to date; not doing anything')
                sys.exit(0)
            if tuple(map(int, config['version'].split('.')[:2])) != sys.version_info[:2]:
                print('Venv is using a different Python 3.x version; recreating')
                clear = True
                upgrade = False
            else:
                clear = False
                upgrade = True

        return clear, upgrade

    def _parse_venv_config(self, file: Path):
        data = {}
        for line in file.read_text().splitlines():
            if '=' not in line:
                continue
            key, __, value = line.partition('=')
            key = key.strip().lower()
            value = value.strip()
            data[key] = value
        return data

    def _update_symlinks(self, python_executable):
        for file in itertools.chain([self.venv_path / 'bin' / 'python'], (self.venv_path / 'bin').glob('python3*')):
            assert file.is_symlink()
            target = file.readlink()
            if not target.is_absolute():
                # python3 and python3.x are usually symlinks to python
                continue
            print(f'Updating symlink {file} -> {python_executable}')
            file.unlink()
            file.symlink_to(python_executable)


def main():
    try:
        venv_path = Path(sys.argv[1])
        check = False
        if len(sys.argv) > 2:
            check = sys.argv[2] == '--check'
    except IndexError:
        print(f'Usage: {sys.argv[0]} VENV_PATH [--check]')
        sys.exit(1)

    upgrader = PythonUpgrader(venv_path)
    if check:
        upgrader.check()
    else:
        upgrader.upgrade()
        upgrader.reinstall_uwsgi()


if __name__ == '__main__':
    main()
