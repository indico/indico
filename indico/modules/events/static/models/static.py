# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import posixpath

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.storage import StoredFileMixin
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.string import format_repr, return_ascii, strict_unicode
from indico.util.struct.enum import RichIntEnum


class StaticSiteState(RichIntEnum):
    __titles__ = [_("Pending"), _("Running"), _("Success"), _("Failed"), _("Expired")]
    pending = 0
    running = 1
    success = 2
    failed = 3
    expired = 4


class StaticSite(StoredFileMixin, db.Model):
    """Static site for an Indico event."""

    __tablename__ = 'static_sites'
    __table_args__ = {'schema': 'events'}

    # StoredFileMixin settings
    add_file_date_column = False
    file_required = False

    #: Entry ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: ID of the event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    #: The state of the static site (a :class:`StaticSiteState` member)
    state = db.Column(
        PyIntEnum(StaticSiteState),
        default=StaticSiteState.pending,
        nullable=False
    )
    #: The date and time the static site was requested
    requested_dt = db.Column(
        UTCDateTime,
        default=now_utc,
        nullable=False
    )
    #: ID of the user who created the static site
    creator_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )

    #: The user who created the static site
    creator = db.relationship(
        'User',
        lazy=False,
        backref=db.backref(
            'static_sites',
            lazy='dynamic'
        )
    )
    #: The Event this static site is associated with
    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'static_sites',
            lazy='dynamic'
        )
    )

    @property
    def locator(self):
        return {'confId': self.event_id, 'id': self.id}

    def _build_storage_path(self):
        path_segments = ['event', strict_unicode(self.event.id), 'static']
        self.assign_id()
        filename = '{}-{}'.format(self.id, self.filename)
        path = posixpath.join(*(path_segments + [filename]))
        return config.STATIC_SITE_STORAGE, path

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'state')
