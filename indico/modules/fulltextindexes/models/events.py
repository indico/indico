# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from indico.core.db.sqlalchemy import db
from sqlalchemy.dialects.postgresql import TSVECTOR


class IndexedEvent(db.Model):

    __tablename__ = 'event_index'
    __table_args__ = (db.Index('title_vector_idx', 'title_vector', postgresql_using='gin'),
                      {'schema': 'events'})

    id = db.Column(
        db.String,
        primary_key=True
    )

    @property
    def title(self):
        return self.title_vector

    @title.setter
    def title(self, title):
        self.title_vector = db.func.to_tsvector('simple', title)

    title_vector = db.Column(
        TSVECTOR
    )
    start_date = db.Column(
        db.DateTime
    )
