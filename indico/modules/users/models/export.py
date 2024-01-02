# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from enum import auto

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.util.date_time import now_utc
from indico.util.enum import RichIntEnum, RichStrEnum
from indico.util.i18n import L_
from indico.util.string import format_repr
from indico.web.flask.util import url_for


class DataExportRequestState(RichIntEnum):
    __titles__ = [L_('None'), L_('Running'), L_('Success'), L_('Failed'), L_('Expired')]
    none = 0  # Default value when there is no request
    running = 1
    success = 2
    failed = 3
    expired = 4  # The associated file has been deleted


class DataExportOptions(RichStrEnum):
    __titles__ = {
        'personal_data': L_('Personal data'),
        'settings': L_('Settings'),
        'contribs': L_('Contributions'),
        'note_revisions': L_('Minutes'),
        'registrations': L_('Registrations'),
        'room_booking': L_('Room booking'),
        'abstracts_papers': L_('Abstracts & Papers'),
        'survey_submissions': L_('Survey submissions'),
        'attachments': L_('Attachments & Materials'),
        'editables': L_('Editables'),
        'misc': L_('Miscellaneous'),
    }
    personal_data = auto()
    settings = auto()
    contribs = auto()
    note_revisions = auto()
    registrations = auto()
    room_booking = auto()
    abstracts_papers = auto()
    survey_submissions = auto()
    attachments = auto()
    editables = auto()
    misc = auto()


class DataExportRequest(db.Model):
    __tablename__ = 'data_export_requests'
    __table_args__ = (db.UniqueConstraint('user_id'),
                      # If the state is 'success', there must be a file attached
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
        ARRAY(sa.Enum(DataExportOptions, native_enum=False)),
        nullable=False,
        default=[],
    )
    #: Whether the files should be exported
    include_files = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    # The request state
    state = db.Column(
        PyIntEnum(DataExportRequestState),
        nullable=False,
        default=DataExportRequestState.none
    )
    # Whether the export archive exceeded the configured :data:`MAX_DATA_EXPORT_SIZE`
    max_size_exceeded = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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
        lazy=True,
        backref=db.backref(
            'data_export_of',
            lazy=True
        )
    )

    @property
    def url(self):
        if self.file:
            return url_for('users.user_data_export_download')

    @property
    def is_running(self):
        return self.state == DataExportRequestState.running

    @property
    def locator(self):
        return {'user_id': self.user_id, 'id': self.id}

    def succeed(self, file):
        self.file = file
        self.state = DataExportRequestState.success

    def fail(self):
        self.file = None
        self.state = DataExportRequestState.failed

    def delete(self):
        if self.file:
            self.file.claimed = False
        db.session.delete(self)

    def __repr__(self):
        return format_repr(self, 'id', 'user_id', 'state', 'file')
