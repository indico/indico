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
Custom attribute keys for reservations
"""

from indico.core.db import db


class ReservationAttributeKey(db.Model):
    __tablename__ = 'reservation_attribute_keys'

    # columns

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False,
        unique=True,
        index=True
    )

    # relationships

    attributes = db.relationship(
        'ReservationAttribute',
        backref='key',
        cascade='all, delete-orphan'
    )

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<ReservationAttributeKey({0}, {1})>'.format(
            self.id,
            self.name
        )

    def addAttribute(self, attribute):
        self.attributes.append(attribute)

    def removeAttribute(self, attribute):
        self.attributes.remove(attribute)

    @staticmethod
    def getKeyByName(name):
        return ReservationAttributeKey.query.filter_by(name=name).first()

    @staticmethod
    def getKeyById(kid):
        return ReservationAttributeKey.query.get(kid)

    @staticmethod
    def getAllKeys():
        return ReservationAttributeKey.query.all()
