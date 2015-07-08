# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from indico.modules.attachments.util import get_attached_items
from indico.modules.attachments.api.util import build_file_api_data, build_folder_api_data
from indico.web.http_api import HTTPAPIHook
from indico.web.http_api.responses import HTTPAPIError
from MaKaC.conference import ConferenceHolder


@HTTPAPIHook.register
class AttachmentsExportHook(HTTPAPIHook):
    TYPES = ('attachments',)
    RE = r'(?P<event_id>\d+)(/(?P<session_id>\d+)(/(?P<contribution_id>\d+)(/(?P<subcontribution_id>\d+))?)?)?'
    MAX_RECORDS = {}
    GUEST_ALLOWED = True
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):
        super(AttachmentsExportHook, self)._getParams()
        event = self._obj = ConferenceHolder().getById(self._pathParams['event_id'], True)
        if event is None:
            raise HTTPAPIError('No such event', 404)
        session_id = self._pathParams.get('session_id')
        if session_id:
            session = self._obj = event.getSessionById(session_id)
            if session is None:
                raise HTTPAPIError("No such session", 404)
        contribution_id = self._pathParams.get('contribution_id')
        if contribution_id:
            contribution = self._obj = session.getContributionById(contribution_id)
            if contribution is None:
                raise HTTPAPIError("No such contribution", 404)
        subcontribution_id = self._pathParams.get('subcontribution_id')
        if subcontribution_id:
            subcontribution = self._obj = contribution.getSubContributionById(subcontribution_id)
            if subcontribution is None:
                raise HTTPAPIError("No such subcontribution", 404)
        self._data = get_attached_items(self._obj)

    def _hasAccess(self, aw):
        return self._obj.canView(aw)

    def export_attachments(self, aw):
        return {
            'attachments': filter(None, (build_file_api_data(file_) for file_ in self._data.get('files', []))),
            'folders': filter(None, (build_folder_api_data(folder) for folder in self._data.get('folders', [])))
        }
