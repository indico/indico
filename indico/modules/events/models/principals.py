# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalPermissionsMixin, PrincipalType
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.string import format_repr


class EventPrincipal(PrincipalPermissionsMixin, db.Model):
    __tablename__ = 'principals'
    principal_backref_name = 'in_event_acls'
    principal_for = 'Event'
    unique_columns = ('event_id',)
    allow_emails = True
    allow_networks = True
    allow_event_roles = True
    allow_category_roles = True
    allow_registration_forms = True

    @declared_attr
    def __table_args__(cls):
        permissions = "ARRAY['paper_editing', 'slides_editing', 'poster_editing']"
        condition = (
            f'type NOT IN ({PrincipalType.local_group}, {PrincipalType.multipass_group}) OR '
            f'(NOT (permissions::text[] && {permissions}))'
        )
        group_perm_constraint = db.CheckConstraint(condition, 'disallow_group_editor_permissions')
        return (group_perm_constraint, *auto_table_args(cls, schema='events'))

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

    def __repr__(self):
        return format_repr(self, 'id', 'event_id', 'principal', read_access=False, full_access=False, permissions=[])
