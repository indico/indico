# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


class NewsItem(db.Model):
    __tablename__ = 'news'
    __table_args__ = {'schema': 'indico'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    content = db.Column(
        db.Text,
        nullable=False
    )

    @locator_property
    def locator(self):
        return {'news_id': self.id}

    @locator.anchor_only
    def locator(self):
        return {'_anchor': self.anchor}

    @property
    def anchor(self):
        return 'news-{}'.format(self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.title)
