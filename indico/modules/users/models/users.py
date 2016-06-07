# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import flash
from flask_multipass import IdentityRetrievalFailed
from sqlalchemy.event import listens_for
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session
from werkzeug.utils import cached_property

from indico.core.auth import multipass
from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.custom.unaccent import define_unaccented_lowercase_index
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.util.models import get_default_values
from indico.modules.users.models.affiliations import UserAffiliation
from indico.modules.users.models.emails import UserEmail
from indico.modules.users.models.favorites import favorite_user_table, FavoriteCategory
from indico.modules.users.models.links import UserLink
from indico.util.i18n import _
from indico.util.string import return_ascii, format_full_name
from indico.util.struct.enum import TitledIntEnum


class UserTitle(TitledIntEnum):
    __titles__ = ('', _('Mr.'), _('Ms.'), _('Mrs.'), _('Dr.'), _('Prof.'))
    none = 0
    mr = 1
    ms = 2
    mrs = 3
    dr = 4
    prof = 5

    @classmethod
    def from_legacy(cls, text):
        return next((x for x in cls if unicode(x.title) == text), None)


class PersonMixin(object):
    """Add convenience properties and methods to person classes.

    Assumes the following attributes exist:
    * first_name
    * last_name
    * title
    """

    def _get_title(self):
        """Return title text"""
        if self._title is None:
            return get_default_values(type(self))['_title'].title
        return self._title.title

    def get_full_name(self, last_name_first=True, last_name_upper=True, abbrev_first_name=True, show_title=False,
                      _show_empty_names=False):
        """Return the person's name in the specified notation.

        Note: Do not use positional arguments when calling this method.
        Always use keyword arguments!

        :param last_name_first: if "lastname, firstname" instead of
                                "firstname lastname" should be used
        :param last_name_upper: if the last name should be all-uppercase
        :param abbrev_first_name: if the first name should be abbreviated to
                                  use only the first character
        :param show_title: if the title of the person should be included
        """
        first_name = self.first_name if self.first_name or not _show_empty_names else 'Unknown'
        last_name = self.last_name if self.last_name or not _show_empty_names else 'Unknown'
        return format_full_name(first_name, last_name, self.title,
                                last_name_first=last_name_first, last_name_upper=last_name_upper,
                                abbrev_first_name=abbrev_first_name, show_title=show_title)

    #: The title of the user
    title = hybrid_property(_get_title)

    @title.expression
    def title(cls):
        return cls._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def full_name(self):
        """Return the person's name in 'Firstname Lastname' notation."""
        return self.get_full_name(last_name_first=False, last_name_upper=False, abbrev_first_name=False)

    # Convenience property to have a canonical `name` property
    name = full_name


#: Fields which can be synced as keys and a mapping to a more human
#: readable version, used for flashing messages
syncable_fields = {
    'first_name': _("first name"),
    'last_name': _("family name"),
    'affiliation': _("affiliation"),
    'address': _("address"),
    'phone': _("phone number")
}


