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
A view of map of rooms in a specific location
"""

from indico.core.db import db


class Aspect(db.Model):
    __tablename__ = 'aspects'

    # columns

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    center_latitude = db.Column(
        db.String,
        nullable=False
    )
    center_longitude = db.Column(
        db.String,
        nullable=False
    )
    zoom_level = db.Column(
        db.SmallInteger,
        nullable=False
    )
    top_left_latitude = db.Column(
        db.String,
        nullable=False
    )
    top_left_longitude = db.Column(
        db.String,
        nullable=False
    )
    bottom_right_latitude = db.Column(
        db.String,
        nullable=False
    )
    bottom_right_longitude = db.Column(
        db.String,
        nullable=False
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey('locations.id'),
        nullable=False
    )

    # core

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Aspect({0}, {1}, {2})>'.format(
            self.id,
            self.location_id,
            self.name
        )

    # getters

    @staticmethod
    def getAspectById(aid):
        return Aspect.query.get(aid)

    @staticmethod
    def getAspectsByName(name):
        return Aspect.query.filter(Aspect.name == name).all()
