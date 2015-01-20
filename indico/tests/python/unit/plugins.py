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

# indico test framework imports
from indico.tests.python.unit.util import IndicoTestFeature

# legacy imports
from MaKaC.plugins.base import Observable, PluginsHolder

from indico.core.db import DBMgr

class DummyObservable(Observable):
    pass


class Plugins_Feature(IndicoTestFeature):

    _requires = ['db.Database']

    def start(self, obj):
        super(Plugins_Feature, self).start(obj)
        with obj._context('database'):
            obj._ph = PluginsHolder()
            obj._ph.reloadAllPlugins()
            obj._do = DummyObservable()
