# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
import redis
from collections import OrderedDict

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
    def from_file(cls, client, filename, name=None):
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
            return cls(client, name, metadata, f.read())

    @classmethod
    def load_directory(cls, client, path='.'):
        """Load scripts from the given directory.

        Scripts must have a .lua extension and will be named like the file."""
        scripts = {}
        for filename in glob.iglob(os.path.join(path, '*.lua')):
            script = cls.from_file(client, filename)
            scripts[script.name] = script
        return scripts

    def __init__(self, client, name, metadata, code):
        self.name = name
        self._check_metadata(metadata)
        self._script = client.register_script(code)

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
        if isinstance(client, redis.client.BasePipeline) and self._process_result:
            raise ValueError('Script with result conversion cannot be called on a pipeline')
        res = self._script(args=args, client=client)
        return self._process_result(res) if self._process_result else res

    def __repr__(self):
        return '<RedisScript(%s, %d arguments)>' % (self.name, self._args)


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