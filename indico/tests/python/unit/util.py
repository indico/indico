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
from flask import session
from functools import wraps
import unittest
import new
import contextlib

# indico imports
from indico.util.contextManager import ContextManager
from indico.util.fossilize import clearCache
from indico.util.i18n import setLocale

# indico legacy imports
from MaKaC.common.logger import Logger
from indico.web.flask.app import make_app

loadedFeatures = []


class FeatureLoadingObject(object):

    def __init__(self):
        self._activeFeatures = []

    def _configFeature(self, ftr, obj):
        global loadedFeatures

        if type(ftr) == str:
            modName, ftrName = ftr.split('.')

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
        self._do._notify('requestFinished')

    def _action_startRequest(self):
        self._do._notify('requestStarted')

    def _action_make_app_request_context(self):
        app = make_app()
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

    def _context_request(self):
        self._startRequest()
        with self._make_app_request_context():
            self._mock_session_user()
            setLocale('en_GB')
            yield
        self._endRequest()


class IndicoTestCase(unittest.TestCase, FeatureLoadingObject):

    """
    IndicoTestCase is a normal TestCase on steroids. It allows you to load
    "features" that will empower your test classes
    """

    _requires = []

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        FeatureLoadingObject.__init__(self)

    def setUp(self):
        setLocale('en_GB')
        Logger.removeHandler('smtp')
        clearCache()  # init/clear fossil cache
        self._configFeatures(self)

    def tearDown(self):
        self._unconfigFeatures(self)

    @contextlib.contextmanager
    def _context(self, *contexts, **kwargs):
        ctxs = []
        res = []
        for ctxname in contexts:
            ctx = getattr(self, '_context_%s' % ctxname)(**kwargs)
            res.append(ctx.next())
            ctxs.append(ctx)

        yield res if len(res) > 1 else res[0]

        for ctx in ctxs[::-1]:
            ctx.next()
