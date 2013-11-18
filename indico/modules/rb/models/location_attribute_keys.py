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
Custom attribute keys for locations
"""

from indico.core.db import db


class LocationAttributeKey(db.Model):
    __tablename__ = 'location_attribute_keys'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    attributes = db.relationship('LocationAttribute',
                                 backref='key',
                                 cascade='all, delete-orphan')

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<LocationAttributeKey({0}, {1})>'.format(self.id, self.name)
