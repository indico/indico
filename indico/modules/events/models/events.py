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

from sqlalchemy.dialects.postgresql import TSVECTOR, JSON

from indico.core.db.sqlalchemy import db
from indico.util.caching import memoize_request


class Event(db.Model):

    __tablename__ = 'events'
    __table_args__ = (db.Index(None, 'title_vector', postgresql_using='gin'),
                      {'schema': 'events'})

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=False
    )

    @property
    def locator(self):
        return {'confId': self.id}

    @property
    def title(self):
        return self.title_vector

    @property
    @memoize_request
    def as_legacy(self):
        """
        Return a legacy ``Conference`` object (ZODB)
        """
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(self.id)

    @title.setter
    def title(self, title):
        self.title_vector = db.func.to_tsvector('simple', title)

    title_vector = db.Column(
        TSVECTOR
    )
    start_date = db.Column(
        db.DateTime,
        nullable=False,
        index=True
    )
    end_date = db.Column(
        db.DateTime,
        nullable=False,
        index=True
    )
    logo = db.deferred(db.Column(
        db.LargeBinary,
        nullable=True
    ))
    logo_metadata = db.Column(
        JSON,
        nullable=True
    )

    @property
    def has_logo(self):
        return self.logo_metadata is not None

    # relationship backrefs:
    # - layout_images (Image.event)
