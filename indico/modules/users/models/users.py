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

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.utils import cached_property

from indico.core.db import db
from indico.modules.users.models.emails import UserEmail
from indico.modules.users.models.favorites import favorite_user_table, FavoriteCategory
from indico.util.caching import memoize_request
from indico.util.string import return_ascii


class User(db.Model):
    """Indico users"""
    __tablename__ = 'users'
    __table_args__ = {'schema': 'users'}

    #: the unique id of the user
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: the first name of the user
    first_name = db.Column(
        db.String,
        nullable=False,
        index=True
    )
    #: the last/family name of the user
    last_name = db.Column(
        db.String,
        nullable=False,
        index=True
    )
    #: the phone number of the user
    phone = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    #: the affiliation of the user
    affiliation = db.Column(
        db.String,
        nullable=False,
        default='',
        index=True
    )
    #: the address of the user
    address = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: the id of the user this user has been merged into
    merged_into_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=True
    )
    #: if the user is an administrator with unrestricted access to everything
    is_admin = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True
    )
    #: if the user has been blocked
    is_blocked = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: if the user is deleted (e.g. due to a merge)
    _is_deleted = db.Column(
        'is_deleted',
        db.Boolean,
        nullable=False,
        default=False
    )

    _primary_email = db.relationship(
        'UserEmail',
        lazy=False,
        uselist=False,
        cascade='all, delete-orphan',
        primaryjoin='(User.id == UserEmail.user_id) & UserEmail.is_primary'
    )
    _secondary_emails = db.relationship(
        'UserEmail',
        lazy=True,
        cascade='all, delete-orphan',
        primaryjoin='(User.id == UserEmail.user_id) & ~UserEmail.is_primary'
    )
    _all_emails = db.relationship(
        'UserEmail',
        lazy=True,
        viewonly=True,
        primaryjoin='User.id == UserEmail.user_id',
        backref=db.backref('user', lazy=False)
    )
    #: the primary email address of the user
    email = association_proxy('_primary_email', 'email', creator=lambda v: UserEmail(email=v, is_primary=True))
    #: any additional emails the user might have
    secondary_emails = association_proxy('_secondary_emails', 'email', creator=lambda v: UserEmail(email=v))
    #: all emails of the user. read-only; use it only for searching by email! also, do not use it between
    #: modifying `email` or `secondary_emails` and a session expire/commit!
    all_emails = association_proxy('_all_emails', 'email')  # read-only!

    #: the user this user has been merged into
    merged_into_user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref('merged_from_users', lazy=True),
        remote_side='User.id',
    )
    #: the users's favorite users
    favorite_users = db.relationship(
        'User',
        secondary=favorite_user_table,
        primaryjoin=id == favorite_user_table.c.user_id,
        secondaryjoin=(id == favorite_user_table.c.target_id) & ~_is_deleted,
        lazy=True,
        backref=db.backref('favorite_of', lazy=True),
    )
    _favorite_categories = db.relationship(
        'FavoriteCategory',
        lazy=True,
        cascade='all, delete-orphan'
    )
    #: the users's favorite categories
    favorite_categories = association_proxy('_favorite_categories', 'target',
                                            creator=lambda x: FavoriteCategory(target=x))

    @hybrid_property
    def is_deleted(self):
        return self._is_deleted

    @is_deleted.setter
    def is_deleted(self, value):
        self._is_deleted = value
        # not using _all_emails here since it only contains newly added emails after an expire/commit
        if self._primary_email:
            self._primary_email.is_user_deleted = value
        for email in self._secondary_emails:
            email.is_user_deleted = value

    @property
    @memoize_request
    def api_key(self):
        # TODO: convert to relationship
        from indico.modules.api.models.keys import APIKey
        return APIKey.find_first(user_id=self.id, is_active=True)

    @cached_property
    def settings(self):
        """Returns the user settings proxy for this user"""
        from indico.modules.users import user_settings
        return user_settings.bind(self)

    @return_ascii
    def __repr__(self):
        return '<User({}, {}, {}, {})>'.format(self.id, self.first_name, self.last_name, self.email)
