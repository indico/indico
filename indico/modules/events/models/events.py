# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db.sqlalchemy import db
from indico.modules.events.logs import EventLogEntry
from indico.util.caching import memoize_request
from indico.util.string import return_ascii


class Event(db.Model):
    __tablename__ = 'events'
    __table_args__ = (db.CheckConstraint("(logo IS NULL) = (logo_metadata::text = 'null')", 'valid_logo'),
                      {'schema': 'events'})

    #: The ID of the event
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: If the event has been deleted
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The metadata of the logo (size, file_name, content_type)
    logo_metadata = db.Column(
        JSON,
        nullable=False,
        default=None
    )
    #: The logo's raw image data
    logo = db.deferred(db.Column(
        db.LargeBinary,
        nullable=True
    ))

    # relationship backrefs:
    # - layout_images (ImageFile.event_new)
    # - layout_stylesheets (StylesheetFile.event_new)
    # - menu_entries (MenuEntry.event_new)

    @property
    @memoize_request
    def as_legacy(self):
        """Returns a legacy `Conference` object (ZODB)"""
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(self.id, None)

    @property
    def has_logo(self):
        return self.logo_metadata is not None

    @property
    def locator(self):
        return {'confId': self.id}

    def log(self, realm, kind, module, summary, user=None, type_='simple', data=None):
        """Creates a new log entry for the event

        :param realm: A value from :class:`.EventLogRealm` indicating
                      the realm of the action.
        :param kind: A value from :class:`.EventLogKind` indicating
                     the kind of the action that was performed.
        :param module: A human-friendly string describing the module
                       related to the action.
        :param summary: A one-line summary describing the logged action.
        :param user: The user who performed the action.
        :param type_: The type of the log entry. This is used for custom
                      rendering of the log message/data
        :param data: JSON-serializable data specific to the log type.

        In most cases the ``simple`` log type is fine. For this type,
        any items from data will be shown in the detailed view of the
        log entry.  You may either use a dict (which will be sorted)
        alphabetically or a list of ``key, value`` pairs which will
        be displayed in the given order.
        """
        db.session.add(EventLogEntry(event_id=self.id, user=user, realm=realm, kind=kind, module=module, type=type_,
                                     summary=summary, data=data or {}))

    @return_ascii
    def __repr__(self):
        return '<Event({})>'.format(self.id)
