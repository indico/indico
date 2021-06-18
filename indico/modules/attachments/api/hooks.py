# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.attachments.api.util import build_folders_api_data
from indico.modules.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.sessions import Session
from indico.web.http_api import HTTPAPIHook
from indico.web.http_api.responses import HTTPAPIError


@HTTPAPIHook.register
class AttachmentsExportHook(HTTPAPIHook):
    TYPES = ('attachments',)
    RE = (r'(?P<event_id>\d+)'
          r'((/session/(?P<session_id>\d+)|(/contribution/(?P<contribution_id>\d+)(/(?P<subcontribution_id>\d+))?))?)?')
    MAX_RECORDS = {}
    GUEST_ALLOWED = True
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):
        super()._getParams()
        event = self._obj = Event.get(self._pathParams['event_id'], is_deleted=False)
        if event is None:
            raise HTTPAPIError('No such event', 404)
        session_id = self._pathParams.get('session_id')
        if session_id:
            self._obj = Session.query.with_parent(event).filter_by(id=session_id).first()
            if self._obj is None:
                raise HTTPAPIError('No such session', 404)
        contribution_id = self._pathParams.get('contribution_id')
        if contribution_id:
            contribution = self._obj = Contribution.query.with_parent(event).filter_by(id=contribution_id).first()
            if contribution is None:
                raise HTTPAPIError('No such contribution', 404)
            subcontribution_id = self._pathParams.get('subcontribution_id')
            if subcontribution_id:
                self._obj = SubContribution.query.with_parent(contribution).filter_by(id=subcontribution_id).first()
                if self._obj is None:
                    raise HTTPAPIError('No such subcontribution', 404)

    def _has_access(self, user):
        return self._obj.can_access(user)

    def export_attachments(self, user):
        return {'folders': build_folders_api_data(self._obj)}
