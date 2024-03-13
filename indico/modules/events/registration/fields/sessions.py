# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import ValidationError, fields, validate

from indico.modules.events.registration.fields.base import RegistrationFormFieldBase
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.util.i18n import _


class SessionsField(RegistrationFormFieldBase):
    name = 'sessions'
    mm_field_class = fields.List
    mm_field_args = (fields.Integer,)
    setup_schema_fields = {
        'display': fields.String(load_default='expanded'),
        'allow_full_days': fields.Boolean(load_default=False),
        'minimum': fields.Integer(load_default=0, validate=validate.Range(0)),
        'maximum': fields.Integer(load_default=0, validate=validate.Range(0)),
    }

    @property
    def default_value(self):
        return []

    def get_validators(self, existing_registration):
        def _check_number_of_sessions(new_data):
            _min = self.view_data.get('minimum')
            _max = self.view_data.get('maximum')
            if _max is not None and _min is not None:
                if _max != 0 and len(new_data) > _max:
                    raise ValidationError(_('Please select no more than {_max} sessions.').format(_max=_max))
                if _min != 0 and len(new_data) < _min:
                    raise ValidationError(_('Please select at least {_min} sessions.').format(_min=_min))
        return _check_number_of_sessions

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        blocks = SessionBlock.query.filter(SessionBlock.id.in_(registration_data.data)).all()
        return ('; ').join(x.full_title for x in blocks) if for_humans or for_search else blocks
