# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json

from flask import session
from marshmallow import ValidationError, fields, validate, validates_schema

from indico.core.db.sqlalchemy import db
from indico.core.marshmallow import mm
from indico.modules.events.registration.fields.base import RegistrationFormFieldBase
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.util.i18n import _


class SessionsFieldDataSchema(mm.Schema):
    minimum = fields.Integer(load_default=0, validate=validate.Range(0))
    maximum = fields.Integer(load_default=0, validate=validate.Range(0))
    collapse_days = fields.Bool(load_default=False)

    @validates_schema(skip_on_field_errors=True)
    def validate_min_max(self, data, **kwargs):
        if data['minimum'] and data['maximum'] and data['minimum'] > data['maximum']:
            raise ValidationError('Maximum value must be less than minimum value.', 'maximum')


class SessionsField(RegistrationFormFieldBase):
    name = 'sessions'
    mm_field_class = fields.List
    mm_field_args = (fields.Integer,)
    setup_schema_base_cls = SessionsFieldDataSchema

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

        def _check_session_block_is_valid(new_data):
            event = self.form_item.registration_form.event
            if not all(s.can_access(session.user)
                       for s in SessionBlock.query.join(Session).filter(SessionBlock.session_id == Session.id,
                                                                        Session.event_id == event.id,
                                                                        SessionBlock.session_id.in_(new_data))):
                raise ValidationError(_("There's a problem with the data format, please try again."))

        return [_check_number_of_sessions, _check_session_block_is_valid]

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        tzinfo = registration_data.registration.event.tzinfo
        blocks = SessionBlock.query.filter(SessionBlock.id.in_(registration_data.data)).all()
        if for_humans or for_search:
            return '; '.join(b.full_title for b in blocks)
        return [
            ' - '.join(
                [
                    b.start_dt.astimezone(tzinfo).strftime('%H:%M'),
                    b.end_dt.astimezone(tzinfo).strftime('%H:%M'),
                    b.full_title
                ]
            )
            for b in blocks
        ]

    def create_sql_filter(self, data_list):
        data_list = json.dumps(list(map(int, data_list)))
        return RegistrationData.data.op('@>')(db.func.jsonb(data_list))
