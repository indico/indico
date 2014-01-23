# -*- coding: utf-8 -*-
##
## $id$
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

# stdlib imports
import zope.interface
import os

# legacy imports
from MaKaC.plugins.base import Observable

# indico imports
from indico.core.extpoint import Component
from indico.core.extpoint.plugins import IPluginImplementationContributor
from indico.ext.search.invenio.implementation import InvenioSEA, InvenioRedirectSEA
import indico.ext.search.invenio
from MaKaC.plugins.base import PluginsHolder
from indico.web.handlers import RHHtdocs


class PluginImplementationContributor(Component, Observable):
    """
    Adds interface extension to plugins's implementation.
    """

    zope.interface.implements(IPluginImplementationContributor)

    def getPluginImplementation(self, obj):
        plugin = PluginsHolder().getPluginType('search').getPlugin("invenio")
        typeSearch = plugin.getOptions()["type"].getValue()
        return ("invenio", InvenioRedirectSEA if typeSearch == "redirect" else InvenioSEA)


class RHSearchHtdocsInvenio(RHHtdocs):

    _local_path = os.path.join(os.path.dirname(indico.ext.search.invenio.__file__), "htdocs")
    _min_dir = 'invenio'
