# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from operator import itemgetter

from flask import session
from sqlalchemy.orm import joinedload

from indico.modules.events.controllers.base import RHProtectedEventBase
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.util.iterables import group_list


class RHAPIRegistrationForms(RHProtectedEventBase):
    def _process(self):
        from indico.modules.events.registration.schemas import RegistrationFormPrincipalSchema
        return RegistrationFormPrincipalSchema(many=True).jsonify(self.event.registration_forms)


class RHAPIEventSessionBlocks(RHProtectedEventBase):
    def _process(self):
        blocks = (SessionBlock.query
                  .join(Session)
                  .filter(Session.event == self.event,
                          ~Session.is_deleted)
                  .options(joinedload(SessionBlock.timetable_entry).raiseload('*'))
                  .all())
        res = [
            {
                'id': sb.id,
                'start_dt': sb.start_dt.astimezone(self.event.tzinfo).date().isoformat(),
                'start_time': sb.start_dt.astimezone(self.event.tzinfo).strftime('%H:%M'),
                'end_time': sb.end_dt.astimezone(self.event.tzinfo).strftime('%H:%M'),
                'full_title': sb.full_title,
            }
            for sb in blocks
            if sb.can_access(session.user)
        ]
        return group_list(res, key=itemgetter('start_dt'), sort_by=itemgetter('start_dt'))
