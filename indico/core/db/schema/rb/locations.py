# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

"""
Holder of rooms in a place and its map view related data
"""

from indico.core.db.schema import db


class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False)
    support_emails = db.Column(db.String)

    aspects = db.relationship('Aspect',
                              backref='location',
                              cascade='all, delete-orphan')

    default_aspect_id = db.Column(db.Integer, db.ForeignKey('aspects.id',
                                                            use_alter=True,
                                                            name='fk_default_aspect_id'))

    rooms = db.relationship('Room',
                            backref='location',
                            cascade='all, delete-orphan')

    def __repr__(self):
        return '<Location({0}, {1}, {2})>'.format(self.id, self.default_aspect_id,
                                                  self.name)
