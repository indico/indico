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

from operator import attrgetter

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.utils import cached_property

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.modules.users.models.affiliations import UserAffiliation
from indico.modules.users.models.emails import UserEmail
from indico.modules.users.models.favorites import favorite_user_table, FavoriteCategory
from indico.modules.users.models.links import UserLink
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import TitledIntEnum


class UserTitle(TitledIntEnum):
    __titles__ = ('', _('Mr.'), _('Ms.'), _('Mrs.'), _('Dr.'), _('Prof.'))
    none = 0
    mr = 1
    ms = 2
    mrs = 3
    dr = 4
    prof = 5


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
    # the title of the user - you usually want the `title` property!
    _title = db.Column(
        'title',
        PyIntEnum(UserTitle),
        nullable=False,
        default=UserTitle.none
    )
    #: the phone number of the user
    phone = db.Column(
        db.String,
        nullable=False,
        default=''
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
    #: if the user is pending (e.g. never logged in, only added to some list)
    is_pending = db.Column(
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

    _affiliation = db.relationship(
        'UserAffiliation',
        lazy=False,
        uselist=False,
        cascade='all, delete-orphan',
        backref=db.backref('user', lazy=True)
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
        collection_class=set,
        primaryjoin='(User.id == UserEmail.user_id) & ~UserEmail.is_primary'
    )
    _all_emails = db.relationship(
        'UserEmail',
        lazy=True,
        viewonly=True,
        primaryjoin='User.id == UserEmail.user_id',
        collection_class=set,
        backref=db.backref('user', lazy=False)
    )
    #: the affiliation of the user
    affiliation = association_proxy('_affiliation', 'name', creator=lambda v: UserAffiliation(name=v))
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
        collection_class=set,
        backref=db.backref('favorite_of', lazy=True, collection_class=set),
    )
    _favorite_categories = db.relationship(
        'FavoriteCategory',
        lazy=True,
        cascade='all, delete-orphan',
        collection_class=set
    )
    #: the users's favorite categories
    favorite_categories = association_proxy('_favorite_categories', 'target',
                                            creator=lambda x: FavoriteCategory(target=x))
    #: the legacy objects the user is connected to
    linked_objects = db.relationship(
        'UserLink',
        lazy='dynamic',
        cascade='all, delete-orphan',
        backref=db.backref('user', lazy=True)
    )
    #: the active API key of the user
    api_key = db.relationship(
        'APIKey',
        lazy=True,
        uselist=False,
        cascade='all, delete-orphan',
        primaryjoin='(User.id == APIKey.user_id) & APIKey.is_active',
        back_populates='user'
    )
    #: the previous API keys of the user
    old_api_keys = db.relationship(
        'APIKey',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='APIKey.created_dt.desc()',
        primaryjoin='(User.id == APIKey.user_id) & ~APIKey.is_active',
        back_populates='user'
    )
    #: the identities used by this user
    identities = db.relationship(
        'Identity',
        lazy=True,
        cascade='all, delete-orphan',
        collection_class=set,
        backref=db.backref('user', lazy=False)
    )
    #: the local groups this user belongs to
    local_groups = db.relationship(
        'LocalGroup',
        secondary='users.group_members',
        lazy=True,
        collection_class=set,
        backref=db.backref('members', lazy=True, collection_class=set),
    )

    @property
    def as_principal(self):
        """The serializable principal identifier of this user"""
        return 'User', self.id

    @property
    def as_avatar(self):
        # TODO: remove this after DB is free of Avatars
        from indico.modules.users.legacy import AvatarUserWrapper
        return AvatarUserWrapper(self.id)

    @property
    def external_identities(self):
        """The external identities of the user"""
        return {x for x in self.identities if x.provider != 'indico'}

    @property
    def local_identities(self):
        """The local identities of the user"""
        return {x for x in self.identities if x.provider == 'indico'}

    @property
    def local_identity(self):
        """The main (most recently used) local identity"""
        identities = sorted(self.local_identities, key=attrgetter('last_login_dt'), reverse=True)
        return identities[0] if identities else None

    @property
    def secondary_local_identities(self):
        """The local identities of the user except the main one"""
        return self.local_identities - {self.local_identity}

    @property
    def locator(self):
        return {'user_id': self.id}

    @hybrid_property
    def title(self):
        """the title of the user"""
        return self._title.title

    @title.expression
    def title(cls):
        return cls._title

    @title.setter
    def title(self, value):
        self._title = value

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

    @cached_property
    def settings(self):
        """Returns the user settings proxy for this user"""
        from indico.modules.users import user_settings
        return user_settings.bind(self)

    @property
    def full_name(self):
        """Returns the user's name in 'Firstname Lastname' notation."""
        return self.get_full_name(last_name_first=False, last_name_upper=False, abbrev_first_name=False)

    @return_ascii
    def __repr__(self):
        return '<User({}, {}, {}, {})>'.format(self.id, self.first_name, self.last_name, self.email)

    def can_be_modified(self, user):
        """If this user can be modified by the given user"""
        return self == user or user.is_admin

    def get_full_name(self, last_name_first=True, last_name_upper=True, abbrev_first_name=True, show_title=False):
        """Returns the user's name in the specified notation.

        Note: Do not use positional arguments when calling this method.
        Always use keyword arguments!

        :param last_name_first: if "lastname, firstname" instead of
                                "firstname lastname" should be used
        :param last_name_upper: if the last name should be all-uppercase
        :param abbrev_first_name: if the first name should be abbreviated to
                                  use only the first character
        :param show_title: if the title of the user should be included
        """
        last_name = self.last_name.upper() if last_name_upper else self.last_name
        first_name = '{}.'.format(self.first_name[0].upper()) if abbrev_first_name else self.first_name
        full_name = '{}, {}'.format(last_name, first_name) if last_name_first else '{} {}'.format(first_name, last_name)
        return full_name if not show_title or not self.title else '{} {}'.format(self.title, full_name)

    def make_email_primary(self, email):
        """Promotes a secondary email address to the primary email address

        :param email: an email address that is currently a secondary email
        """
        secondary = next((x for x in self._secondary_emails if x.email == email), None)
        if secondary is None:
            raise ValueError('email is not a secondary email address')
        self._primary_email.is_primary = False
        db.session.flush()
        secondary.is_primary = True
        db.session.flush()

    def is_in_group(self, group):
        """Checks if the user is in a group

        :param group: A :class:`GroupProxy`
        """
        return group.has_member(self)

    def get_linked_roles(self, type_):
        """Retrieves the roles the user is linked to for a given type"""
        return UserLink.get_linked_roles(self, type_)

    def get_linked_objects(self, type_, role):
        """Retrieves linked objects for the user"""
        return UserLink.get_links(self, type_, role)

    def link_to(self, obj, role):
        """Adds a link between the user and an object

        :param obj: a legacy object
        :param role: the role to use in the link
        """
        return UserLink.create_link(self, obj, role)

    def unlink_to(self, obj, role):
        """Removes a link between the user and an object

        :param obj: a legacy object
        :param role: the role to use in the link
        """
        return UserLink.remove_link(self, obj, role)
