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

from MaKaC.services.implementation.base import ServiceBase
from MaKaC.plugins.base import PluginsHolder

import os
from indico.web.rh import RHHtdocs
from indico.ext.importer.helpers import ImporterHelper
import indico.ext.importer

class RHImporterHtdocs(RHHtdocs):
    """
    Static file handler for Importer plugin
    """

    _url = r"^/importer/(?P<filepath>.*)$"
    _local_path = os.path.join(indico.ext.importer.__path__[0], 'htdocs')


class DataImportService(ServiceBase):
    """
    Fetches data from the specified importer plugin.
    Arguments:
    query - string used in importer's search phrase
    importer - name of an importer plugin being used
    size - number of returned queries
    """

    def _checkParams(self):
        ServiceBase._checkParams(self)
        self._query = self._params['query']
        self._importer = self._params['importer']
        self._size = self._params.get('size', 10)

    def _getAnswer(self):
        importer = ImporterHelper.getImporter(self._importer)
        if importer:
            return importer.importData(self._query, self._size)

class GetImportersService(ServiceBase):
    """
    Returns names and ids of active importer plugins.
    """
    def _getAnswer(self):
        importers = {}
        for plugin in PluginsHolder().getPluginType('importer').getPluginList():
            importers[plugin.getId()] = plugin.getName()
        return importers

methodMap = {
             "importer.import" : DataImportService,
             "importer.getImporters": GetImportersService,
             }