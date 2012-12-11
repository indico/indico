# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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
import re

# indico imports
from indico.util.metadata.serializer import Serializer

from indico.web.http_api.api import HTTPAPIHook, DataFetcher
from indico.web.http_api.responses import HTTPAPIError
from indico.web.rh.file import RHFileCommon
from indico.web.wsgi import webinterface_handler_config as apache

# legacy imports
from MaKaC.conference import LocalFile
from MaKaC.common import Config


@HTTPAPIHook.register
class FileHook(HTTPAPIHook, RHFileCommon):
    """
    Example: /export/file/conference/1/session/2/contrib/3/subcontrib/4/material/Slides/5.bin?ak=00000000-0000-0000-0000-000000000000
    """
    TYPES = ('file',)
    DEFAULT_DETAIL = 'bin'
    VALID_FORMATS = ('bin',)
    GUEST_ALLOWED = True
    RE = r'(?P<event>[\w\s]+)(/session/(?P<session>[\w\s]+))?(/contrib/(?P<contrib>[\w\s]+))?(/subcontrib/(?P<subcontrib>[\w\s]+))?/material/(?P<material>[^/]+)/(?P<res>[\w\s]+)'

    def _getParams(self):
        super(FileHook, self)._getParams()

        self._type = 'file'
        self._event = self._pathParams['event']
        self._session = self._pathParams['session']
        self._contrib = self._pathParams['contrib']
        self._subcontrib = self._pathParams['subcontrib']
        self._material = self._pathParams['material']
        self._res = self._pathParams['res']

        self._params = {'confId': self._event, 'sessionId': self._session, 'contribId': self._contrib,
                  'subContId': self._subcontrib, 'materialId': self._material, 'resId': self._res}

        import MaKaC.webinterface.locators as locators
        l = locators.WebLocator()
        try:
            l.setResource(self._params)
            self._file = l.getObject()
        except (KeyError, AttributeError):
            raise HTTPAPIError("File not found", apache.HTTP_NOT_FOUND)


    def export_file(self, aw):

        if not isinstance(self._file, LocalFile):
            raise HTTPAPIError("Resource is not a file", apache.HTTP_NOT_FOUND)

        self._binaryData = RHFileCommon._process(self)

        expInt = FileFetcher(aw, self)
        return expInt.file([Config.getInstance().getFileTypeMimeType(self._file.getFileType()), self._binaryData])

    def _hasAccess(self, aw):
        return self._file.canAccess(aw)

    @classmethod
    def _matchPath(cls, path):
        if not hasattr(cls, '_RE'):
            cls._RE = re.compile(r'/' + cls.PREFIX + '/event/' + cls.RE + r'\.(\w+)$')
        return cls._RE.match(path)


class FileFetcher(DataFetcher):

    DETAIL_INTERFACES = {
        'bin': '',
    }

    def file(self, data):
        return self._process(data)


class FileSerializer(Serializer):

    schemaless = False

    def __call__(self, fossils):
        self._mime = fossils['results'][0]
        return fossils['results'][1]


Serializer.register('bin', FileSerializer)
