# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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


class SessionPrincipal(PrincipalRolesMixin, db.Model):
    __tablename__ = 'session_principals'
    principal_backref_name = 'in_session_acls'
    principal_for = 'Session'
    unique_columns = ('session_id',)
    disallowed_protection_modes = frozenset()

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='events')

    #: The ID of the acl entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated session
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('events.sessions.id'),
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - session (Session.acl_entries)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'session_id', 'principal', read_access=False, full_access=False, roles=[])


class SessionBlockPrincipal(PrincipalRolesMixin, db.Model):
    __tablename__ = 'session_block_principals'
    principal_backref_name = 'in_session_block_acls'
    principal_for = 'SessionBlock'
    unique_columns = ('session_block_id',)

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='events')

    #: The ID of the acl entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated session block
    session_block_id = db.Column(
        db.Integer,
        db.ForeignKey('events.session_blocks.id'),
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - session_block (SessionBlock.acl_entries)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'session_block_id', 'principal', read_access=False, full_access=False, roles=[])
