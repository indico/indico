# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import print_function, unicode_literals

import atexit
import os
import subprocess
import sys
import time

import pywatchman
from flask.helpers import get_root_path
from werkzeug._reloader import _find_observable_paths

from indico.util.console import cformat


def _patterns_to_terms(patterns):
    return ['anyof'] + [['match', p, 'wholename', {'includedotfiles': True}] for p in patterns]


def _disable_reloader(argv):
    argv = list(argv)  # we usually pass sys.argv, so let's not modify that
    for i, arg in enumerate(argv):
        if arg == '--reloader' and argv[i + 1] == 'watchman':
            argv[i + 1] = 'none'
        elif arg.startswith('--reloader') and '=' in arg:
            argv[i] = '--reloader=none'
    return argv


class Watcher(object):
    def __init__(self, path, patterns):
        self.path = path
        self.name = path.replace('/', '-').strip('-')
        self.patterns = patterns
        self.root_dir = None
        self.triggered = False

    def start(self, client):
        query = {
            'expression': _patterns_to_terms(self.patterns),
            'fields': ['name']
        }
        watch = client.query('watch-project', self.path)
        if 'warning' in watch:
            # no idea when this happens, but the example scripts have it...
            print('watchman warning:', watch['warning'])
        self.root_dir = watch['watch']
        if 'relative_path' in watch:
            query['relative_root'] = watch['relative_path']
        # get the initial clock value so that we only get updates
        query['since'] = client.query('clock', self.root_dir)['clock']
        client.query('subscribe', self.root_dir, self.name, query)

    def consume(self, client):
        data = client.getSubscription(self.name)
        if data:
            files = sorted(f for record in data for f in record.get('files', []))
            relpath = os.path.relpath(self.path)
            if relpath == '.':
                print(cformat('%{cyan}Changes found:').format(relpath))
            else:
                print(cformat('%{cyan}Changes found in %{cyan!}{}%{reset}%{cyan}:').format(relpath))
            for f in files:
                print(cformat(' * %{blue!}{}').format(f))
            self.triggered = True

    def check(self):
        triggered = self.triggered
        self.triggered = False
        return triggered

    def __repr__(self):
        return '<Watcher({!r}, {!r})>'.format(self.path, self.patterns)


class Watchman(object):
    def __init__(self):
        self._proc = None
        self._watchers = set()
        self._client = None
        atexit.register(self._terminate)

    def run(self):
        self._client = pywatchman.client(timeout=300)
        self._client.capabilityCheck(required=['wildmatch', 'cmd-watch-project'])
        indico_project_root = os.path.realpath(os.path.join(get_root_path('indico'), '..'))
        paths = sorted({os.path.realpath(p) for p in _find_observable_paths() if os.path.exists(p)})
        for path in paths:
            patterns = ['**/*.py', '**/entry_points.txt']
            if path == indico_project_root:
                patterns += ['indico/indico.conf', 'indico/logging.yaml']
            watcher = Watcher(path, patterns)
            watcher.start(self._client)
            self._watchers.add(watcher)
        self._launch()
        self._monitor()

    def _monitor(self):
        while True:
            self._client.setTimeout(300)
            try:
                self._client.receive()
                for w in self._watchers:
                    w.consume(self._client)

                self._client.setTimeout(0.1)
                settled = False
                while not settled:
                    try:
                        self._client.receive()
                        for w in self._watchers:
                            w.consume(self._client)
                    except pywatchman.SocketTimeout:
                        settled = True
                        break

                triggered = False
                for w in self._watchers:
                    # this cannot be done with any() since all triggered watchers
                    # need to be reset during the check
                    if w.check():
                        triggered = True

                if triggered:
                    self._restart()

            except pywatchman.SocketTimeout:
                # are we still connected?
                try:
                    self._client.query('version')
                except Exception as exc:
                    print('watchman error:', exc)
                    return

            except KeyboardInterrupt:
                print()
                return

    def _launch(self, quiet=False, retry=0):
        assert not self._proc
        if not quiet and not retry:
            print(cformat('%{green!}Launching Indico'))
        try:
            argv = _disable_reloader(sys.argv)
            self._proc = subprocess.Popen(argv)
        except OSError as exc:
            delay = (retry + 1) * 0.5
            print(cformat('%{red!}Could not launch Indico: {}').format(exc))
            print(cformat('%{yellow}Retrying in {}s').format(delay))
            time.sleep(delay)
            self._launch(quiet=quiet, retry=(retry + 1))

    def _terminate(self, quiet=False):
        if not self._proc:
            return
        if not quiet:
            print(cformat('%{red!}Terminating Indico'))
        self._proc.terminate()
        self._proc = None

    def _restart(self):
        print(cformat('%{yellow!}Restarting Indico'))
        self._terminate(quiet=True)
        self._launch(quiet=True)
