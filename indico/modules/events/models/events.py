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

from contextlib import contextmanager

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import JSON

from indico.core.db.sqlalchemy import db
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.modules.events.logs import EventLogEntry
from indico.util.caching import memoize_request
from indico.util.decorators import classproperty
from indico.util.string import return_ascii, to_unicode, format_repr
from indico.web.flask.util import url_for


class Event(LocationMixin, ProtectionManagersMixin, db.Model):
    """An Indico event

    This model contains the most basic information related to an event.

    Note that the ACL is currently only used for managers but not for
    view access!
    """
    __tablename__ = 'events'
    __auto_table_args = (db.CheckConstraint("(logo IS NULL) = (logo_metadata::text = 'null')", 'valid_logo'),
                         db.CheckConstraint("(stylesheet IS NULL) = (stylesheet_metadata::text = 'null')",
                                            'valid_stylesheet'),
                         {'schema': 'events'})
    disallowed_protection_modes = frozenset()
    inheriting_have_acl = True
    location_backref_name = 'events'
    allow_location_inheritance = False
    __logging_disabled = False

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    #: The ID of the event
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: If the event has been deleted
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The ID of the user who created the event
    creator_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True
    )
    #: The metadata of the logo (hash, size, filename, content_type)
    logo_metadata = db.Column(
        JSON,
        nullable=False,
        default=None
    )
    #: The logo's raw image data
    logo = db.deferred(db.Column(
        db.LargeBinary,
        nullable=True
    ))
    #: The metadata of the stylesheet (hash, size, filename)
    stylesheet_metadata = db.Column(
        JSON,
        nullable=False,
        default=None
    )
    #: The stylesheet's raw image data
    stylesheet = db.deferred(db.Column(
        db.Text,
        nullable=True
    ))
    #: The ID of the event's default page (conferences only)
    default_page_id = db.Column(
        db.Integer,
        db.ForeignKey('events.pages.id'),
        index=True,
        nullable=True
    )
    #: The last user-friendly registration ID
    _last_friendly_registration_id = db.deferred(db.Column(
        'last_friendly_registration_id',
        db.Integer,
        nullable=False,
        default=0
    ))
    #: The last user-friendly contribution ID
    _last_friendly_contribution_id = db.deferred(db.Column(
        'last_friendly_contribution_id',
        db.Integer,
        nullable=False,
        default=0
    ))
    #: The last user-friendly session ID
    _last_friendly_session_id = db.deferred(db.Column(
        'last_friendly_session_id',
        db.Integer,
        nullable=False,
        default=0
    ))

    #: The user who created the event
    creator = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'created_events',
            lazy='dynamic'
        )
    )
    #: The event's default page (conferences only)
    default_page = db.relationship(
        'EventPage',
        lazy=True,
        foreign_keys=[default_page_id],
        # don't use this backref. we just need it so SA properly NULLs
        # this column when deleting the default page
        backref=db.backref('_default_page_of_event', lazy=True)
    )
    #: The ACL entries for the event
    acl_entries = db.relationship(
        'EventPrincipal',
        backref='event_new',
        cascade='all, delete-orphan',
        collection_class=set
    )
    #: External references associated with this event
    references = db.relationship(
        'EventReference',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'event_new',
            lazy=True
        )
    )

    # relationship backrefs:
    # - agreements (Agreement.event_new)
    # - attachment_folders (AttachmentFolder.event_new)
    # - contribution_fields (ContributionField.event_new)
    # - contributions (Contribution.event_new)
    # - custom_pages (EventPage.event_new)
    # - layout_images (ImageFile.event_new)
    # - legacy_attachment_folder_mappings (LegacyAttachmentFolderMapping.event_new)
    # - legacy_attachment_mappings (LegacyAttachmentMapping.event_new)
    # - legacy_contribution_mappings (LegacyContributionMapping.event_new)
    # - legacy_mapping (LegacyEventMapping.event_new)
    # - legacy_session_mappings (LegacySessionMapping.event_new)
    # - log_entries (EventLogEntry.event_new)
    # - menu_entries (MenuEntry.event_new)
    # - notes (EventNote.event_new)
    # - persons (EventPerson.event_new)
    # - registration_forms (RegistrationForm.event_new)
    # - registrations (Registration.event_new)
    # - reminders (EventReminder.event_new)
    # - requests (Request.event_new)
    # - reservations (Reservation.event_new)
    # - sessions (Session.event_new)
    # - settings (EventSetting.event_new)
    # - settings_principals (EventSettingPrincipal.event_new)
    # - static_sites (StaticSite.event_new)
    # - surveys (Survey.event_new)
    # - timetable_entries (TimetableEntry.event_new)
    # - vc_room_associations (VCRoomEventAssociation.event_new)

    @property
    @memoize_request
    def as_legacy(self):
        """Returns a legacy `Conference` object (ZODB)"""
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(self.id, True)

    @property
    def protection_parent(self):
        return self.as_legacy.getOwner()

    @property
    def has_logo(self):
        return self.logo_metadata is not None

    @property
    def logo_url(self):
        return url_for('event_images.logo_display', self, slug=self.logo_metadata['hash'])

    @property
    def has_stylesheet(self):
        return self.stylesheet_metadata is not None

    @property
    def locator(self):
        return {'confId': self.id}

    @property
    def participation_regform(self):
        return self.registration_forms.filter_by(is_participation=True, is_deleted=False).first()

    @property
    def title(self):
        return to_unicode(self.as_legacy.getTitle())

    @property
    def type(self):
        event_type = self.as_legacy.getType()
        if event_type == 'simple_event':
            event_type = 'lecture'
        return event_type

    @property
    @contextmanager
    def logging_disabled(self):
        """Temporarily disables event logging

        This is useful when performing actions e.g. during event
        creation or at other times where adding entries to the event
        log doesn't make sense.
        """
        self.__logging_disabled = True
        try:
            yield
        finally:
            self.__logging_disabled = False

    def can_access(self, user, allow_admin=True):
        if not allow_admin:
            raise NotImplementedError('can_access(..., allow_admin=False) is unsupported until ACLs are migrated')
        from MaKaC.accessControl import AccessWrapper
        return self.as_legacy.canAccess(AccessWrapper(user.as_avatar if user else None))

    def can_manage(self, user, role=None, allow_key=False, *args, **kwargs):
        # XXX: Remove this method once modification keys are gone!
        return (super(Event, self).can_manage(user, role, *args, **kwargs) or
                (allow_key and self.as_legacy.canKeyModify()))

    @memoize_request
    def has_feature(self, feature):
        """Checks if a feature is enabled for the event"""
        from indico.modules.events.features.util import is_feature_enabled
        return is_feature_enabled(self, feature)

    def log(self, realm, kind, module, summary, user=None, type_='simple', data=None):
        """Creates a new log entry for the event

        :param realm: A value from :class:`.EventLogRealm` indicating
                      the realm of the action.
        :param kind: A value from :class:`.EventLogKind` indicating
                     the kind of the action that was performed.
        :param module: A human-friendly string describing the module
                       related to the action.
        :param summary: A one-line summary describing the logged action.
        :param user: The user who performed the action.
        :param type_: The type of the log entry. This is used for custom
                      rendering of the log message/data
        :param data: JSON-serializable data specific to the log type.

        In most cases the ``simple`` log type is fine. For this type,
        any items from data will be shown in the detailed view of the
        log entry.  You may either use a dict (which will be sorted)
        alphabetically or a list of ``key, value`` pairs which will
        be displayed in the given order.
        """
        if self.__logging_disabled:
            return
        entry = EventLogEntry(user=user, realm=realm, kind=kind, module=module, type=type_, summary=summary,
                              data=data or {})
        self.log_entries.append(entry)

    @return_ascii
    def __repr__(self):
        # TODO: add self.protection_repr once we use it and the title once we store it here
        return format_repr(self, 'id', is_deleted=False)

    # TODO: Remove the next block of code once event acls (read access) are migrated
    def _fail(self, *args, **kwargs):
        raise NotImplementedError('These properties are not usable until event ACLs are in the new DB')
    is_public = classproperty(classmethod(_fail))
    is_inheriting = classproperty(classmethod(_fail))
    is_protected = classproperty(classmethod(_fail))
    protection_repr = property(_fail)
    del _fail
