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

"""
Some utils for unit tests
"""

# system imports
from contextlib import contextmanager
from contextlib2 import ExitStack
from flask import session
from functools import wraps
import os
import unittest
import new
import contextlib

# indico imports
from indico.util.benchmark import Benchmark
from indico.util.contextManager import ContextManager
from indico.util.fossilize import clearCache
from indico.util.i18n import set_session_lang

# indico legacy imports
from indico.core.logger import Logger
from indico.web.flask.app import make_app

loadedFeatures = []


class FeatureLoadingObject(object):

    def __init__(self):
        self._activeFeatures = []

    def _configFeature(self, ftr, obj):
        global loadedFeatures

        if type(ftr) == str:
            ftrName, modName = map(lambda p: p[::-1],
                                   ftr[::-1].split('.', 1))

            ftrClsName = "%s_Feature" % ftrName

            mod = __import__('indico.tests.python.unit.%s' % modName,
                             globals(), locals(), [ftrClsName])
            ftr = mod.__dict__[ftrClsName]
        else:
            pass

        for name, func in ftr.__dict__.iteritems():
            if name.startswith('_action_'):
                setattr(obj, name[7:], new.instancemethod(func, obj, obj.__class__))

            elif name.startswith('_context_'):
                setattr(obj, name, new.instancemethod(func, obj, obj.__class__))

        ftrObj = ftr()

        if ftr not in loadedFeatures:
            ftrObj.start(obj)
            loadedFeatures.append(ftr)

        return ftrObj

    def _configFeatures(self, obj):

        # process requirements
        for ftr in self._requires:
            ftrObj = self._configFeature(ftr, obj)
            self._activeFeatures.append(ftrObj)

    def _unconfigFeatures(self, obj):
        global loadedFeatures
        for ftr in self._activeFeatures[::-1]:
            ftr.destroy(obj)

        del loadedFeatures[:]
        del self._activeFeatures[:]


class IndicoTestFeature(FeatureLoadingObject):

    _requires = []

    def start(self, obj):
        self._configFeatures(obj)

    def destroy(self, obj):
        self._unconfigFeatures(obj)


def with_context(context):
    """
    Decorator
    """
    def wrapper(method):
        @wraps(method)
        def testWrapped(self, *args, **kwargs):
            with self._context(context):
                return method(self, *args, **kwargs)
        return testWrapped
    return wrapper


class ContextManager_Feature(IndicoTestFeature):

    """
    Creates a context manager
    """

    def start(self, obj):
        super(ContextManager_Feature, self).start(obj)

        # create the context
        ContextManager.destroy()

    def destroy(self, obj):
        super(ContextManager_Feature, self).destroy(obj)

        ContextManager.destroy()


class RequestEnvironment_Feature(IndicoTestFeature):

    """
    Creates an environment that should be similar to a regular request
    """

    def _action_endRequest(self):
        if hasattr(self, '_do'):
            self._do._notify('requestFinished')

    def _action_startRequest(self):
        if hasattr(self, '_do'):
            self._do._notify('requestStarted')

    def _action_make_app_request_context(self, config):
        # XXX: Check if this breaks SA tests. If yes, use an argument for db_setup
        app = make_app(db_setup=False)
        if config:
            for k, v in config.iteritems():
                app.config[k] = v
        env = {
            'environ_base': {
                'REMOTE_ADDR': '127.0.0.1'
            }
        }
        return app.test_request_context(**env)

    def _action_mock_session_user(self):
        # None of the current tests actually require a user in the session.
        # If this changes, assign a avatar mock object here
        session.user = None

    def _context_request(self, config=None):
        self._startRequest()
        with self._make_app_request_context(config):
            self._mock_session_user()
            set_session_lang('en_GB')
            yield
        self._endRequest()


class IndicoTestCase(unittest.TestCase, FeatureLoadingObject):

    """
    IndicoTestCase is a normal TestCase on steroids. It allows you to load
    "features" that will empower your test classes
    """

    _requires = []
    _slow = False

    def __init__(self, *args, **kwargs):
        self._benchmark = Benchmark()
        unittest.TestCase.__init__(self, *args, **kwargs)
        FeatureLoadingObject.__init__(self)

    def setUp(self):
        if os.environ.get('INDICO_SKIP_SLOW_TESTS') == '1':
            if self._slow:
                self.skipTest('Slow tests disabled')
            testMethod = getattr(self, self._testMethodName)
            if getattr(testMethod, '_slow', False):
                self.skipTest('Slow tests disabled')
        set_session_lang('en_GB')
        Logger.removeHandler('smtp')
        clearCache()  # init/clear fossil cache
        self._configFeatures(self)
        self._benchmark.start()

    def tearDown(self):
        self._benchmark.stop()
        self._unconfigFeatures(self)

    @contextlib.contextmanager
    def _context(self, *contexts, **kwargs):
        with ExitStack() as stack:
            res = []
            for ctxname in contexts:
                ctx = contextmanager(getattr(self, '_context_%s' % ctxname))
                res.append(stack.enter_context(ctx(**kwargs)))
            yield res if len(res) > 1 else res[0]

    def run(self, result=None):
        res = super(IndicoTestCase, self).run(result)
        if os.environ.get('INDICO_BENCHMARK_TESTS') == '1':
            self._benchmark.print_result(1, 2.5)
        return res
