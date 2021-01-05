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


class TrackPrincipal(PrincipalPermissionsMixin, db.Model):
    __tablename__ = 'track_principals'
    principal_backref_name = 'in_track_acls'
    principal_for = 'Track'
    unique_columns = ('track_id',)
    allow_event_roles = True
    allow_category_roles = True

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='events')

    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        return (
            db.CheckConstraint('NOT read_access', 'no_read_access'),
            db.CheckConstraint('NOT full_access', 'no_full_access')
        )

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    track_id = db.Column(
        db.Integer,
        db.ForeignKey('events.tracks.id'),
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - track (Track.acl_entries)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'track_id', 'principal', permissions=[])
