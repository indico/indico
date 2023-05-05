# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.util.date_time import now_utc
from indico.util.enum import RichIntEnum
from indico.util.i18n import _


class DataExportRequestState(RichIntEnum):
    __titles__ = [_('Pending'), _('Running'), _('Success'), _('Failed'), _('Expired')]
    pending = 0  # Default value when there is no request
    running = 1
    success = 2
    failed = 3
    expired = 4  # The associated file has been deleted


class DataExportOptions(RichIntEnum):
    __titles__ = [_('Personal data'), _('Settings'), _('Minutes & Contributions'), _('Registrations'),
                  _('Room booking data'), _('Abstracts & Papers'), _('Survey submissions'),
                  _('Attachments & Materials'), _('Miscellaneous')]
    personal_data = 0
    settings = 1
    contribs = 2
    registrations = 3
    room_booking = 4
    abstracts_papers = 5
    survey_submissions = 6
    attachments = 7
    misc = 8


class DataExportRequest(db.Model):
    __tablename__ = 'data_export_requests'
    __table_args__ = (db.UniqueConstraint('user_id'),
                      # If the state is 'success', there must be a file
                      db.CheckConstraint(f'(state != {DataExportRequestState.success}) OR (file_id IS NOT NULL)',
                                         'success_has_file'),
                      {'schema': 'users'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The user id of the requestor
    user_id = db.Column(
        db.ForeignKey('users.users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    #: The id of the generated zip file
    file_id = db.Column(
        db.ForeignKey('indico.files.id'),
        nullable=True,
        index=True
    )
    #: The date and time the request was created
    requested_dt = db.Column(
        UTCDateTime,
        default=now_utc,
        nullable=False
    )
    #: The items which where requested to be exported
    selected_options = db.Column(
        ARRAY(sa.Enum(DataExportOptions)),
        nullable=False,
        default=[],
    )
    # The request state
    state = db.Column(
        PyIntEnum(DataExportRequestState),
        nullable=False,
        default=DataExportRequestState.pending
    )

    user = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'data_export_request',
            lazy=True,
            uselist=False,
            cascade='all, delete-orphan',
            passive_deletes=True
        )
    )

    file = db.relationship(
        'File',
        lazy=False,
        cascade='all, delete-orphan',
        single_parent=True
    )

    @property
    def url(self):
        if f := self.file:
            return f.signed_download_url

    @property
    def is_running(self):
        return self.state == DataExportRequestState.running

    @property
    def locator(self):
        return {'user_id': self.user_id, 'id': self.id}

    def __repr__(self):
        return f'<DataExportRequest({self.id}, {self.user_id}, {self.state}, {self.file})>'
