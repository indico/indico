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

from sqlalchemy import DDL
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import mapper
from sqlalchemy.orm.base import NEVER_SET, NO_VALUE

from indico.core.db import db
from indico.core.db.sqlalchemy.attachments import AttachedItemsMixin
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.notes import AttachedNotesMixin
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.queries import increment_and_get
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.management.util import get_non_inheriting_objects
from indico.modules.events.models.persons import PersonLinkDataMixin
from indico.modules.events.sessions.util import session_coordinator_priv_enabled
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


def _get_next_friendly_id(context):
    """Get the next friendly id for a contribution."""
    from indico.modules.events import Event
    event_id = context.current_parameters['event_id']
    assert event_id is not None
    return increment_and_get(Event._last_friendly_contribution_id, Event.id == event_id)


class CustomFieldsMixin(object):
    """Methods to process custom field data."""

    def set_custom_field(self, field_id, field_value):
        fv = self.get_field_value(field_id, raw=True)
        if not fv:
            field_value_cls = type(self).field_values.prop.mapper.class_
            fv = field_value_cls(contribution_field=self.event_new.get_contribution_field(field_id))
            self.field_values.append(fv)
        fv.data = field_value


class Contribution(DescriptionMixin, ProtectionManagersMixin, LocationMixin, AttachedItemsMixin,
                   AttachedNotesMixin, PersonLinkDataMixin, CustomFieldsMixin, db.Model):
    __tablename__ = 'contributions'
    __auto_table_args = (db.Index(None, 'friendly_id', 'event_id', unique=True),
                         db.Index(None, 'event_id', 'track_id'),
                         db.Index(None, 'event_id', 'abstract_id'),
                         db.CheckConstraint("session_block_id IS NULL OR session_id IS NOT NULL",
                                            'session_block_if_session'),
                         db.ForeignKeyConstraint(['session_block_id', 'session_id'],
                                                 ['events.session_blocks.id', 'events.session_blocks.session_id']),
                         {'schema': 'events'})
    location_backref_name = 'contributions'
    disallowed_protection_modes = frozenset()
    inheriting_have_acl = True

    PRELOAD_EVENT_ATTACHED_ITEMS = True
    PRELOAD_EVENT_ATTACHED_NOTES = True
    ATTACHMENT_FOLDER_ID_COLUMN = 'contribution_id'

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The human-friendly ID for the contribution
    friendly_id = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_friendly_id
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('events.sessions.id'),
        index=True,
        nullable=True
    )
    session_block_id = db.Column(
        db.Integer,
        db.ForeignKey('events.session_blocks.id'),
        index=True,
        nullable=True
    )
    track_id = db.Column(
        db.Integer,
        nullable=True
    )
    abstract_id = db.Column(
        db.Integer,
        db.ForeignKey('events.abstracts.id'),
        index=True,
        nullable=True
    )
    type_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contribution_types.id'),
        index=True,
        nullable=True
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    duration = db.Column(
        db.Interval,
        nullable=False
    )
    board_number = db.Column(
        db.String,
        nullable=False,
        default=''
    )
    keywords = db.Column(
        ARRAY(db.String),
        nullable=False,
        default=[]
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The last user-friendly sub-contribution ID
    _last_friendly_subcontribution_id = db.deferred(db.Column(
        'last_friendly_subcontribution_id',
        db.Integer,
        nullable=False,
        default=0
    ))

    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'contributions',
            primaryjoin='(Contribution.event_id == Event.id) & ~Contribution.is_deleted',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    session = db.relationship(
        'Session',
        lazy=True,
        backref=db.backref(
            'contributions',
            primaryjoin='(Contribution.session_id == Session.id) & ~Contribution.is_deleted',
            lazy=True
        )
    )
    session_block = db.relationship(
        'SessionBlock',
        lazy=True,
        foreign_keys=[session_block_id],
        backref=db.backref(
            'contributions',
            primaryjoin='(Contribution.session_block_id == SessionBlock.id) & ~Contribution.is_deleted',
            lazy=True
        )
    )
    type = db.relationship(
        'ContributionType',
        lazy=True,
        backref=db.backref(
            'contributions',
            lazy=True
        )
    )
    acl_entries = db.relationship(
        'ContributionPrincipal',
        lazy=True,
        cascade='all, delete-orphan',
        collection_class=set,
        backref='contribution'
    )
    subcontributions = db.relationship(
        'SubContribution',
        lazy=True,
        primaryjoin='(SubContribution.contribution_id == Contribution.id) & ~SubContribution.is_deleted',
        order_by='SubContribution.position',
        cascade='all, delete-orphan',
        backref=db.backref(
            'contribution',
            primaryjoin='SubContribution.contribution_id == Contribution.id',
            lazy=True
        )
    )
    abstract = db.relationship(
        'Abstract',
        lazy=True,
        backref=db.backref(
            'contribution',
            lazy=True,
            uselist=False
        )
    )
    #: External references associated with this contribution
    references = db.relationship(
        'ContributionReference',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'contribution',
            lazy=True
        )
    )
    #: Persons associated with this contribution
    person_links = db.relationship(
        'ContributionPersonLink',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'contribution',
            lazy=True
        )
    )
    #: Data stored in abstract/contribution fields
    field_values = db.relationship(
        'ContributionFieldValue',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'contribution',
            lazy=True
        )
    )

    # relationship backrefs:
    # - attachment_folders (AttachmentFolder.contribution)
    # - legacy_mapping (LegacyContributionMapping.contribution)
    # - note (EventNote.contribution)
    # - timetable_entry (TimetableEntry.contribution)
    # - vc_room_associations (VCRoomEventAssociation.linked_contrib)

    @declared_attr
    def is_scheduled(cls):
        from indico.modules.events.timetable.models.entries import TimetableEntry
        query = (db.exists([1])
                 .where(TimetableEntry.contribution_id == cls.id)
                 .correlate_except(TimetableEntry))
        return db.column_property(query, deferred=True)

    @declared_attr
    def subcontribution_count(cls):
        from indico.modules.events.contributions.models.subcontributions import SubContribution
        query = (db.select([db.func.count(SubContribution.id)])
                 .where((SubContribution.contribution_id == cls.id) & ~SubContribution.is_deleted)
                 .correlate_except(SubContribution))
        return db.column_property(query, deferred=True)

    def __init__(self, **kwargs):
        # explicitly initialize those relationships with None to avoid
        # an extra query to check whether there is an object associated
        # when assigning a new one (e.g. during cloning)
        kwargs.setdefault('note', None)
        kwargs.setdefault('timetable_entry', None)
        super(Contribution, self).__init__(**kwargs)

    @property
    def location_parent(self):
        if self.session_block_id is not None:
            return self.session_block
        elif self.session_id is not None:
            return self.session
        else:
            return self.event_new

    @property
    def protection_parent(self):
        return self.session if self.session_id is not None else self.event_new

    @property
    def track(self):
        return self.event_new.as_legacy.getTrackById(str(self.track_id))

    @property
    def start_dt(self):
        return self.timetable_entry.start_dt if self.timetable_entry else None

    @property
    def end_dt(self):
        return self.timetable_entry.start_dt + self.duration if self.timetable_entry else None

    @property
    def speakers(self):
        return [person_link for person_link in self.person_links if person_link.is_speaker]

    @property
    def speaker_names(self):
        return [person_link.full_name for person_link in self.person_links if person_link.is_speaker]

    @property
    def primary_authors(self):
        return {person_link for person_link in self.person_links if person_link.author_type == AuthorType.primary}

    @property
    def secondary_authors(self):
        return {person_link for person_link in self.person_links if person_link.author_type == AuthorType.secondary}

    @property
    def submitters(self):
        return {person_link for person_link in self.person_links if person_link.is_submitter}

    @locator_property
    def locator(self):
        return dict(self.event_new.locator, contrib_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', is_deleted=False, _text=self.title)

    def can_manage(self, user, role=None, allow_admin=True, check_parent=True, explicit_role=False):
        if super(Contribution, self).can_manage(user, role, allow_admin=allow_admin, check_parent=check_parent,
                                                explicit_role=explicit_role):
            return True
        if (check_parent and self.session_id is not None and
                self.session.can_manage(user, 'coordinate', allow_admin=allow_admin, explicit_role=explicit_role) and
                session_coordinator_priv_enabled(self.event_new, 'manage-contributions')):
            return True
        return False

    def get_non_inheriting_objects(self):
        """Get a set of child objects that do not inherit protection"""
        return get_non_inheriting_objects(self)

    def get_field_value(self, field_id, raw=False):
        fv = next((v for v in self.field_values if v.contribution_field_id == field_id), None)
        if raw:
            return fv
        else:
            return fv.friendly_data if fv else ''


@listens_for(mapper, 'after_configured', once=True)
def _mapper_configured():
    Contribution.register_location_events()

    @listens_for(Contribution.session, 'set')
    def _set_session_block(target, value, *unused):
        if value is None:
            target.session_block = None

    @listens_for(Contribution.timetable_entry, 'set')
    @no_autoflush
    def _set_timetable_entry(target, value, *unused):
        if value is None:
            target.session_block = None
        else:
            if target.session is not None:
                target.session_block = value.parent.session_block

    @listens_for(Contribution.duration, 'set')
    def _set_duration(target, value, oldvalue, *unused):
        from indico.modules.events.util import register_time_change
        if oldvalue in (NEVER_SET, NO_VALUE):
            return
        if value != oldvalue and target.timetable_entry is not None:
            register_time_change(target.timetable_entry)


@listens_for(Contribution.__table__, 'after_create')
def _add_timetable_consistency_trigger(target, conn, **kw):
    sql = """
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE
        ON {}
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('contribution');
    """.format(target.fullname)
    DDL(sql).execute(conn)
