# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from itertools import groupby

from indico.modules.events.controllers.base import RHProtectedEventBase


class RHAPIRegistrationForms(RHProtectedEventBase):
    def _process(self):
        from indico.modules.events.registration.schemas import RegistrationFormPrincipalSchema
        return RegistrationFormPrincipalSchema(many=True).jsonify(self.event.registration_forms)


class RHAPIEventTimeTable(RHProtectedEventBase):
    def _process(self):
        schema = [{'id': sb.id, 'start_dt': sb.start_dt.strftime('%d-%b-%Y'),
                   'fullTitle': sb.full_title} for s in self.event.sessions for sb in s.blocks]
        return {date: list(e) for date, e in groupby(schema, key=lambda x: x['start_dt'])}
