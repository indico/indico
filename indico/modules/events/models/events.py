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

import pytz
from sqlalchemy import DDL
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import JSON, ARRAY
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm.base import NEVER_SET, NO_VALUE

from indico.core.db.sqlalchemy import db, UTCDateTime
from indico.core.db.sqlalchemy.attachments import AttachedItemsMixin
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.notes import AttachedNotesMixin
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin
from indico.core.db.sqlalchemy.searchable_titles import SearchableTitleMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap, get_related_object
from indico.modules.events.logs import EventLogEntry
from indico.modules.events.management.util import get_non_inheriting_objects
from indico.modules.events.models.persons import PersonLinkDataMixin
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.util.caching import memoize_request
from indico.util.date_time import overlaps
from indico.util.decorators import strict_classproperty
from indico.util.string import return_ascii, format_repr, text_to_repr, RichMarkup
from indico.web.flask.util import url_for


class Event(SearchableTitleMixin, DescriptionMixin, LocationMixin, ProtectionManagersMixin, AttachedItemsMixin,
            AttachedNotesMixin, PersonLinkDataMixin, db.Model):
    """An Indico event

    This model contains the most basic information related to an event.

    Note that the ACL is currently only used for managers but not for
    view access!
    """
    __tablename__ = 'events'
    disallowed_protection_modes = frozenset()
    inheriting_have_acl = True
    allow_access_key = True
    allow_no_access_contact = True
    location_backref_name = 'events'
    allow_location_inheritance = False
    description_wrapper = RichMarkup
    __logging_disabled = False

    ATTACHMENT_FOLDER_ID_COLUMN = 'event_id'

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        return (db.Index(None, 'category_chain', postgresql_using='gin'),
                db.Index('ix_events_start_dt_desc', cls.start_dt.desc()),
                db.Index('ix_events_end_dt_desc', cls.end_dt.desc()),
                db.CheckConstraint("(category_id IS NOT NULL AND category_chain IS NOT NULL) OR is_deleted",
                                   'category_data_set'),
                db.CheckConstraint("category_id = category_chain[array_length(category_chain, 1)]",
                                   'category_id_matches_chain'),
                db.CheckConstraint("category_chain[1] = 0", 'category_chain_has_root'),
                db.CheckConstraint("(logo IS NULL) = (logo_metadata::text = 'null')", 'valid_logo'),
                db.CheckConstraint("(stylesheet IS NULL) = (stylesheet_metadata::text = 'null')",
                                   'valid_stylesheet'),
                db.CheckConstraint("end_dt >= start_dt", 'valid_dates'),
                db.CheckConstraint("cloned_from_id != id", 'not_cloned_from_self'),
                {'schema': 'events'})

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
    #: The ID of immediate parent category of the event
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        nullable=True,
        index=True
    )
    #: The category chain of the event (from immediate parent to root)
    category_chain = db.Column(
        ARRAY(db.Integer),
        nullable=True
    )
    #: If this event was cloned, the id of the parent event
    cloned_from_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        nullable=True,
        index=True,
    )
    #: The start date of the event
    start_dt = db.Column(
        UTCDateTime,
        nullable=False,
        index=True
    )
    #: The end date of the event
    end_dt = db.Column(
        UTCDateTime,
        nullable=False,
        index=True
    )
    #: The timezone of the event
    timezone = db.Column(
        db.String,
        nullable=False
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

    #: The category containing the event
    category = db.relationship(
        'Category',
        lazy=True,
        backref=db.backref(
            'events',
            primaryjoin='(Category.id == Event.category_id) & ~Event.is_deleted',
            order_by=start_dt,
            lazy=True
        )
    )
    #: The user who created the event
    creator = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'created_events',
            lazy='dynamic'
        )
    )
    #: The event this one was cloned from
    cloned_from = db.relationship(
        'Event',
        lazy=True,
        remote_side='Event.id',
        backref=db.backref(
            'clones',
            lazy=True,
            order_by=start_dt
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
    #: Persons associated with this event
    person_links = db.relationship(
        'EventPersonLink',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'event',
            lazy=True
        )
    )

    # relationship backrefs:
    # - abstracts (Abstract.event_new)
    # - agreements (Agreement.event_new)
    # - all_attachment_folders (AttachmentFolder.event_new)
    # - all_legacy_attachment_folder_mappings (LegacyAttachmentFolderMapping.event_new)
    # - all_legacy_attachment_mappings (LegacyAttachmentMapping.event_new)
    # - all_notes (EventNote.event_new)
    # - all_vc_room_associations (VCRoomEventAssociation.event_new)
    # - attachment_folders (AttachmentFolder.linked_event)
    # - clones (Event.cloned_from)
    # - contribution_fields (ContributionField.event_new)
    # - contribution_types (ContributionType.event_new)
    # - contributions (Contribution.event_new)
    # - custom_pages (EventPage.event_new)
    # - layout_images (ImageFile.event_new)
    # - legacy_contribution_mappings (LegacyContributionMapping.event_new)
    # - legacy_mapping (LegacyEventMapping.event_new)
    # - legacy_session_block_mappings (LegacySessionBlockMapping.event_new)
    # - legacy_session_mappings (LegacySessionMapping.event_new)
    # - legacy_subcontribution_mappings (LegacySubContributionMapping.event_new)
    # - log_entries (EventLogEntry.event_new)
    # - menu_entries (MenuEntry.event_new)
    # - note (EventNote.linked_event)
    # - persons (EventPerson.event_new)
    # - registration_forms (RegistrationForm.event_new)
    # - registrations (Registration.event_new)
    # - reminders (EventReminder.event_new)
    # - report_links (ReportLink.event_new)
    # - requests (Request.event_new)
    # - reservations (Reservation.event_new)
    # - sessions (Session.event_new)
    # - settings (EventSetting.event_new)
    # - settings_principals (EventSettingPrincipal.event_new)
    # - static_sites (StaticSite.event_new)
    # - surveys (Survey.event_new)
    # - timetable_entries (TimetableEntry.event_new)
    # - vc_room_associations (VCRoomEventAssociation.linked_event)

    @property
    @memoize_request
    def as_legacy(self):
        """Returns a legacy `Conference` object (ZODB)"""
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(self.id, True)

    @property
    def event_new(self):
        """Convenience property so all event entities have it"""
        return self

    @property
    def has_logo(self):
        return self.logo_metadata is not None

    @property
    def has_stylesheet(self):
        return self.stylesheet_metadata is not None

    @property
    def theme(self):
        from indico.modules.events.layout import layout_settings, theme_settings
        return (layout_settings.get(self, 'timetable_theme') or
                theme_settings.defaults[self.type])

    @property
    def locator(self):
        return {'confId': self.id}

    @property
    def logo_url(self):
        return url_for('event_images.logo_display', self, slug=self.logo_metadata['hash'])

    @property
    def participation_regform(self):
        return self.registration_forms.filter_by(is_participation=True, is_deleted=False).first()

    @property
    @memoize_request
    def published_registrations(self):
        from indico.modules.events.registration.util import get_published_registrations
        return get_published_registrations(self)

    @property
    def protection_parent(self):
        return self.category

    @property
    def start_dt_local(self):
        return self.start_dt.astimezone(self.tzinfo)

    @property
    def end_dt_local(self):
        return self.end_dt.astimezone(self.tzinfo)

    @property
    def type(self):
        event_type = self.as_legacy.getType()
        if event_type == 'simple_event':
            event_type = 'lecture'
        return event_type

    @property
    def tzinfo(self):
        return pytz.timezone(self.timezone)

    @property
    def display_tzinfo(self):
        """The tzinfo of the event as preferred by the current user"""
        from MaKaC.common.timezoneUtils import DisplayTZ
        return DisplayTZ(conf=self).getDisplayTZ(as_timezone=True)

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

    @hybrid_method
    def happens_between(self, from_dt=None, to_dt=None):
        """Check whether the event takes place within two dates"""
        if from_dt is not None and to_dt is not None:
            # any event that takes place during the specified range
            return overlaps((self.start_dt, self.end_dt), (from_dt, to_dt), inclusive=True)
        elif from_dt is not None:
            # any event that starts on/after the specified date
            return self.start_dt >= from_dt
        elif to_dt is not None:
            # any event that ends on/before the specifed date
            return self.end_dt <= to_dt
        else:
            return True

    @happens_between.expression
    def happens_between(cls, from_dt=None, to_dt=None):
        if from_dt is not None and to_dt is not None:
            # any event that takes place during the specified range
            return db_dates_overlap(cls, 'start_dt', from_dt, 'end_dt', to_dt, inclusive=True)
        elif from_dt is not None:
            # any event that starts on/after the specified date
            return cls.start_dt >= from_dt
        elif to_dt is not None:
            # any event that ends on/before the specifed date
            return cls.end_dt <= to_dt
        else:
            return True

    @hybrid_method
    def starts_between(self, from_dt=None, to_dt=None):
        """Check whether the event starts within two dates"""
        if from_dt is not None and to_dt is not None:
            return from_dt <= self.start_dt <= to_dt
        elif from_dt is not None:
            return self.start_dt >= from_dt
        elif to_dt is not None:
            return self.start_dt <= to_dt
        else:
            return True

    @starts_between.expression
    def starts_between(cls, from_dt=None, to_dt=None):
        if from_dt is not None and to_dt is not None:
            return cls.start_dt.between(from_dt, to_dt)
        elif from_dt is not None:
            return cls.start_dt >= from_dt
        elif to_dt is not None:
            return cls.start_dt <= to_dt
        else:
            return True

    @hybrid_property
    def duration(self):
        return self.end_dt - self.start_dt

    def get_non_inheriting_objects(self):
        """Get a set of child objects that do not inherit protection"""
        return get_non_inheriting_objects(self)

    def get_contribution(self, id_):
        """Get a contribution of the event"""
        return get_related_object(self, 'contributions', {'id': id_})

    def get_session(self, id_=None, friendly_id=None):
        """Get a session of the event"""
        if friendly_id is None and id_ is not None:
            criteria = {'id': id_}
        elif id_ is None and friendly_id is not None:
            criteria = {'friendly_id': friendly_id}
        else:
            raise ValueError('Exactly one kind of id must be specified')
        return get_related_object(self, 'sessions', criteria)

    def get_session_block(self, id_, scheduled_only=False):
        """Get a session block of the event"""
        from indico.modules.events.sessions.models.blocks import SessionBlock
        query = SessionBlock.query.filter(SessionBlock.id == id_,
                                          SessionBlock.session.has(event_new=self.event_new, is_deleted=False))
        if scheduled_only:
            query.filter(SessionBlock.timetable_entry != None)  # noqa
        return query.first()

    @memoize_request
    def has_feature(self, feature):
        """Checks if a feature is enabled for the event"""
        from indico.modules.events.features.util import is_feature_enabled
        return is_feature_enabled(self, feature)

    @property
    @memoize_request
    def scheduled_notes(self):
        from indico.modules.events.notes.util import get_scheduled_notes
        return get_scheduled_notes(self)

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

    def get_contribution_field(self, field_id):
        return next((v for v in self.contribution_fields if v.id == field_id), '')

    def move_start_dt(self, start_dt):
        """Set event start_dt and adjust its timetable entries"""
        diff = start_dt - self.start_dt
        for entry in self.timetable_entries.filter(TimetableEntry.parent_id.is_(None)):
            new_dt = entry.start_dt + diff
            entry.move(new_dt)
        self.start_dt = start_dt

    def preload_all_acl_entries(self):
        db.m.Contribution.preload_acl_entries(self)
        db.m.Session.preload_acl_entries(self)

    @return_ascii
    def __repr__(self):
        # TODO: add self.protection_repr once we use it
        return format_repr(self, 'id', 'start_dt', 'end_dt', is_deleted=False,
                           _text=text_to_repr(self.title, max_length=75))


Event.register_location_events()
Event.register_protection_events()


@listens_for(Event.category, 'set')
def _category_id_set(target, value, *unused):
    target.category_chain = [x.id for x in value.chain_query]


@listens_for(Event.start_dt, 'set')
@listens_for(Event.end_dt, 'set')
def _set_start_end_dt(target, value, oldvalue, *unused):
    from indico.modules.events.util import register_event_time_change
    if oldvalue in (NEVER_SET, NO_VALUE):
        return
    if value != oldvalue:
        register_event_time_change(target)


@listens_for(Event.__table__, 'after_create')
def _add_timetable_consistency_trigger(target, conn, **kw):
    sql = """
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER UPDATE
        ON {}
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('event');
    """.format(target.fullname)
    DDL(sql).execute(conn)
