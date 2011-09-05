# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2011 CERN.
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

from indico.web.http_api import HTTPAPIHook
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.responses import HTTPAPIError
from indico.web.wsgi import webinterface_handler_config as apache
from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin
from MaKaC.plugins.Collaboration.RecordingManager.common import createIndicoLink


globalHTTPAPIHooks = ['CollaborationAPIHook']

class CollaborationAPIHook(HTTPAPIHook):
    PREFIX = 'api'
    TYPES = ('recordingManager',)
    RE = r'createLink'
    GUEST_ALLOWED = False
    VALID_FORMATS = ('json',)
    COMMIT = True
    HTTP_POST = True

    def _hasAccess(self, aw):
        return RCCollaborationAdmin.hasRights(user=aw.getUser())

    def _getParams(self):
        super(CollaborationAPIHook, self)._getParams()
        self._indicoID = get_query_parameter(self._queryParams, ['iid', 'indicoID'])
        self._cdsID = get_query_parameter(self._queryParams, ['cid', 'cdsID'])

    def api_recordingManager(self, aw):
        if not self._indicoID or not self._cdsID:
            raise HTTPAPIError('A required argument is missing.', apache.HTTP_BAD_REQUEST)

        success = createIndicoLink(self._indicoID, self._cdsID)
        return {'success': success}