class User(PersonMixin, db.Model):
    """Indico users"""

    # Useful when dealing with both users and groups in the same code
    is_group = False
    is_single_person = True
    is_network = False
    principal_order = 0
    principal_type = PrincipalType.user

    __tablename__ = 'users'
    __table_args__ = (db.CheckConstraint('id != merged_into_id', 'not_merged_self'),
                      db.CheckConstraint("is_pending OR (first_name != '' AND last_name != '')",
                                         'not_pending_proper_names'),
                      {'schema': 'users'})

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
    is_deleted = db.Column(
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
        secondaryjoin=(id == favorite_user_table.c.target_id) & ~is_deleted,
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

    # relationship backrefs:
    # - _all_settings (UserSetting.user)
    # - abstract_judgments (Judgment.judge)
    # - agreements (Agreement.user)
    # - attachment_files (AttachmentFile.user)
    # - attachments (Attachment.user)
    # - blockings (Blocking.created_by_user)
    # - created_events (Event.creator)
    # - event_log_entries (EventLogEntry.user)
    # - event_notes_revisions (EventNoteRevision.user)
    # - event_persons (EventPerson.user)
    # - event_reminders (EventReminder.creator)
    # - favorite_of (User.favorite_users)
    # - in_attachment_acls (AttachmentPrincipal.user)
    # - in_attachment_folder_acls (AttachmentFolderPrincipal.user)
    # - in_blocking_acls (BlockingPrincipal.user)
    # - in_category_acls (CategoryPrincipal.user)
    # - in_contribution_acls (ContributionPrincipal.user)
    # - in_event_acls (EventPrincipal.user)
    # - in_event_settings_acls (EventSettingPrincipal.user)
    # - in_session_acls (SessionPrincipal.user)
    # - in_settings_acls (SettingPrincipal.user)
    # - local_groups (LocalGroup.members)
    # - merged_from_users (User.merged_into_user)
    # - oauth_tokens (OAuthToken.user)
    # - owned_rooms (Room.owner)
    # - paper_reviewing_roles (PaperReviewingRole.user)
    # - registrations (Registration.user)
    # - requests_created (Request.created_by_user)
    # - requests_processed (Request.processed_by_user)
    # - reservations (Reservation.created_by_user)
    # - reservations_booked_for (Reservation.booked_for_user)
    # - static_sites (StaticSite.creator)
    # - survey_submissions (SurveySubmission.user)
    # - vc_rooms (VCRoom.created_by_user)

    @property
    def as_principal(self):
        """The serializable principal identifier of this user"""
        return 'User', self.id

    @property
    def as_avatar(self):
        # TODO: remove this after DB is free of Avatars
        from indico.modules.users.legacy import AvatarUserWrapper
        avatar = AvatarUserWrapper(self.id)

        # avoid garbage collection
        avatar.user
        return avatar

    as_legacy = as_avatar

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
        identities = sorted(self.local_identities, key=attrgetter('safe_last_login_dt'), reverse=True)
        return identities[0] if identities else None

    @property
    def secondary_local_identities(self):
        """The local identities of the user except the main one"""
        return self.local_identities - {self.local_identity}

    @property
    def locator(self):
        return {'user_id': self.id}

    @cached_property
    def settings(self):
        """Returns the user settings proxy for this user"""
        from indico.modules.users import user_settings
        return user_settings.bind(self)

    @property
    def synced_fields(self):
        """The fields of the user whose values are currently synced.

        This set is always a subset of the synced fields define in
        synced fields of the idp in 'indico.conf'.
        """
        synced_fields = self.settings.get('synced_fields')
        # If synced_fields is missing or None, then all fields are synced
        if synced_fields is None:
            return multipass.synced_fields
        else:
            return set(synced_fields) & multipass.synced_fields

    @synced_fields.setter
    def synced_fields(self, value):
        value = set(value) & multipass.synced_fields
        if value == multipass.synced_fields:
            self.settings.delete('synced_fields')
        else:
            self.settings.set('synced_fields', list(value))

    @property
    def synced_values(self):
        """The values from the synced identity for the user.

        Those values are not the actual user's values and might differ
        if they are not set as synchronized.
        """
        identity = self._get_synced_identity(refresh=False)
        if identity is None:
            return {}
        return {field: (identity.data.get(field) or '') for field in multipass.synced_fields}

    def __contains__(self, user):
        """Convenience method for `user in user_or_group`."""
        return self == user

    @return_ascii
    def __repr__(self):
        return '<User({}, {}, {}, {})>'.format(self.id, self.first_name, self.last_name, self.email)

    def can_be_modified(self, user):
        """If this user can be modified by the given user"""
        return self == user or user.is_admin

    def iter_identifiers(self, check_providers=False, providers=None):
        """Yields ``(provider, identifier)`` tuples for the user.

        :param check_providers: If True, providers are searched for
                                additional identifiers once all existing
                                identifiers have been yielded.
        :param providers: May be a set containing provider names to
                          get only identifiers from the specified
                          providers.
        """
        done = set()
        for identity in self.identities:
            if providers is not None and identity.provider not in providers:
                continue
            item = (identity.provider, identity.identifier)
            done.add(item)
            yield item
        if not check_providers:
            return
        for identity_info in multipass.search_identities(providers=providers, exact=True, email=self.all_emails):
            item = (identity_info.provider.name, identity_info.identifier)
            if item not in done:
                yield item

    def get_full_name(self, *args, **kwargs):
        kwargs['_show_empty_names'] = True
        return super(User, self).get_full_name(*args, **kwargs)

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

    def synchronize_data(self, refresh=False):
        """Synchronize the fields of the user from the sync identity.

        This will take only into account :attr:`synced_fields`.

        :param refresh: bool -- Whether to refresh the synced identity
                        with the sync provider before instead of using
                        the stored data. (Only if the sync provider
                        supports refresh.)
        """
        identity = self._get_synced_identity(refresh=refresh)
        if identity is None:
            return
        for field in self.synced_fields:
            old_value = getattr(self, field)
            new_value = identity.data.get(field) or ''
            if field in ('first_name', 'last_name') and not new_value:
                continue
            if old_value == new_value:
                continue
            flash(_("Your {field_name} has been synchronised from '{old_value}' to '{new_value}'.").format(
                  field_name=syncable_fields[field], old_value=old_value, new_value=new_value))
            setattr(self, field, new_value)

    def _get_synced_identity(self, refresh=False):
        sync_provider = multipass.sync_provider
        if sync_provider is None:
            return None
        identities = sorted([x for x in self.identities if x.provider == sync_provider.name],
                            key=attrgetter('safe_last_login_dt'), reverse=True)
        if not identities:
            return None
        identity = identities[0]
        if refresh and identity.multipass_data is not None:
            try:
                identity_info = sync_provider.refresh_identity(identity.identifier, identity.multipass_data)
            except IdentityRetrievalFailed:
                identity_info = None
            if identity_info:
                identity.data = identity_info.data
        return identity


@listens_for(User._primary_email, 'set')
@listens_for(User._secondary_emails, 'append')
def _user_email_added(target, value, *unused):
    # Make sure that a newly added email has the same deletion state as the user itself
    value.is_user_deleted = target.is_deleted


@listens_for(User._primary_email, 'set')
@listens_for(User._secondary_emails, 'append')
@listens_for(User._secondary_emails, 'remove')
def _user_email_changed(target, value, *unused):
    # all_emails is out of sync when changing the emails
    sess = object_session(target)
    if sess is not None:
        sess.expire(target, ['_all_emails'])


@listens_for(User.is_deleted, 'set')
def _user_deleted(target, value, *unused):
    # Reflect the user deletion state in the email table.
    # Not using _all_emails here since it only contains newly added emails after an expire/commit
    if target._primary_email:
        target._primary_email.is_user_deleted = value
    for email in target._secondary_emails:
        email.is_user_deleted = value


define_unaccented_lowercase_index(User.first_name)
define_unaccented_lowercase_index(User.last_name)
define_unaccented_lowercase_index(User.phone)
define_unaccented_lowercase_index(User.address)
