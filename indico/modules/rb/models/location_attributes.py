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
Custom attributes for locations
"""

from indico.core.db import db
from indico.modules.rb.models import utils


class LocationAttribute(utils.JSONStringBridgeMixin, db.Model):
    __tablename__ = 'location_attributes'

    # columns

    key_id = db.Column(
        db.Integer,
        db.ForeignKey('location_attribute_keys.id'),
        nullable=False,
        primary_key=True
    )
    raw_data = db.Column(
        db.String,
        nullable=False
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('locations.id'),
        primary_key=True,
        nullable=False
    )

    def __str__(self):
        return self.value

    def __repr__(self):
        return '<LocationAttribute({0}, {1}, {2})>'.format(
            self.location_id,
            self.key_id,
            self.value
        )
