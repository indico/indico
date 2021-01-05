# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalPermissionsMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.decorators import strict_classproperty
from indico.util.string import format_repr, return_ascii


class RoomPrincipal(PrincipalPermissionsMixin, db.Model):
    __tablename__ = 'room_principals'
    principal_backref_name = 'in_room_acls'
    principal_for = 'Room'
    unique_columns = ('room_id',)

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='roombooking')

    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        # Since all rooms are visible to anyone who can access room booking,
        # we do not use the read_access permission.
        return db.CheckConstraint('NOT read_access', 'no_read_access'),

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    room_id = db.Column(
        db.ForeignKey('roombooking.rooms.id'),
        index=True,
        nullable=False
    )

    # relationship backrefs:
    # - room (Room.acl_entries)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'room_id', 'principal', read_access=False, full_access=False, permissions=[])
