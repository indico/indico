# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args


class MenuEntryPrincipal(PrincipalMixin, db.Model):
    allow_event_roles = True
    allow_category_roles = True
    allow_registration_forms = True

    __tablename__ = 'menu_entry_principals'
    principal_backref_name = 'in_menu_entry_acls'
    unique_columns = ('menu_entry_id',)

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='events')

    #: The ID of the acl entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated menu entry
    menu_entry_id = db.Column(
        db.Integer,
        db.ForeignKey('events.menu_entries.id'),
        nullable=False
    )

    # relationship backrefs:
    # - menu_entry (MenuEntry.acl_entries)

    def __repr__(self):
        return f'<MenuEntryPrincipal({self.id}, {self.menu_entry_id}, {self.principal})>'
