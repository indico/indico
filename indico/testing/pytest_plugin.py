# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import logging
import os
import re
import sys
import tempfile

import py


# Ignore config file in case there is one
os.environ['INDICO_CONFIG'] = os.devnull

pytest_plugins = ('indico.testing.fixtures.abstract', 'indico.testing.fixtures.app', 'indico.testing.fixtures.cache',
                  'indico.testing.fixtures.category', 'indico.testing.fixtures.contribution',
                  'indico.testing.fixtures.database', 'indico.testing.fixtures.disallow',
                  'indico.testing.fixtures.editing', 'indico.testing.fixtures.oauth', 'indico.testing.fixtures.paper',
                  'indico.testing.fixtures.person', 'indico.testing.fixtures.user', 'indico.testing.fixtures.event',
                  'indico.testing.fixtures.rb', 'indico.testing.fixtures.smtp', 'indico.testing.fixtures.storage',
                  'indico.testing.fixtures.timetable', 'indico.testing.fixtures.util',
                  'indico.testing.fixtures.session', 'indico.testing.fixtures.receipt')


def pytest_configure(config):
    # Load all the plugins defined in pytest_plugins
    config.pluginmanager.consider_module(sys.modules[__name__])
    config.indico_temp_dir = py.path.local(tempfile.mkdtemp(prefix='indicotesttmp.'))
    config.indico_plugins = [_f for _f in [x.strip() for x in re.split(r'[\s,;]+', config.getini('indico_plugins'))]
                             if _f]
    # Make sure we don't write any log files (or worse: send emails)
    assert not logging.root.handlers
    logging.root.addHandler(logging.NullHandler())
    # Silence the annoying pycountry logger
    logging.getLogger('pycountry.db').addHandler(logging.NullHandler())


def pytest_unconfigure(config):
    config.indico_temp_dir.remove(rec=True)


def pytest_addoption(parser):
    parser.addini('indico_plugins', 'List of indico plugins to load')
