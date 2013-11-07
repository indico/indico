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
Custom attribute keys for rooms
"""

from indico.core.db import db


class RoomAttributeKey(db.Model):
    __tablename__ = 'room_attribute_keys'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    attributes = db.relationship('RoomAttribute',
                                 backref='key',
                                 cascade='all, delete-orphan')

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<RoomAttributeKey({0}, {1})>'.format(self.id, self.name)

    def addAttribute(self, attribute):
        self.attributes.append(attribute)

    def removeAttribute(self, attribute):
        self.attributes.remove(attribute)

    def clearAttributes(self):
        del self.attributes[:]

    @staticmethod
    def getAllKeys():
        return RoomAttributeKey.query.all()

    @staticmethod
    def getAllKeyNames():
        # TODO: replace with projection
        return [k.name for k in RoomAttributeKey.getAllKeys()]

    @staticmethod
    def getKeysByName(name):
        return RoomAttributeKey.query.filter(RoomAttributeKey.name == name)

    @staticmethod
    def getKeyById(kid):
        return RoomAttributeKey.query.get(kid)
