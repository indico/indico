# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify

from indico.modules.events.controllers.base import RHAuthenticatedEventBase
from indico.modules.forms.models.forms import RegistrationForm


class RHListTemplateRegistrationForms(RHAuthenticatedEventBase):
    """AJAX endpoint that lists all template registration forms usable by the event (dict representation)."""

    ALLOW_LOCKED = True

    def _process(self):
        query = RegistrationForm.query.filter(~RegistrationForm.is_deleted,
                                              RegistrationForm.category_id.in_(self.event.category_chain))

        result = [{'id': regform.id, 'friendly_id': regform.id, 'title': regform.title,
                   'full_title': f'# {regform.title}: in category: {regform.owner.id}'}
                  for regform in query]
        return jsonify(result)
