# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from operator import itemgetter

from indico.modules.events.controllers.base import RHProtectedEventBase
from indico.util.iterables import group_list


class RHAPIRegistrationForms(RHProtectedEventBase):
    def _process(self):
        from indico.modules.events.registration.schemas import RegistrationFormPrincipalSchema
        return RegistrationFormPrincipalSchema(many=True).jsonify(self.event.registration_forms)


class RHAPIEventSessionBlocks(RHProtectedEventBase):
    def _process(self):
        schema = [{'id': sb.id, 'start_dt': sb.start_dt.astimezone(self.event.tzinfo).date().isoformat(),
                   'full_title': sb.full_title} for s in self.event.sessions for sb in s.blocks]
        return group_list(schema, key=itemgetter('start_dt'), sort_by=itemgetter('start_dt'))
