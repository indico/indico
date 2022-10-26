# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import itertools
from contextlib import contextmanager
from enum import Enum
from operator import attrgetter
from uuid import uuid4

from flask import flash, g, has_request_context, session
from flask_multipass import IdentityRetrievalFailed
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.event import listens_for
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import object_session
from sqlalchemy.sql import select
from werkzeug.utils import cached_property

from indico.core import signals
from indico.core.auth import multipass
from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.custom.unaccent import define_unaccented_lowercase_index
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.util.models import get_default_values
from indico.modules.users.models.affiliations import Affiliation
from indico.modules.users.models.emails import UserEmail
from indico.modules.users.models.favorites import favorite_category_table, favorite_event_table, favorite_user_table
from indico.util.enum import RichIntEnum
from indico.util.i18n import _, force_locale
from indico.util.locators import locator_property
from indico.util.string import format_full_name, format_repr, validate_email
from indico.web.flask.util import url_for


class UserTitle(RichIntEnum):
    __titles__ = ('', _('Mr'), _('Ms'), _('Mrs'), _('Dr'), _('Prof.'), _('Mx'))
    none = 0
    mr = 1
    ms = 2
    mrs = 3
    dr = 4
    prof = 5
    mx = 6


class NameFormat(RichIntEnum):
    __titles__ = (_('John Doe'), _('Doe, John'), _('Doe, J.'), _('J. Doe'),
                  _('John DOE'), _('DOE, John'), _('DOE, J.'), _('J. DOE'))
    first_last = 0
    last_first = 1
    last_f = 2
    f_last = 3
    first_last_upper = 4
    last_first_upper = 5
    last_f_upper = 6
    f_last_upper = 7


class ProfilePictureSource(int, Enum):
    standard = 0
    identicon = 1
    gravatar = 2
    custom = 3


class PersonMixin:
    """Add convenience properties and methods to person classes.

    Assumes the following attributes exist:
    * first_name
    * last_name
    * title
    """

    def _get_title(self):
        """Return title text."""
        if self._title is None:
            return get_default_values(type(self)).get('_title', UserTitle.none).title
        return self._title.title

    def get_full_name(self, show_title=False, last_name_first=True, last_name_upper=True,
                      abbrev_first_name=True, _show_empty_names=False):
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
        return format_full_name(first_name, last_name, self.title if show_title else None,
                                last_name_first=last_name_first, last_name_upper=last_name_upper,
                                abbrev_first_name=abbrev_first_name)

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
        return self.get_full_name(show_title=False, last_name_first=False, last_name_upper=False,
                                  abbrev_first_name=False)

    @property
    def full_name_affiliation(self):
        return f'{self.full_name} ({self.affiliation})' if self.affiliation else self.full_name

    @property
    def display_full_name(self):
        """Return the full name using the user's preferred name format."""
        if has_request_context():
            return format_display_full_name(session.user, self)
        else:
            return format_display_full_name(None, self)

    # Convenience property to have a canonical `name` property
    name = full_name

    @property
    def affiliation_details(self):
        from indico.modules.users.schemas import AffiliationSchema
        if link := getattr(self, 'affiliation_link', None):
            return AffiliationSchema().dump(link)
        else:
            return None


#: Fields which can be synced as keys and a mapping to a more human
#: readable version, used for flashing messages
syncable_fields = {
    'first_name': _('first name'),
    'last_name': _('family name'),
    'affiliation': _('affiliation'),
    'address': _('address'),
    'phone': _('phone number'),
    'email': _('primary email address'),
}


