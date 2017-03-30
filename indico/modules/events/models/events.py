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

from collections import OrderedDict
from contextlib import contextmanager
from datetime import timedelta

import pytz
from flask import has_request_context, session
from sqlalchemy import orm, DDL
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import column_property
from sqlalchemy.orm.base import NEVER_SET, NO_VALUE
from sqlalchemy.sql import select

from indico.core import signals
from indico.core.db.sqlalchemy import db, UTCDateTime, PyIntEnum
from indico.core.db.sqlalchemy.attachments import AttachedItemsMixin
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin, RenderMode
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.notes import AttachedNotesMixin
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin, ProtectionMode
from indico.core.db.sqlalchemy.searchable_titles import SearchableTitleMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.queries import db_dates_overlap, get_related_object
from indico.modules.categories import Category
from indico.modules.events.logs import EventLogEntry
from indico.modules.events.management.util import get_non_inheriting_objects
from indico.modules.events.models.persons import PersonLinkDataMixin
from indico.modules.events.settings import EventSettingProperty, event_core_settings, event_contact_settings
from indico.modules.events.timetable.models.entries import TimetableEntry
from indico.util.caching import memoize_request
from indico.util.date_time import overlaps, now_utc
from indico.util.decorators import strict_classproperty
from indico.util.i18n import _
from indico.util.string import return_ascii, format_repr, text_to_repr, to_unicode
from indico.util.struct.enum import RichIntEnum
from indico.web.flask.util import url_for


class EventType(RichIntEnum):
    __titles__ = [None, _('Lecture'), _('Meeting'), _('Conference')]
    lecture = 1
    meeting = 2
    conference = 3

    @property
    def legacy_name(self):
        return 'simple_event' if self == EventType.lecture else self.name


