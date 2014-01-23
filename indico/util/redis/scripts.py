# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import glob
import os
import re
from collections import OrderedDict
from MaKaC.common.logger import Logger

import indico.util.json as json


class RedisScript(object):
    """Wrapper for redis scripts.

    Makes passing arguments more comfortable and allows result conversion.
    """

    RESULT_PROCESSORS = {
        'json': json.loads,
        'json_odict': lambda x: OrderedDict(json.loads(x))
    }

    @classmethod
    def from_file(cls, client, filename, name=None, _broken=False):
        """Load script and metadata from a file.

        Metadata syntax: comma-separated key=value pairs in the first line.
        """
        if not name:
            name = os.path.splitext(os.path.basename(filename))[0]
        with open(filename) as f:
            metadata_line = f.readline().strip().lstrip('- \t')
            try:
                metadata = dict(re.search(r'(\S+)=(\S+)', item).groups() for item in metadata_line.split(','))
            except AttributeError:
                raise ValueError('Invalid metadata line: %s' % metadata_line)
            return cls(client, name, metadata, f.read(), _broken)

    @classmethod
    def load_directory(cls, client, path='.'):
        """Load scripts from the given directory.

        Scripts must have a .lua extension and will be named like the file."""
        scripts = {}
        failed = False
        for filename in glob.iglob(os.path.join(path, '*.lua')):
            # If one script fails to laod because of a ConnectionError we don't even try
            # to load other scripts to avoid long timeouts
            script = cls.from_file(client, filename, _broken=failed)
            failed = script.broken
            scripts[script.name] = script
        return scripts

    def __init__(self, client, name, metadata, code, _broken=False):
        self.broken = False
        self.name = name
        self._check_metadata(metadata)
        if _broken:
            # If we already know that redis is broken we can keep things fast
            # by not even trynig to send the script to redis
            self._script = _BrokenScript(name, client)
            self.broken = True
            return
        from indico.util.redis import ConnectionError
        try:
            self._script = client.register_script(code)
        except ConnectionError:
            Logger.get('redis').exception('Could not load script %s' % name)
            self._script = _BrokenScript(name, client)
            self.broken = True

    def _check_metadata(self, metadata):
        result_type = metadata.get('result')
        self._process_result = self.RESULT_PROCESSORS[result_type] if result_type else None
        self._args = int(metadata.get('args', 0))
        if self._args < 0:
            raise ValueError('Argument count cannot be negative')

    def __call__(self, *args, **kwargs):
        """Execute the script"""
        if len(args) != self._args:
            raise TypeError('Script takes exactly %d argument (%d given)' % (self._args, len(args)))
        client = kwargs.get('client', self._script.registered_client)
        import redis
        if isinstance(client, redis.client.BasePipeline) and self._process_result:
            raise ValueError('Script with result conversion cannot be called on a pipeline')
        try:
            res = self._script(args=args, client=client)
        except redis.RedisError, e:
            # If we are not on a pipeline and the execution fails, log it with arguments
            Logger.get('redis').exception('Executing %s(%r) failed', self.name, args)
            return None
        if isinstance(self._script, _BrokenScript):
            # If we "called" a broken script it logged itself being broken but we need to bail out early
            return None
        return self._process_result(res) if self._process_result else res

    def __repr__(self):
        return '<RedisScript(%s, %d arguments)>' % (self.name, self._args)


class _BrokenScript(object):
    def __init__(self, name, client):
        self.name = name
        self.registered_client = client

    def __call__(self, args, client):
        Logger.get('redis').error('Tried to call unavailable redis script: %s(%r)', self.name, args)


class LazyScriptLoader(object):
    def __init__(self, client, script_dir):
        self._scripts = None
        self._client = client
        self._script_dir = script_dir

    def __getattr__(self, item):
        if self._scripts is None:
            self._load_scripts()
        try:
            return self._scripts[item]
        except KeyError:
            raise AttributeError(item)

    def flush(self):
        """Remove all scripts (locally) to force a reload."""
        self._scripts = None

    def _load_scripts(self):
        self._scripts = RedisScript.load_directory(self._client, self._script_dir)
