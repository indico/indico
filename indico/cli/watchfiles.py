# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import atexit
import functools
import importlib
import os
import re
import subprocess
import sys
import time
from collections import ChainMap
from itertools import chain
from pathlib import Path

import click
from flask.helpers import get_root_path
from watchfiles import DefaultFilter, watch
from werkzeug._reloader import _find_watchdog_paths

from indico.util.console import cformat


def _disable_reloader(argv):
    argv = list(argv)  # we usually pass sys.argv, so let's not modify that
    for i, arg in enumerate(argv):
        if arg == '--reloader' and argv[i + 1] == 'watchfiles':
            argv[i + 1] = 'none'
            break
        elif arg.startswith('--reloader='):
            argv[i] = '--reloader=none'
            break
        elif arg == '--watchfiles':
            del argv[i]
            break
    else:
        argv += ['--reloader', 'none']
    return argv


class IndicoFilter(DefaultFilter):
    PYTHON_SUFFIXES = ('.py', '.pyx', '.pyd', '/entry_points.txt')

    def __init__(self, indico_config_paths):
        self.indico_config_paths = {str(x) for x in indico_config_paths}
        ignore_dirs = set(super().ignore_dirs) - {'site-packages'}
        super().__init__(ignore_dirs=ignore_dirs)

    def __call__(self, change, path):
        if path in self.indico_config_paths:
            # config paths are exact matches on full paths so we can always
            # succeed there; no need to check blacklisted paths etc
            return True
        elif not path.endswith(self.PYTHON_SUFFIXES):
            # anything that's not python-related doesn't matter
            return False

        # for indico itself we no longer have a build dir since hatchling does not create one,
        # but for plugins we simply consider any build dir adjacent to a pyproject.toml irrelevant.
        # it would be nice if no plugins used setuptools to make this unnecessary, but unfortunately
        # we don't have control over which build backend other people use
        if '/build/' in path or path.endswith('/build'):
            path_obj = Path(path)
            if (list(path_obj.parents)[-path_obj.parts.index('build')] / 'pyproject.toml').exists():
                return False

        return super().__call__(change, path)


def _get_editable_package_dirs():
    # XXX not using `ast` to parse the import from the pth file since it's way easier with a simple regex
    mappings = [
        importlib.import_module(m.group(1)).MAPPING
        for f in list(chain.from_iterable(Path(p).glob('__editable__.*.pth') for p in sys.path))
        if (m := re.search(r'import (__editable___\S+_finder)', f.read_text()))
    ]
    return {Path(x).parent for x in set(ChainMap(*mappings).values())}


class Watchfiles:
    def __init__(self):
        self._proc = None
        self._paths = set()
        atexit.register(self._terminate)

    def run(self):
        indico_root_path = Path(get_root_path('indico')).parent
        editable_paths = _get_editable_package_dirs()
        paths = {Path(os.path.realpath(p)) for p in _find_watchdog_paths(editable_paths, set()) if os.path.exists(p)}
        if env_config_string := os.environ.get('INDICO_CONFIG'):
            env_config = Path(env_config_string).expanduser()
            if env_config.parent.exists():
                paths.add(env_config.parent)
            indico_config_paths = {env_config, env_config.parent / 'logging.yaml'}
        else:
            indico_project_root = indico_root_path / 'indico'
            indico_config_paths = {indico_project_root / 'indico.conf', indico_project_root / 'logging.yaml'}

        self._paths = sorted(paths)
        watcher = watch(*paths, watch_filter=IndicoFilter(indico_config_paths))
        self._launch()
        for changes in watcher:
            self._print_changes(changes)
            self._restart()

    @functools.cache  # noqa: B019
    def _get_root(self, path):
        return next((p for p in self._paths if path.is_relative_to(p)), None)

    def _print_changes(self, changes):
        files = {Path(x[1]) for x in changes}
        # sort but keep priority on indico paths in case we really have multiple roots...
        files = sorted(files, key=lambda x: (not str(x).startswith(os.getcwd()), x))
        # ...because this is a bit hacky as we assume that usually all files are from a single root
        root = os.path.relpath(self._get_root(files[0].parent))
        if root == '.':
            click.secho('Changes found:', fg='cyan')
        else:
            print(cformat('%{cyan}Changes found in %{cyan!}{}%{reset}%{cyan}:').format(root))
        for f in files:
            rel = os.path.relpath(f, root)
            print(cformat(' * %{blue!}{}').format(rel))

    def _launch(self, quiet=False, retry=0):
        assert not self._proc
        if not quiet and not retry:
            click.secho('Launching Indico', fg='green', bold=True)
        try:
            argv = _disable_reloader(sys.argv)
            self._proc = subprocess.Popen(argv)
        except OSError as exc:
            delay = (retry + 1) * 0.5
            click.secho(f'Could not launch Indico: {exc}', fg='red', bold=True)
            click.secho(f'Retrying in {delay}s', fg='yellow')
            time.sleep(delay)
            self._launch(quiet=quiet, retry=(retry + 1))

    def _terminate(self, quiet=False):
        if not self._proc:
            return
        if not quiet:
            click.secho('Terminating Indico', fg='red', bold=True)
        self._proc.terminate()
        self._proc = None

    def _restart(self):
        click.secho('Restarting Indico', fg='yellow', bold=True)
        self._terminate(quiet=True)
        self._launch(quiet=True)
