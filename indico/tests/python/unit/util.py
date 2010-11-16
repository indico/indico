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
import unittest

# indico imports
from MaKaC.common.contextManager import ContextManager


# stores features that have been loaded so far
_indicoLoadedTestFeatures = []


class FeatureLoadingObject(object):

    def _configFeature(self, ftr, obj):
        global _indicoLoadedTestFeatures

        modName, ftrName = ftr.split('.')

        ftrClsName = "%s_Feature" % ftrName

        mod = __import__('indico.tests.python.unit.%s' % modName,
                         globals(), locals(), [ftrClsName])

        ftr = mod.__dict__[ftrClsName]
        ftrObj = ftr()
        ftrObj.start(obj)


    def _configFeatures(self, obj):
        global _indicoLoadedTestFeatures

        self._activeFeatures = []

        for ftr in self._requires:
            if ftr not in _indicoLoadedTestFeatures:
                ftrObj = self._configFeature(ftr, obj)
                self._activeFeatures.append(ftrObj)
                _indicoLoadedTestFeatures.append(ftr)

    def _unconfigFeatures(self, obj):
        for ftr in self._activeFeatures:
            ftr.destroy(obj)


class IndicoTestCase(unittest.TestCase, FeatureLoadingObject):

    """
    IndicoTestcase is a normal TestCase on steroids. It allows you to load
    "features" that will empower your test classes
    """

    _requires = []

    def setUp(self):
        self._configFeatures(self)

    def destroy(self):
        self._unconfigFeatures(self)


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

    def start(self, obj):
        super(RequestEnvironment_Feature, self).start(obj)
        obj._do._notify('requestStarted')


    def destroy(self, obj):
        super(RequestEnvironment_Feature, self).destroy(obj)
        obj._do._notify('requestFinished')

