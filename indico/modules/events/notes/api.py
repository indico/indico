# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.notes.models.notes import EventNote
from indico.modules.events.notes.util import build_note_api_data
from indico.modules.events.sessions import Session
from indico.web.http_api import HTTPAPIHook
from indico.web.http_api.responses import HTTPAPIError


@HTTPAPIHook.register
class NoteExportHook(HTTPAPIHook):
    TYPES = ('note',)
    RE = (r'(?P<event_id>\d+)'
          r'((/session/(?P<session_id>\d+)|(/contribution/(?P<contribution_id>\d+)(/(?P<subcontribution_id>\d+))?))?)?')
    MAX_RECORDS = {}
    GUEST_ALLOWED = True
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):
        super(NoteExportHook, self)._getParams()
        event = self._obj = Event.get(self._pathParams['event_id'], is_deleted=False)
        if event is None:
            raise HTTPAPIError('No such event', 404)
        session_id = self._pathParams.get('session_id')
        if session_id:
            self._obj = Session.query.with_parent(event).filter_by(id=session_id).first()
            if self._obj is None:
                raise HTTPAPIError("No such session", 404)
        contribution_id = self._pathParams.get('contribution_id')
        if contribution_id:
            contribution = self._obj = (Contribution.query.with_parent(event)
                                        .filter_by(id=contribution_id, is_deleted=False)
                                        .first())
            if contribution is None:
                raise HTTPAPIError("No such contribution", 404)
            subcontribution_id = self._pathParams.get('subcontribution_id')
            if subcontribution_id:
                self._obj = SubContribution.query.with_parent(contribution).filter_by(id=subcontribution_id,
                                                                                      is_deleted=False).first()
                if self._obj is None:
                    raise HTTPAPIError("No such subcontribution", 404)
        self._note = EventNote.get_for_linked_object(self._obj, preload_event=False)
        if self._note is None or self._note.is_deleted:
            raise HTTPAPIError("No such note", 404)

    def _has_access(self, user):
        return self._obj.can_access(user)

    def export_note(self, user):
        return build_note_api_data(self._note)
