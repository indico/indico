# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from operator import itemgetter

from flask import session
from marshmallow import fields
from sqlalchemy.orm import joinedload

from indico.modules.events.controllers.base import RHProtectedEventBase
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.util.date_time import format_interval
from indico.util.iterables import group_list
from indico.web.args import use_kwargs


class RHAPIRegistrationForms(RHProtectedEventBase):
    def _process(self):
        from indico.modules.events.registration.schemas import RegistrationFormPrincipalSchema
        return RegistrationFormPrincipalSchema(many=True).jsonify(self.event.registration_forms)


class RHAPIEventSessionBlocks(RHProtectedEventBase):
    @use_kwargs({
        'force_event_tz': fields.Boolean(load_default=False),
    }, location='query')
    def _process(self, force_event_tz):
        tzinfo = self.event.tzinfo if force_event_tz else self.event.display_tzinfo
        blocks = (SessionBlock.query
                  .join(Session)
                  .filter(Session.event == self.event,
                          ~Session.is_deleted)
                  .options(joinedload(SessionBlock.timetable_entry).raiseload('*'))
                  .all())
        res = [
            {
                'id': sb.id,
                'start_date': sb.start_dt.astimezone(tzinfo).date().isoformat(),
                'time': format_interval(sb.start_dt.astimezone(tzinfo), sb.end_dt.astimezone(tzinfo), 'Hm'),
                'full_title': sb.full_title,
            }
            for sb in blocks
            if sb.can_access(session.user)
        ]
        return group_list(res, key=itemgetter('start_date'), sort_by=itemgetter('start_date', 'time'))