class _EventSettingProperty(EventSettingProperty):
    # the Event is already an Event (duh!), no need to get any other attribute
    attr = staticmethod(lambda x: x)


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
    possible_render_modes = {RenderMode.html}
    default_render_mode = RenderMode.html
    __logging_disabled = False

    ATTACHMENT_FOLDER_ID_COLUMN = 'event_id'

    @strict_classproperty
    @classmethod
    def __auto_table_args(cls):
        return (db.Index('ix_events_start_dt_desc', cls.start_dt.desc()),
                db.Index('ix_events_end_dt_desc', cls.end_dt.desc()),
                db.Index('ix_events_not_deleted_category', cls.is_deleted, cls.category_id),
                db.Index('ix_events_not_deleted_category_dates',
                         cls.is_deleted, cls.category_id, cls.start_dt, cls.end_dt),
                db.Index('ix_uq_events_url_shortcut', db.func.lower(cls.url_shortcut), unique=True,
                         postgresql_where=db.text('NOT is_deleted')),
                db.CheckConstraint("category_id IS NOT NULL OR is_deleted", 'category_data_set'),
                db.CheckConstraint("(logo IS NULL) = (logo_metadata::text = 'null')", 'valid_logo'),
                db.CheckConstraint("(stylesheet IS NULL) = (stylesheet_metadata::text = 'null')",
                                   'valid_stylesheet'),
                db.CheckConstraint("end_dt >= start_dt", 'valid_dates'),
                db.CheckConstraint("url_shortcut != ''", 'url_shortcut_not_empty'),
                db.CheckConstraint("cloned_from_id != id", 'not_cloned_from_self'),
                db.CheckConstraint('visibility IS NULL OR visibility >= 0', 'valid_visibility'),
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
    #: If the event is locked (read-only mode)
    is_locked = db.Column(
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
    #: The ID of the series this events belongs to
    series_id = db.Column(
        db.Integer,
        db.ForeignKey('events.series.id'),
        nullable=True,
        index=True
    )
    #: If this event was cloned, the id of the parent event
    cloned_from_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        nullable=True,
        index=True,
    )
    #: The creation date of the event
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        index=True,
        default=now_utc
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
    #: The type of the event
    _type = db.Column(
        'type',
        PyIntEnum(EventType),
        nullable=False
    )
    #: The visibility depth in category overviews
    visibility = db.Column(
        db.Integer,
        nullable=True,
        default=None
    )
    #: A list of tags/keywords for the event
    keywords = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[],
    )
    #: The URL shortcut for the event
    url_shortcut = db.Column(
        db.String,
        nullable=True
    )
    #: The metadata of the logo (hash, size, filename, content_type)
    logo_metadata = db.Column(
        JSON,
        nullable=False,
        default=lambda: None
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
        default=lambda: None
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
            order_by=(start_dt, id),
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
        post_update=True,
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
    #: The series this event is part of
    series = db.relationship(
        'EventSeries',
        lazy=True,
        backref=db.backref(
            'events',
            lazy=True,
            order_by=(start_dt, id),
            primaryjoin='(Event.series_id == EventSeries.id) & ~Event.is_deleted',
        )
    )

    #: Users who can review on all tracks
    global_abstract_reviewers = db.relationship(
        'User',
        secondary='events.track_abstract_reviewers',
        collection_class=set,
        lazy=True,
        backref=db.backref(
            'global_abstract_reviewer_for_events',
            collection_class=set,
            lazy=True
        )
    )

    #: Users who are conveners on all tracks
    global_conveners = db.relationship(
        'User',
        secondary='events.track_conveners',
        collection_class=set,
        lazy=True,
        backref=db.backref(
            'global_convener_for_events',
            collection_class=set,
            lazy=True
        )
    )

    # relationship backrefs:
    # - abstract_email_templates (AbstractEmailTemplate.event_new)
    # - abstract_review_questions (AbstractReviewQuestion.event_new)
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
    # - designer_templates (DesignerTemplate.event_new)
    # - layout_images (ImageFile.event_new)
    # - legacy_contribution_mappings (LegacyContributionMapping.event_new)
    # - legacy_mapping (LegacyEventMapping.event_new)
    # - legacy_session_block_mappings (LegacySessionBlockMapping.event_new)
    # - legacy_session_mappings (LegacySessionMapping.event_new)
    # - legacy_subcontribution_mappings (LegacySubContributionMapping.event_new)
    # - log_entries (EventLogEntry.event_new)
    # - menu_entries (MenuEntry.event_new)
    # - note (EventNote.linked_event)
    # - paper_competences (PaperCompetence.event_new)
    # - paper_review_questions (PaperReviewQuestion.event_new)
    # - paper_templates (PaperTemplate.event_new)
    # - persons (EventPerson.event_new)
    # - registration_forms (RegistrationForm.event_new)
    # - registrations (Registration.event_new)
    # - reminders (EventReminder.event_new)
    # - requests (Request.event_new)
    # - reservations (Reservation.event_new)
    # - sessions (Session.event_new)
    # - settings (EventSetting.event_new)
    # - settings_principals (EventSettingPrincipal.event_new)
    # - static_list_links (StaticListLink.event_new)
    # - static_sites (StaticSite.event_new)
    # - surveys (Survey.event_new)
    # - timetable_entries (TimetableEntry.event_new)
    # - tracks (Track.event_new)
    # - vc_room_associations (VCRoomEventAssociation.linked_event)

    start_dt_override = _EventSettingProperty(event_core_settings, 'start_dt_override')
    end_dt_override = _EventSettingProperty(event_core_settings, 'end_dt_override')
    organizer_info = _EventSettingProperty(event_core_settings, 'organizer_info')
    additional_info = _EventSettingProperty(event_core_settings, 'additional_info')
    contact_title = _EventSettingProperty(event_contact_settings, 'title')
    contact_emails = _EventSettingProperty(event_contact_settings, 'emails')
    contact_phones = _EventSettingProperty(event_contact_settings, 'phones')

    @classmethod
    def category_chain_overlaps(cls, category_ids):
        """
        Create a filter that checks whether the event has any of the
        provided category ids in its parent chain.

        :param category_ids: A list of category ids or a single
                             category id
        """
        from indico.modules.categories import Category
        if not isinstance(category_ids, (list, tuple, set)):
            category_ids = [category_ids]
        cte = Category.get_tree_cte()
        return (cte.c.id == Event.category_id) & cte.c.path.overlap(category_ids)

    @classmethod
    def is_visible_in(cls, category):
        """
        Create a filter that checks whether the event is visible in
        the specified category.
        """
        cte = category.visible_categories_cte
        return (db.exists(db.select([1]))
                .where(db.and_(cte.c.id == Event.category_id,
                               db.or_(Event.visibility.is_(None), Event.visibility > cte.c.level))))

    @property
    @memoize_request
    def as_legacy(self):
        """Return a legacy `Conference` object"""
        from indico.modules.events.legacy import LegacyConference
        return LegacyConference(self)

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
        theme = layout_settings.get(self, 'timetable_theme')
        if theme and theme in theme_settings.get_themes_for(self.type):
            return theme
        else:
            return theme_settings.defaults[self.type]

    @property
    def locator(self):
        return {'confId': self.id}

    @property
    def logo_url(self):
        return url_for('event_images.logo_display', self, slug=self.logo_metadata['hash'])

    @property
    def participation_regform(self):
        return next((form for form in self.registration_forms if form.is_participation), None)

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
    def start_dt_display(self):
        """
        The 'displayed start dt', which is usually the actual start dt,
        but may be overridden for a conference.
        """
        if self.type_ == EventType.conference and self.start_dt_override:
            return self.start_dt_override
        else:
            return self.start_dt

    @property
    def end_dt_display(self):
        """
        The 'displayed end dt', which is usually the actual end dt,
        but may be overridden for a conference.
        """
        if self.type_ == EventType.conference and self.end_dt_override:
            return self.end_dt_override
        else:
            return self.end_dt

    @property
    def type(self):
        # XXX: this should eventually be replaced with the type_
        # property returning the enum - but there are too many places
        # right now that rely on the type string
        return self.type_.name

    @hybrid_property
    def type_(self):
        return self._type

    @type_.setter
    def type_(self, value):
        old_type = self._type
        self._type = value
        if old_type is not None and old_type != value:
            signals.event.type_changed.send(self, old_type=old_type)

    @property
    def url(self):
        return url_for('events.display', self)

    @property
    def external_url(self):
        return url_for('events.display', self, _external=True)

    @property
    def short_url(self):
        id_ = self.url_shortcut or self.id
        return url_for('events.shorturl', confId=id_)

    @property
    def short_external_url(self):
        id_ = self.url_shortcut or self.id
        return url_for('events.shorturl', confId=id_, _external=True)

    @property
    def tzinfo(self):
        return pytz.timezone(self.timezone)

    @property
    def display_tzinfo(self):
        """The tzinfo of the event as preferred by the current user"""
        from indico.legacy.common.timezoneUtils import DisplayTZ
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

    @hybrid_method
    def ends_after(self, dt):
        """Check whether the event ends on/after the specified date"""
        return self.end_dt >= dt if dt is not None else True

    @ends_after.expression
    def ends_after(cls, dt):
        return cls.end_dt >= dt if dt is not None else True

    @hybrid_property
    def duration(self):
        return self.end_dt - self.start_dt

    def can_lock(self, user):
        """Check whether the user can lock/unlock the event"""
        return user and (user.is_admin or user == self.creator or self.category.can_manage(user))

    def get_relative_event_ids(self):
        """Get the first, last, previous and next event IDs.

        Any of those values may be ``None`` if there is no matching
        event or if it would be the current event.

        :return: A dict containing ``first``, ``last``, ``prev`` and ``next``.
        """
        subquery = (select([Event.id,
                            db.func.first_value(Event.id).over(order_by=(Event.start_dt, Event.id)).label('first'),
                            db.func.last_value(Event.id).over(order_by=(Event.start_dt, Event.id),
                                                              range_=(None, None)).label('last'),
                            db.func.lag(Event.id).over(order_by=(Event.start_dt, Event.id)).label('prev'),
                            db.func.lead(Event.id).over(order_by=(Event.start_dt, Event.id)).label('next')])
                    .where((Event.category_id == self.category_id) & ~Event.is_deleted)
                    .alias())
        rv = (db.session.query(subquery.c.first, subquery.c.last, subquery.c.prev, subquery.c.next)
              .filter(subquery.c.id == self.id)
              .one()
              ._asdict())
        if rv['first'] == self.id:
            rv['first'] = None
        if rv['last'] == self.id:
            rv['last'] = None
        return rv

    def get_verbose_title(self, show_speakers=False, show_series_pos=False):
        """Get the event title with some additional information

        :param show_speakers: Whether to prefix the title with the
                              speakers of the event.
        :param show_series_pos: Whether to suffix the title with the
                                position and total count in the event's
                                series.
        """
        title = self.title
        if show_speakers and self.person_links:
            speakers = ', '.join(sorted([pl.full_name for pl in self.person_links], key=unicode.lower))
            title = '{}, "{}"'.format(speakers, title)
        if show_series_pos and self.series and self.series.show_sequence_in_title:
            title = '{} ({}/{})'.format(title, self.series_pos, self.series_count)
        return title

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
                                          SessionBlock.session.has(event_new=self, is_deleted=False))
        if scheduled_only:
            query.filter(SessionBlock.timetable_entry != None)  # noqa
        return query.first()

    def get_allowed_sender_emails(self, include_current_user=True, include_creator=True, include_managers=True,
                                  include_contact=True, include_chairs=True, extra=None):
        """
        Return the emails of people who can be used as senders (or
        rather Reply-to contacts) in emails sent from within an event.

        :param include_current_user: Whether to include the email of
                                     the currently logged-in user
        :param include_creator: Whether to include the email of the
                                event creator
        :param include_managers: Whether to include the email of all
                                 event managers
        :param include_contact: Whether to include the "event contact"
                                emails
        :param include_chairs: Whether to include the emails of event
                               chairpersons (or lecture speakers)
        :param extra: An email address that is always included, even
                      if it is not in any of the included lists.
        :return: An OrderedDict mapping emails to pretty names
        """
        emails = {}
        # Contact/Support
        if include_contact:
            for email in self.contact_emails:
                emails[email] = self.contact_title
        # Current user
        if include_current_user and has_request_context() and session.user:
            emails[session.user.email] = session.user.full_name
        # Creator
        if include_creator:
            emails[self.creator.email] = self.creator.full_name
        # Managers
        if include_managers:
            emails.update((p.principal.email, p.principal.full_name)
                          for p in self.acl_entries
                          if p.type == PrincipalType.user and p.full_access)
        # Chairs
        if include_chairs:
            emails.update((pl.email, pl.full_name) for pl in self.person_links if pl.email)
        # Extra email (e.g. the current value in an object from the DB)
        if extra:
            emails.setdefault(extra, extra)
        # Sanitize and format emails
        emails = {to_unicode(email.strip().lower()): '{} <{}>'.format(to_unicode(name), to_unicode(email))
                  for email, name in emails.iteritems()
                  if email and email.strip()}
        own_email = session.user.email if has_request_context() and session.user else None
        return OrderedDict(sorted(emails.items(), key=lambda x: (x[0] != own_email, x[1].lower())))

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

    def iter_days(self, tzinfo=None):
        start_dt = self.start_dt
        end_dt = self.end_dt
        if tzinfo:
            start_dt = start_dt.astimezone(tzinfo)
            end_dt = end_dt.astimezone(tzinfo)
        duration = (end_dt - start_dt).days
        for offset in xrange(duration + 1):
            yield (start_dt + timedelta(days=offset)).date()

    def preload_all_acl_entries(self):
        db.m.Contribution.preload_acl_entries(self)
        db.m.Session.preload_acl_entries(self)

    def move(self, category):
        old_category = self.category
        self.category = category
        db.session.flush()
        signals.event.moved.send(self, old_parent=old_category)

    def delete(self, reason, user=None):
        from indico.modules.events import logger, EventLogRealm, EventLogKind
        self.is_deleted = True
        signals.event.deleted.send(self, user=user)
        db.session.flush()
        logger.info('Event %r deleted [%s]', self, reason)
        self.log(EventLogRealm.event, EventLogKind.negative, 'Event', 'Event deleted', user, data={'Reason': reason})

    @property
    @memoize_request
    def cfa(self):
        from indico.modules.events.abstracts.models.call_for_abstracts import CallForAbstracts
        return CallForAbstracts(self)

    @property
    @memoize_request
    def cfp(self):
        from indico.modules.events.papers.models.call_for_papers import CallForPapers
        return CallForPapers(self)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'start_dt', 'end_dt', is_deleted=False, is_locked=False,
                           _text=text_to_repr(self.title, max_length=75))


