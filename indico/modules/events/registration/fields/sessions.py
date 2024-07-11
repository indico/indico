# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json

from flask import g, session
from marshmallow import ValidationError, fields, validate, validates_schema
from sqlalchemy.orm import joinedload

from indico.core.db.sqlalchemy import db
from indico.core.marshmallow import mm
from indico.modules.events.registration.controllers.display import RHRegistrationForm
from indico.modules.events.registration.fields.base import RegistrationFormFieldBase
from indico.modules.events.registration.models.registrations import RegistrationData
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.sessions import Session
from indico.util.date_time import format_interval, format_skeleton
from indico.util.i18n import _


class SessionsFieldDataSchema(mm.Schema):
    minimum = fields.Integer(load_default=0, validate=validate.Range(0))
    maximum = fields.Integer(load_default=0, validate=validate.Range(0))
    collapse_days = fields.Bool(load_default=False)

    @validates_schema(skip_on_field_errors=True)
    def validate_min_max(self, data, **kwargs):
        if data['minimum'] and data['maximum'] and data['minimum'] > data['maximum']:
            raise ValidationError('Maximum value must be less than minimum value.', 'maximum')


def _format_block(block, tzinfo):
    interval = format_interval(block.start_dt.astimezone(tzinfo), block.end_dt.astimezone(tzinfo), 'Hm')
    day = format_skeleton(block.start_dt, 'EdMM', timezone=tzinfo)
    return f'{day}: {interval} - {block.full_title}'


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
        event = self.form_item.registration_form.event
        session_blocks = (SessionBlock.query
                          .join(Session)
                          .filter(Session.event == event,
                                  ~Session.is_deleted)
                          .options(joinedload(SessionBlock.timetable_entry).raiseload('*'))
                          .all())
        return {str(b.id): _format_block(b, event.tzinfo) for b in session_blocks}

    def get_validators(self, existing_registration):
        def _check_number_of_sessions(new_data):
            min_ = self.form_item.data.get('minimum')
            max_ = self.form_item.data.get('maximum')
            if max_ is not None and min_ is not None:
                if max_ != 0 and len(new_data) > max_:
                    raise ValidationError(_('Please select no more than {max} sessions.').format(max=max_))
                if min_ != 0 and len(new_data) < min_:
                    raise ValidationError(_('Please select at least {min} sessions.').format(min=min_))

        def _check_session_block_is_valid(new_data):
            event = self.form_item.registration_form.event
            blocks = SessionBlock.query.filter(SessionBlock.id.in_(new_data)).all()
            # disallow referencing invalid session blocks
            if len(blocks) != len(new_data):
                raise ValidationError('Cannot select session blocks which do not exist')
            # disallow any session blocks from other events
            if not all(sb.event == event for sb in blocks):
                raise ValidationError('Cannot select session blocks from another event')
            # ensure the user can access the session
            if not all(sb.can_access(session.user) for sb in blocks):
                raise ValidationError('Cannot select session blocks not accessible to you')

        return [_check_number_of_sessions, _check_session_block_is_valid]

    def get_friendly_data(self, registration_data, for_humans=False, for_search=False):
        event = registration_data.registration.event
        # this is a bit ugly, but we need to use the user's timezone if it's in an end-user area,
        # while using the event's timezone if it's in a management area...
        tzinfo = event.display_tzinfo if isinstance(getattr(g, 'rh', None), RHRegistrationForm) else event.tzinfo
        blocks = (SessionBlock.query
                  .filter(SessionBlock.id.in_(registration_data.data))
                  .options(joinedload(SessionBlock.timetable_entry).raiseload('*'))
                  .all())
        if for_humans or for_search:
            return '; '.join(b.full_title for b in blocks)
        return [_format_block(b, tzinfo) for b in blocks]

    def create_sql_filter(self, data_list):
        data_list = json.dumps(list(map(int, data_list)))
        return RegistrationData.data.op('@>')(db.func.jsonb(data_list))
