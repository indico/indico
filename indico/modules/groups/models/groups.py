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
from indico.util.string import return_ascii


class LocalGroup(db.Model):
    __tablename__ = 'groups'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_groups_name_lower', db.func.lower(cls.name), unique=True),
                {'schema': 'users'})

    #: the unique id of the group
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: the name of the group
    name = db.Column(
        db.String,
        nullable=False,
        index=True
    )

    #: the local groups this user belongs to
    members = db.relationship(
        'User',
        secondary='users.group_members',
        lazy=True,
        collection_class=set,
        backref=db.backref('local_groups', lazy=True, collection_class=set),
    )

    # relationship backrefs:
    # - in_attachment_acls (AttachmentPrincipal.local_group)
    # - in_attachment_folder_acls (AttachmentFolderPrincipal.local_group)
    # - in_blocking_acls (BlockingPrincipal.local_group)
    # - in_category_acls (CategoryPrincipal.local_group)
    # - in_contribution_acls (ContributionPrincipal.local_group)
    # - in_event_acls (EventPrincipal.local_group)
    # - in_event_settings_acls (EventSettingPrincipal.local_group)
    # - in_session_acls (SessionPrincipal.local_group)
    # - in_settings_acls (SettingPrincipal.local_group)

    @return_ascii
    def __repr__(self):
        return '<LocalGroup({}, {})>'.format(self.id, self.name)

    @property
    def proxy(self):
        """Returns a GroupProxy wrapping this group"""
        from indico.modules.groups import GroupProxy
        return GroupProxy(self.id, _group=self)


group_members_table = db.Table(
    'group_members',
    db.metadata,
    db.Column(
        'group_id',
        db.Integer,
        db.ForeignKey('users.groups.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    db.Column(
        'user_id',
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        nullable=False,
        index=True
    ),
    schema='users'
)