Event.register_location_events()
Event.register_protection_events()


@listens_for(orm.mapper, 'after_configured', once=True)
def _mappers_configured():
    event_alias = db.aliased(Event)

    # Event.category_chain -- the category ids of the event, starting
    # with the root category down to the event's immediate parent.
    cte = Category.get_tree_cte()
    query = select([cte.c.path]).where(cte.c.id == Event.category_id).correlate_except(cte)
    Event.category_chain = column_property(query, deferred=True)

    # Event.effective_protection_mode -- the effective protection mode
    # (public/protected) of the event, even if it's inheriting it from its
    # parent category
    query = (select([db.case({ProtectionMode.inheriting.value: Category.effective_protection_mode},
                             else_=Event.protection_mode, value=Event.protection_mode)])
             .where(Category.id == Event.category_id))
    Event.effective_protection_mode = column_property(query, deferred=True)

    # Event.series_pos -- the position of the event in its series
    subquery = (select([event_alias.id,
                        db.func.row_number().over(order_by=(event_alias.start_dt, event_alias.id)).label('pos')])
                .where((event_alias.series_id == Event.series_id) & ~event_alias.is_deleted)
                .correlate(Event)
                .alias())
    query = select([subquery.c.pos]).where(subquery.c.id == Event.id).correlate_except(subquery)
    Event.series_pos = column_property(query, group='series', deferred=True)

    # Event.series_count -- the number of events in the event's series
    query = (db.select([db.func.count(event_alias.id)])
             .where((event_alias.series_id == Event.series_id) & ~event_alias.is_deleted)
             .correlate_except(event_alias))
    Event.series_count = column_property(query, group='series', deferred=True)


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
        AFTER UPDATE OF start_dt, end_dt
        ON {table}
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('event');
    """.format(table=target.fullname)
    DDL(sql).execute(conn)


@listens_for(Event.__table__, 'after_create')
def _add_deletion_consistency_trigger(target, conn, **kw):
    sql = """
        CREATE CONSTRAINT TRIGGER consistent_deleted
        AFTER INSERT OR UPDATE OF category_id, is_deleted
        ON {table}
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE categories.check_consistency_deleted();
    """.format(table=target.fullname)
    DDL(sql).execute(conn)
