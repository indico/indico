# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


class RoomFeature(db.Model):
    __tablename__ = 'features'
    __table_args__ = {'schema': 'roombooking'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String,
        nullable=False,
        index=True,
        unique=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    icon = db.Column(
        db.String,
        nullable=False,
        default=''
    )

    # relationship backrefs:
    # - equipment_types (EquipmentType.features)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'name', _text=self.title)
