# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.


import logging
import os
import re
import sys
import tempfile

import py


# Ignore config file in case there is one
os.environ['INDICO_CONFIG'] = os.devnull

pytest_plugins = ('indico.testing.fixtures.app', 'indico.testing.fixtures.category',
                  'indico.testing.fixtures.contribution', 'indico.testing.fixtures.database',
                  'indico.testing.fixtures.disallow', 'indico.testing.fixtures.person', 'indico.testing.fixtures.user',
                  'indico.testing.fixtures.event', 'indico.testing.fixtures.smtp', 'indico.testing.fixtures.util')


def pytest_configure(config):
    from indico.core.config import Config
    from indico.core.logger import Logger
    # Load all the plugins defined in pytest_plugins
    config.pluginmanager.consider_module(sys.modules[__name__])
    config.indico_temp_dir = py.path.local(tempfile.mkdtemp(prefix='indicotesttmp.'))
    plugins = filter(None, [x.strip() for x in re.split(r'[\s,;]+', config.getini('indico_plugins'))])
    # Throw away all indico.conf options early
    Config.getInstance().reset({
        'SmtpServer': ('localhost', 0),  # invalid port - just in case so we NEVER send emails!
        'CacheBackend': 'null',
        'Loggers': [],
        'TempDir': config.indico_temp_dir.strpath,
        'CacheDir': config.indico_temp_dir.strpath,
        'StorageBackends': {'default': config.indico_temp_dir},
        'AttachmentStorage': 'default',
        'Plugins': plugins,
        'SecretKey': os.urandom(16)
    })
    # Make sure we don't write any log files (or worse: send emails)
    Logger.reset()
    del logging.root.handlers[:]
    logging.root.addHandler(logging.NullHandler())
    # Silence the annoying pycountry logger
    import pycountry.db
    pycountry.db.logger.addHandler(logging.NullHandler())


def pytest_unconfigure(config):
    config.indico_temp_dir.remove(rec=True)


def pytest_addoption(parser):
    parser.addini('indico_plugins', 'List of indico plugins to load')