def format_display_full_name(user, obj):
    from indico.modules.events.layout import layout_settings
    name_format = layout_settings.get(g.rh.event, 'name_format') if 'rh' in g and hasattr(g.rh, 'event') else None
    if name_format is None:
        name_format = user.settings.get('name_format') if user else NameFormat.first_last
    upper = name_format in (NameFormat.first_last_upper, NameFormat.f_last_upper, NameFormat.last_f_upper,
                            NameFormat.last_first_upper)
    if name_format in (NameFormat.first_last, NameFormat.first_last_upper):
        return obj.get_full_name(last_name_first=False, last_name_upper=upper, abbrev_first_name=False)
    elif name_format in (NameFormat.last_first, NameFormat.last_first_upper):
        return obj.get_full_name(last_name_first=True, last_name_upper=upper, abbrev_first_name=False)
    elif name_format in (NameFormat.last_f, NameFormat.last_f_upper):
        return obj.get_full_name(last_name_first=True, last_name_upper=upper, abbrev_first_name=True)
    elif name_format in (NameFormat.f_last, NameFormat.f_last_upper):
        return obj.get_full_name(last_name_first=False, last_name_upper=upper, abbrev_first_name=True)
    else:
        raise ValueError(f'Invalid name format: {name_format}')


class User(PersonMixin, db.Model):
    """Indico users."""

    principal_order = 0
    principal_type = PrincipalType.user

    __tablename__ = 'users'
    __table_args__ = (db.Index(None, 'is_system', unique=True, postgresql_where=db.text('is_system')),
                      db.CheckConstraint('NOT is_system OR (NOT is_blocked AND NOT is_pending AND NOT is_deleted)',
                                         'valid_system_user'),
                      db.CheckConstraint('id != merged_into_id', 'not_merged_self'),
                      db.CheckConstraint("is_pending OR (first_name != '' AND last_name != '')",
                                         'not_pending_proper_names'),
                      db.CheckConstraint("(picture IS NULL) = (picture_metadata::text = 'null')", 'valid_picture'),
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
    #: the name of the affiliation (regardless if predefined or manually-entered)
    affiliation = db.Column(
        db.String,
        nullable=False,
        index=True,
        default=''
    )
    #: the id of the underlying predefined affiliation
    affiliation_id = db.Column(
        db.ForeignKey('indico.affiliations.id'),
        nullable=True,
        index=True
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
        nullable=True,
        index=True
    )
    #: if the user is the default system user
    is_system = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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
    #: a unique secret used to generate signed URLs
    signing_secret = db.Column(
        UUID,
        nullable=False,
        default=lambda: str(uuid4())
    )
    #: the user profile picture
    picture = db.deferred(db.Column(
        db.LargeBinary,
        nullable=True
    ))
    #: user profile picture metadata
    picture_metadata = db.Column(
        JSONB,
        nullable=False,
        default=lambda: None
    )
    #: user profile picture source
    picture_source = db.Column(
        PyIntEnum(ProfilePictureSource),
        nullable=False,
        default=ProfilePictureSource.standard,
    )

    _primary_email = db.relationship(
        'UserEmail',
        lazy=False,
        uselist=False,
        cascade='all, delete-orphan',
        primaryjoin='(User.id == UserEmail.user_id) & UserEmail.is_primary',
        overlaps='_secondary_emails'
    )
    _secondary_emails = db.relationship(
        'UserEmail',
        lazy=True,
        cascade='all, delete-orphan',
        collection_class=set,
        primaryjoin='(User.id == UserEmail.user_id) & ~UserEmail.is_primary',
        overlaps='_primary_email'
    )
    _all_emails = db.relationship(
        'UserEmail',
        lazy=True,
        viewonly=True,
        sync_backref=False,
        primaryjoin='User.id == UserEmail.user_id',
        collection_class=set,
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
    #: the predefined affiliation of the user
    affiliation_link = db.relationship(
        'Affiliation',
        lazy=False,
        backref=db.backref(
            'user_affiliations',
            lazy='dynamic',
            # disable backref cascade so the link created in `principal_from_identifier` does not
            # add the User to the session just because it's linked to an Affiliation
            cascade_backrefs=False
        )
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
    #: the users's favorite categories
    favorite_categories = db.relationship(
        'Category',
        secondary=favorite_category_table,
        lazy=True,
        collection_class=set,
        backref=db.backref('favorite_of', lazy=True, collection_class=set),
    )
    #: the user's category suggestions
    suggested_categories = db.relationship(
        'SuggestedCategory',
        lazy='dynamic',
        order_by='SuggestedCategory.score.desc()',
        cascade='all, delete-orphan',
        backref=db.backref('user', lazy=True)
    )
    #: the users's favorite events
    favorite_events = db.relationship(
        'Event',
        secondary=favorite_event_table,
        lazy=True,
        collection_class=set,
        backref=db.backref('favorite_of', lazy=True, collection_class=set),
    )
    #: the active API key of the user
    api_key = db.relationship(
        'APIKey',
        lazy=True,
        uselist=False,
        cascade='all, delete-orphan',
        primaryjoin='(User.id == APIKey.user_id) & APIKey.is_active',
        back_populates='user',
        overlaps='old_api_keys'
    )
    #: the previous API keys of the user
    old_api_keys = db.relationship(
        'APIKey',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='APIKey.created_dt.desc()',
        primaryjoin='(User.id == APIKey.user_id) & ~APIKey.is_active',
        back_populates='user',
        overlaps='api_key'
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
    # - abstract_comments (AbstractComment.user)
    # - abstract_email_log_entries (AbstractEmailLogEntry.user)
    # - abstract_reviews (AbstractReview.user)
    # - abstracts (Abstract.submitter)
    # - agreements (Agreement.user)
    # - anonymous_survey_submissions (AnonymousSurveySubmission.user)
    # - attachment_files (AttachmentFile.user)
    # - attachments (Attachment.user)
    # - blockings (Blocking.created_by_user)
    # - category_log_entries (CategoryLogEntry.user)
    # - category_roles (CategoryRole.members)
    # - content_reviewer_for_contributions (Contribution.paper_content_reviewers)
    # - created_events (Event.creator)
    # - editing_comments (EditingRevisionComment.user)
    # - editing_revisions (EditingRevision.submitter)
    # - editor_for_editables (Editable.editor)
    # - editor_for_revisions (EditingRevision.editor)
    # - event_log_entries (EventLogEntry.user)
    # - event_move_requests (EventMoveRequest.requestor)
    # - event_notes_revisions (EventNoteRevision.user)
    # - event_persons (EventPerson.user)
    # - event_reminders (EventReminder.creator)
    # - event_roles (EventRole.members)
    # - favorite_of (User.favorite_users)
    # - favorite_rooms (Room.favorite_of)
    # - in_attachment_acls (AttachmentPrincipal.user)
    # - in_attachment_folder_acls (AttachmentFolderPrincipal.user)
    # - in_blocking_acls (BlockingPrincipal.user)
    # - in_category_acls (CategoryPrincipal.user)
    # - in_contribution_acls (ContributionPrincipal.user)
    # - in_event_acls (EventPrincipal.user)
    # - in_event_settings_acls (EventSettingPrincipal.user)
    # - in_room_acls (RoomPrincipal.user)
    # - in_session_acls (SessionPrincipal.user)
    # - in_settings_acls (SettingPrincipal.user)
    # - in_track_acls (TrackPrincipal.user)
    # - judge_for_contributions (Contribution.paper_judges)
    # - judged_abstracts (Abstract.judge)
    # - judged_papers (PaperRevision.judge)
    # - layout_reviewer_for_contributions (Contribution.paper_layout_reviewers)
    # - local_groups (LocalGroup.members)
    # - merged_from_users (User.merged_into_user)
    # - moderated_event_move_requests (EventMoveRequest.moderator)
    # - modified_abstract_comments (AbstractComment.modified_by)
    # - modified_abstracts (Abstract.modified_by)
    # - modified_review_comments (PaperReviewComment.modified_by)
    # - oauth_app_links (OAuthApplicationUserLink.user)
    # - owned_rooms (Room.owner)
    # - paper_competences (PaperCompetence.user)
    # - paper_reviews (PaperReview.user)
    # - paper_revisions (PaperRevision.submitter)
    # - personal_tokens (PersonalToken.user)
    # - registrations (Registration.user)
    # - requests_created (Request.created_by_user)
    # - requests_processed (Request.processed_by_user)
    # - reservations (Reservation.created_by_user)
    # - reservations_booked_for (Reservation.booked_for_user)
    # - review_comments (PaperReviewComment.user)
    # - static_sites (StaticSite.creator)
    # - survey_submissions (SurveySubmission.user)
    # - vc_rooms (VCRoom.created_by_user)

    @staticmethod
    def get_system_user():
        return User.query.filter_by(is_system=True).one()

    @property
    def as_principal(self):
        """The serializable principal identifier of this user."""
        return 'User', self.id

    @property
    def identifier(self):
        return f'User:{self.id}'

    @property
    def avatar_bg_color(self):
        from indico.modules.users.util import get_color_for_user_id
        return get_color_for_user_id(self.id)

    @property
    def external_identities(self):
        """The external identities of the user."""
        return {x for x in self.identities if x.provider != 'indico'}

    @property
    def local_identities(self):
        """The local identities of the user."""
        return {x for x in self.identities if x.provider == 'indico'}

    @property
    def local_identity(self):
        """The main (most recently used) local identity."""
        identities = sorted(self.local_identities, key=attrgetter('safe_last_login_dt'), reverse=True)
        return identities[0] if identities else None

    @property
    def secondary_local_identities(self):
        """The local identities of the user except the main one."""
        return self.local_identities - {self.local_identity}

    @property
    def last_login_dt(self):
        """The datetime when the user last logged in."""
        if not self.identities:
            return None
        return max(self.identities, key=attrgetter('safe_last_login_dt')).last_login_dt

    @locator_property
    def locator(self):
        return {'user_id': self.id}

    @cached_property
    def settings(self):
        """Return the user settings proxy for this user."""
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

    @property
    def has_picture(self):
        return self.picture_metadata is not None

    @property
    def avatar_url(self):
        from indico.modules.users.util import get_avatar_url_from_name
        if self.is_system:
            return url_for('assets.image', filename='robot.svg')
        elif self.id is None:
            return get_avatar_url_from_name(self.first_name)
        slug = self.picture_metadata['hash'] if self.picture_metadata else 'default'
        return url_for('users.user_profile_picture_display', self, slug=slug)

    def __contains__(self, user):
        """Convenience method for `user in user_or_group`."""
        return self == user

    def __repr__(self):
        return format_repr(self, 'id', 'email', is_deleted=False, is_pending=False, _text=self.full_name)

    def can_be_modified(self, user):
        """If this user can be modified by the given user."""
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

    def get_identity(self, provider):
        """Return the first user identity which matches the given provider.

        :param provider: The id of the provider in question
        :return: The requested identity, or `None` if none is found
        """
        return next(
            (ident for ident in self.identities if ident.provider == provider),
            None
        )

    @property
    def can_get_all_multipass_groups(self):
        """
        Check whether it is possible to get all multipass groups the user is in.
        """
        return all(multipass.identity_providers[x.provider].supports_get_identity_groups
                   for x in self.identities
                   if x.provider != 'indico' and x.provider in multipass.identity_providers)

    def iter_all_multipass_groups(self):
        """Iterate over all multipass groups the user is in."""
        return itertools.chain.from_iterable(multipass.identity_providers[x.provider].get_identity_groups(x.identifier)
                                             for x in self.identities
                                             if x.provider != 'indico' and x.provider in multipass.identity_providers)

    def get_full_name(self, *args, **kwargs):
        kwargs['_show_empty_names'] = True
        return super().get_full_name(*args, **kwargs)

    def make_email_primary(self, email):
        """Promote a secondary email address to the primary email address.

        :param email: an email address that is currently a secondary email
        """
        secondary = next((x for x in self._secondary_emails if x.email == email), None)
        if secondary is None:
            raise ValueError('email is not a secondary email address')
        old = self.email
        self._primary_email.is_primary = False
        db.session.flush()
        secondary.is_primary = True
        db.session.flush()
        signals.users.primary_email_changed.send(self, old=old, new=email)

    def reset_signing_secret(self):
        self.signing_secret = str(uuid4())

    def query_personal_tokens(self, *, include_revoked=False):
        """Query the personal tokens of the user.

        :param include_revoked: whether to query revoked tokens as well
        """
        query = self.personal_tokens
        if not include_revoked:
            query = query.filter_by(revoked_dt=None)
        return query

    def synchronize_data(self, refresh=False, silent=False):
        """Synchronize the fields of the user from the sync identity.

        This will take only into account :attr:`synced_fields`.

        :param refresh: bool -- Whether to refresh the synced identity
                        with the sync provider before instead of using
                        the stored data. (Only if the sync provider
                        supports refresh.)
        :param silent: bool -- Whether to just synchronize but not flash
                       any messages
        """
        from indico.modules.users import logger
        identity = self._get_synced_identity(refresh=refresh)
        if identity is None:
            return
        if not any(identity.data.values()):
            # refuse to sync with empty identities, just in case - if there is no
            # data at all there's a good chance something is wrong!
            return
        affiliation_data = identity.data.get('affiliation_data')
        for field in self.synced_fields:
            old_value = getattr(self, field)
            new_value = identity.data.get(field) or ''
            if field == 'email':
                new_value = new_value.lower()
            if field in ('first_name', 'last_name', 'email') and not new_value:
                continue
            if field == 'affiliation':
                if affiliation_data:
                    self.affiliation_link = Affiliation.get_or_create_from_data(affiliation_data)
                else:
                    self.affiliation_link = None  # clear link to predefined affiliation
            if old_value == new_value:
                continue
            logger.info('Syncing %s for %r from %r to %r', field, self, old_value, new_value)
            if field == 'email':
                if not self._synchronize_email(new_value, silent=silent):
                    continue
            else:
                setattr(self, field, new_value)
            if not silent:
                flash(_("Your {field_name} has been synchronized from '{old_value}' to '{new_value}'.").format(
                    field_name=syncable_fields[field], old_value=old_value, new_value=new_value))

    def _synchronize_email(self, email, silent=False):
        from indico.modules.users import logger
        from indico.modules.users.tasks import update_gravatars
        from indico.modules.users.util import get_user_by_email

        if not validate_email(email, check_dns=False):
            logger.warning('Cannot sync email for %r to %r; address is invalid', self, email)
            if not silent:
                flash(_("Your email address could not be synchronized from '{old_value}' to "
                        "'{new_value}' since the new email address is not valid.")
                      .format(old_value=self.email, new_value=email), 'warning')
            return False

        if email not in self.secondary_emails:
            if other := get_user_by_email(email):
                logger.warning('Cannot sync email for %r to %r; already used by %r', self, email, other)
                if not silent:
                    flash(_("Your email address could not be synchronized from '{old_value}' to "
                            "'{new_value}' due to a conflict with another Indico profile.")
                          .format(old_value=self.email, new_value=email), 'warning')
                return False
            self.secondary_emails.add(email)
            signals.users.email_added.send(self, email=email, silent=silent)

        self.make_email_primary(email)
        if self.picture_source in (ProfilePictureSource.gravatar, ProfilePictureSource.identicon):
            update_gravatars.delay(self)
        return True

    def _get_synced_identity(self, refresh=False):
        sync_provider = multipass.sync_provider
        if sync_provider is None:
            return None
        identities = sorted((x for x in self.identities if x.provider == sync_provider.name),
                            key=attrgetter('safe_last_login_dt', 'id'), reverse=True)
        if not identities:
            return None
        identity = identities[0]
        if refresh and identity.multipass_data is not None and sync_provider.supports_refresh:
            try:
                identity_info = sync_provider.refresh_identity(identity.identifier, identity.multipass_data)
            except IdentityRetrievalFailed:
                identity_info = None
            if identity_info:
                identity.data = identity_info.data
        return identity

    def get_merged_from_users_recursive(self):
        """Get the users merged into this users recursively."""
        user_alias = db.aliased(User)
        cte_query = (select([user_alias.id.label('merged_from_id')])
                     .where(user_alias.merged_into_id == self.id)
                     .cte(recursive=True))
        rec_query = (select([user_alias.id])
                     .where(user_alias.merged_into_id == cte_query.c.merged_from_id))
        cte = cte_query.union_all(rec_query)
        return User.query.join(cte, User.id == cte.c.merged_from_id).all()

    @contextmanager
    def force_user_locale(self):
        """Temporarily override the locale to the locale of the user."""
        locale = self.settings.get('lang')
        with force_locale(locale):
            yield


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
define_unaccented_lowercase_index(User.affiliation)
define_unaccented_lowercase_index(User.phone)
define_unaccented_lowercase_index(User.address)
