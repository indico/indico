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

    @return_ascii
    def __repr__(self):
        return '<Event({})>'.format(self.id)
