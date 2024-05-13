# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import ValidationError, fields, validate

from indico.core.db.sqlalchemy import db
from indico.modules.events.registration.fields.base import RegistrationFormFieldBase
from indico.modules.events.registration.models.registrations import RegistrationData
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

    @property
    def filter_choices(self):
        sessions_ids = [s.id for s in self.form_item.registration_form.event.sessions]
        return {str(s.id): s.full_title for s in SessionBlock.query.filter(SessionBlock.session_id.in_(sessions_ids))}

    def get_validators(self, existing_registration):
        def _check_number_of_sessions(new_data):
            _min = self.view_data.get('minimum')
            _max = self.view_data.get('maximum')
            if _max is not None and _min is not None:
                if _max != 0 and len(new_data) > _max:
                    raise ValidationError(_('Please select no more than {max} sessions.').format(max=_max))
                if _min != 0 and len(new_data) < _min:
                    raise ValidationError(_('Please select at least {min} sessions.').format(min=_min))
        return _check_number_of_sessions

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        tzinfo = registration_data.registration.event.tzinfo
        blocks = SessionBlock.query.filter(SessionBlock.id.in_(registration_data.data)).all()
        formatted_blocks = [f'{b.full_title}-{b.start_dt.astimezone(tzinfo).strftime("%H:%M:%S")}'
                            for b in blocks] if blocks else None
        return '; '.join(x.full_title for x in blocks) if for_humans or for_search else formatted_blocks

    def create_sql_filter(self, data_list):
        data_list = str([int(e) for e in data_list])
        return RegistrationData.data.op('@>')(db.func.jsonb(data_list))
