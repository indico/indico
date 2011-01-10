# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Some utils for unit tests
"""

# system imports
import unittest, sys, new, contextlib

# indico imports
from MaKaC.common.contextManager import ContextManager

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
        self._configFeatures(self)

    def _closeEnvironment(self):
        self._unconfigFeatures(self)

    @contextlib.contextmanager
    def _context(self, *contexts):
        ctxs = []
        for ctxname in contexts:
            ctx = getattr(self, '_context_%s' % ctxname)()

            ctx.next()
            ctxs.append(ctx)

        yield

        for ctx in ctxs[::-1]:
            ctx.next()


class IndicoTestFeature(FeatureLoadingObject):

    _requires = []

    def start(self, obj):
        self._configFeatures(obj)

    def destroy(self, obj):
        self._unconfigFeatures(obj)


class ContextManager_Feature(IndicoTestFeature):

    """
    Creates a context manager
    """

    _requires = []

    def start(self, obj):
        super(ContextManager_Feature, self).start(obj)

        # create the context
        ContextManager.create()


    def destroy(self, obj):
        super(ContextManager_Feature, self).destroy(obj)

        ContextManager.destroy()


class RequestEnvironment_Feature(IndicoTestFeature):

    """
    Creates an environment that should be similar to a regular request
    """

    _requires = []

    def _action_endRequest(self):
        self._do._notify('requestFinished')

    def _action_startRequest(self):
        self._do._notify('requestStarted')

    def _context_request(self):
        self._startRequest()
        yield
        self._endRequest()
