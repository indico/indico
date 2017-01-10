# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalRolesMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.util.string import return_ascii, format_repr


class CategoryPrincipal(PrincipalRolesMixin, db.Model):
    __tablename__ = 'principals'
    principal_backref_name = 'in_category_acls'
    principal_for = 'Category'
    unique_columns = ('category_id',)
    allow_networks = True

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='categories')

    #: The ID of the acl entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated event
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - category (Category.acl_entries)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'category_id', 'principal', read_access=False, full_access=False, roles=[])
