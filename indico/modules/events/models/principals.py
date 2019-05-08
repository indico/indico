# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalPermissionsMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.string import format_repr, return_ascii


class EventPrincipal(PrincipalPermissionsMixin, db.Model):
    __tablename__ = 'principals'
    principal_backref_name = 'in_event_acls'
    principal_for = 'Event'
    unique_columns = ('event_id',)
    allow_emails = True
    allow_networks = True
    allow_event_roles = True

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='events')

    #: The ID of the acl entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated event
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - event (Event.acl_entries)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'principal', read_access=False, full_access=False, permissions=[])
