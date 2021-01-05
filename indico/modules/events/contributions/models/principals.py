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
from indico.util.string import format_repr, return_ascii


class ContributionPrincipal(PrincipalPermissionsMixin, db.Model):
    __tablename__ = 'contribution_principals'
    principal_backref_name = 'in_contribution_acls'
    principal_for = 'Contribution'
    unique_columns = ('contribution_id',)
    disallowed_protection_modes = frozenset()
    allow_emails = True
    allow_event_roles = True
    allow_category_roles = True
    allow_registration_forms = True

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='events')

    #: The ID of the acl entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated contribution
    contribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - contribution (Contribution.acl_entries)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'contribution_id', 'principal', read_access=False, full_access=False,
                           permissions=[])
