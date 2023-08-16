# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import g, session
from sqlalchemy import DDL
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.event import listens_for
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import column_property, mapper
from sqlalchemy.orm.base import NEVER_SET, NO_VALUE
from sqlalchemy.sql import select

from indico.core.db import db
from indico.core.db.sqlalchemy.attachments import AttachedItemsMixin
from indico.core.db.sqlalchemy.descriptions import RenderMode, SearchableDescriptionMixin
from indico.core.db.sqlalchemy.locations import LocationMixin
from indico.core.db.sqlalchemy.notes import AttachedNotesMixin
from indico.core.db.sqlalchemy.protection import ProtectionManagersMixin, ProtectionMode
from indico.core.db.sqlalchemy.searchable import SearchableTitleMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.core.db.sqlalchemy.util.queries import increment_and_get
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.editing.models.editable import EditableType
from indico.modules.events.management.util import get_non_inheriting_objects
from indico.modules.events.models.events import Event
from indico.modules.events.models.persons import AuthorsSpeakersMixin, PersonLinkMixin
from indico.modules.events.papers.models.papers import Paper
from indico.modules.events.papers.models.revisions import PaperRevision, PaperRevisionState
from indico.modules.events.sessions.models.sessions import Session
from indico.modules.events.sessions.util import session_coordinator_priv_enabled
from indico.util.iterables import materialize_iterable
from indico.util.locators import locator_property
from indico.util.string import format_repr, slugify


def _get_next_friendly_id(context):
    """Get the next friendly id for a contribution."""
    from indico.modules.events import Event
    event_id = context.current_parameters['event_id']

    # Check first if there is a pre-allocated friendly id
    # (and use it in that case)
    friendly_ids = g.get('friendly_ids', {}).get(Contribution, {}).get(event_id, [])
    if friendly_ids:
        return friendly_ids.pop(0)

    assert event_id is not None
    return increment_and_get(Event._last_friendly_contribution_id, Event.id == event_id)


class CustomFieldsMixin:
    """Methods to process custom field data."""

    def get_field_value(self, field_id, raw=False):
        fv = next((v for v in self.field_values if v.contribution_field_id == field_id), None)
        if raw:
            return fv
        else:
            return fv.friendly_data if fv else ''

    @no_autoflush
    def set_custom_field(self, field_id, field_value):
        fv = self.get_field_value(field_id, raw=True)
        if not fv:
            field_value_cls = type(self).field_values.prop.mapper.class_
            fv = field_value_cls(contribution_field=self.event.get_contribution_field(field_id))
            self.field_values.append(fv)
        old_value = fv.data
        fv.data = field_value
        return old_value


class Contribution(SearchableTitleMixin, SearchableDescriptionMixin, ProtectionManagersMixin, LocationMixin,
                   AttachedItemsMixin, AttachedNotesMixin, PersonLinkMixin, AuthorsSpeakersMixin, CustomFieldsMixin,
                   db.Model):
    __tablename__ = 'contributions'
    __auto_table_args = (db.Index(None, 'friendly_id', 'event_id', unique=True,
                                  postgresql_where=db.text('NOT is_deleted')),
                         db.Index(None, 'event_id', 'track_id'),
                         db.Index(None, 'event_id', 'abstract_id'),
                         db.Index(None, 'abstract_id', unique=True, postgresql_where=db.text('NOT is_deleted')),
                         db.CheckConstraint('session_block_id IS NULL OR session_id IS NOT NULL',
                                            'session_block_if_session'),
                         db.CheckConstraint("date_trunc('minute', duration) = duration", 'duration_no_seconds'),
                         db.ForeignKeyConstraint(['session_block_id', 'session_id'],
                                                 ['events.session_blocks.id', 'events.session_blocks.session_id']),
                         {'schema': 'events'})
    person_link_relation_name = 'ContributionPersonLink'
    person_link_backref_name = 'contribution'
    location_backref_name = 'contributions'
    disallowed_protection_modes = frozenset()
    inheriting_have_acl = True
    possible_render_modes = {RenderMode.html, RenderMode.markdown}
    default_render_mode = RenderMode.markdown
    allow_relationship_preloading = True

    PRELOAD_EVENT_ATTACHED_ITEMS = True
    PRELOAD_EVENT_NOTES = True
    ATTACHMENT_FOLDER_ID_COLUMN = 'contribution_id'

    @classmethod
    def allocate_friendly_ids(cls, event, n):
        """Allocate n Contribution friendly_ids.

        This is needed so that we can allocate all IDs in one go. Not doing
        so could result in DB deadlocks. All operations that create more than
        one contribution should use this method.

        :param event: the :class:`Event` in question
        :param n: the number of ids to pre-allocate
        """
        from indico.modules.events import Event
        fid = increment_and_get(Event._last_friendly_contribution_id, Event.id == event.id, n)
        friendly_ids = g.setdefault('friendly_ids', {})
        friendly_ids.setdefault(cls, {})[event.id] = list(range(fid - n + 1, fid + 1))

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
        db.ForeignKey('events.tracks.id', ondelete='SET NULL'),
        index=True,
        nullable=True
    )
    abstract_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        index=True,
        nullable=True
    )
    type_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contribution_types.id'),
        index=True,
        nullable=True
    )
    code = db.Column(
        db.String,
        nullable=False,
        default=''
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

    event = db.relationship(
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
            primaryjoin='(Contribution.abstract_id == Abstract.id) & ~Contribution.is_deleted',
            lazy=True,
            uselist=False
        )
    )
    track = db.relationship(
        'Track',
        lazy=True,
        backref=db.backref(
            'contributions',
            primaryjoin='(Contribution.track_id == Track.id) & ~Contribution.is_deleted',
            lazy=True,
            passive_deletes=True
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
    #: The accepted paper revision
    _accepted_paper_revision = db.relationship(
        'PaperRevision',
        lazy=True,
        viewonly=True,
        uselist=False,
        primaryjoin=lambda: db.and_(PaperRevision._contribution_id == Contribution.id,
                                    PaperRevision.state == PaperRevisionState.accepted),
    )
    #: Paper files not submitted for reviewing
    pending_paper_files = db.relationship(
        'PaperFile',
        lazy=True,
        viewonly=True,
        primaryjoin='(PaperFile._contribution_id == Contribution.id) & (PaperFile.revision_id.is_(None))',
    )
    #: Paper reviewing judges
    paper_judges = db.relationship(
        'User',
        secondary='event_paper_reviewing.judges',
        collection_class=set,
        lazy=True,
        backref=db.backref(
            'judge_for_contributions',
            collection_class=set,
            lazy=True
        )
    )
    #: Paper content reviewers
    paper_content_reviewers = db.relationship(
        'User',
        secondary='event_paper_reviewing.content_reviewers',
        collection_class=set,
        lazy=True,
        backref=db.backref(
            'content_reviewer_for_contributions',
            collection_class=set,
            lazy=True
        )
    )
    #: Paper layout reviewers
    paper_layout_reviewers = db.relationship(
        'User',
        secondary='event_paper_reviewing.layout_reviewers',
        collection_class=set,
        lazy=True,
        backref=db.backref(
            'layout_reviewer_for_contributions',
            collection_class=set,
            lazy=True
        )
    )

    @declared_attr
    def _paper_last_revision(cls):
        # Incompatible with joinedload
        subquery = (db.select([db.func.max(PaperRevision.submitted_dt)])
                    .where(PaperRevision._contribution_id == cls.id)
                    .correlate_except(PaperRevision)
                    .scalar_subquery())
        return db.relationship(
            'PaperRevision',
            uselist=False,
            lazy=True,
            viewonly=True,
            primaryjoin=db.and_(PaperRevision._contribution_id == cls.id, PaperRevision.submitted_dt == subquery)
        )

    # relationship backrefs:
    # - _paper_files (PaperFile._contribution)
    # - _paper_revisions (PaperRevision._contribution)
    # - attachment_folders (AttachmentFolder.contribution)
    # - editables (Editable.contribution)
    # - legacy_mapping (LegacyContributionMapping.contribution)
    # - note (EventNote.contribution)
    # - room_reservation_links (ReservationLink.contribution)
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
                 .correlate_except(SubContribution)
                 .scalar_subquery())
        return db.column_property(query, deferred=True)

    @declared_attr
    def _paper_revision_count(cls):
        query = (db.select([db.func.count(PaperRevision.id)])
                 .where(PaperRevision._contribution_id == cls.id)
                 .correlate_except(PaperRevision)
                 .scalar_subquery())
        return db.column_property(query, deferred=True)

    def __init__(self, **kwargs):
        # explicitly initialize those relationships with None to avoid
        # an extra query to check whether there is an object associated
        # when assigning a new one (e.g. during cloning)
        kwargs.setdefault('note', None)
        kwargs.setdefault('timetable_entry', None)
        super().__init__(**kwargs)

    @classmethod
    def preload_acl_entries(cls, event):
        cls.preload_relationships(cls.query.with_parent(event), 'acl_entries')

    @property
    def location_parent(self):
        if self.session_block_id is not None:
            return self.session_block
        elif self.session_id is not None:
            return self.session
        else:
            return self.event

    @property
    def protection_parent(self):
        return self.session if self.session_id is not None else self.event

    @property
    def start_dt(self):
        return self.timetable_entry.start_dt if self.timetable_entry else None

    @property
    def end_dt(self):
        return self.timetable_entry.start_dt + self.duration if self.timetable_entry else None

    @property
    def start_dt_poster(self):
        if self.session and self.session.is_poster and self.timetable_entry and self.timetable_entry.parent:
            return self.timetable_entry.parent.start_dt

    @property
    def end_dt_poster(self):
        if self.session and self.session.is_poster and self.timetable_entry and self.timetable_entry.parent:
            return self.timetable_entry.parent.end_dt

    @property
    def duration_poster(self):
        if self.session and self.session.is_poster and self.timetable_entry and self.timetable_entry.parent:
            return self.timetable_entry.parent.duration

    @property
    def start_dt_display(self):
        """The displayed start time of the contribution.

        This is the start time of the poster session if applicable,
        otherwise the start time of the contribution itself.
        """
        return self.start_dt_poster or self.start_dt

    @property
    def end_dt_display(self):
        """The displayed end time of the contribution.

        This is the end time of the poster session if applicable,
        otherwise the end time of the contribution itself.
        """
        return self.end_dt_poster or self.end_dt

    @property
    def duration_display(self):
        """The displayed duration of the contribution.

        This is the duration of the poster session if applicable,
        otherwise the duration of the contribution itself.
        """
        return self.duration_poster or self.duration

    @property
    def submitters(self):
        return {person_link for person_link in self.person_links if person_link.is_submitter}

    @locator_property
    def locator(self):
        return dict(self.event.locator, contrib_id=self.id)

    @property
    def verbose_title(self):
        return f'#{self.friendly_id} ({self.title})'

    @property
    def paper(self):
        return Paper(self) if self._paper_last_revision else None

    @property
    def allowed_types_for_editable(self):
        from indico.modules.events.editing.settings import editable_type_settings
        if not self.event.has_feature('editing'):
            return []

        submitted_for = {editable.type.name for editable in self.editables}
        return [
            editable_type
            for editable_type in self.event.editable_types
            if editable_type not in submitted_for
            and editable_type_settings[EditableType[editable_type]].get(self.event, 'submission_enabled')
        ]

    @property
    def enabled_editables(self):
        """Return all submitted editables with enabled types."""
        from indico.modules.events.editing.settings import editing_settings
        if not self.event.has_feature('editing'):
            return []

        enabled_editable_types = editing_settings.get(self.event, 'editable_types')
        enabled_editables = [editable for editable in self.editables if editable.type.name in enabled_editable_types]
        order = list(EditableType)
        return sorted(enabled_editables, key=lambda editable: order.index(editable.type))

    @property
    def has_published_editables(self):
        return any(e.published_revision_id is not None for e in self.enabled_editables)

    @property
    def slug(self):
        return slugify(self.friendly_id, self.title, maxlen=30)

    def is_paper_reviewer(self, user):
        return user in self.paper_content_reviewers or user in self.paper_layout_reviewers

    def __repr__(self):
        return format_repr(self, 'id', is_deleted=False, _text=self.title)

    def can_manage(self, user, permission=None, allow_admin=True, check_parent=True, explicit_permission=False):
        if super().can_manage(user, permission, allow_admin=allow_admin, check_parent=check_parent,
                              explicit_permission=explicit_permission):
            return True
        if (check_parent and self.session_id is not None and
                self.session.can_manage(user, 'coordinate', allow_admin=allow_admin,
                                        explicit_permission=explicit_permission) and
                session_coordinator_priv_enabled(self.event, 'manage-contributions')):
            return True
        return False

    def can_edit(self, user):
        # Submitters can edit their own contributions if configured
        from indico.modules.events.contributions import contribution_settings
        submitters_can_edit = contribution_settings.get(self.event, 'submitters_can_edit')
        return self.can_manage(user, permission=('submit' if submitters_can_edit else None))

    @materialize_iterable()
    def get_manage_button_options(self, *, note_may_exist=False):
        if self.event.is_locked:
            return
        if self.can_edit_note(session.user) and (note_may_exist or not self.has_note):
            yield 'notes_edit'
        if self.can_edit(session.user):
            yield 'contribution_edit'
        if self.can_manage(session.user):
            yield 'contribution_protection_edit'
        if self.can_manage_attachments(session.user):
            yield 'attachments_edit'
        if self.can_manage(session.user):
            yield 'contribution_subcontributions_edit'

    def get_non_inheriting_objects(self):
        """Get a set of child objects that do not inherit protection."""
        return get_non_inheriting_objects(self)

    def is_user_associated(self, user, check_abstract=False):
        if user is None:
            return False
        if check_abstract and self.abstract and self.abstract.submitter == user:
            return True
        return any(pl.person.user == user for pl in self.person_links if pl.person.user)

    def can_submit_proceedings(self, user):
        """Whether the user can submit editables/papers."""
        if user is None:
            return False
        # The submitter of the original abstract is always authorized
        if self.abstract and self.abstract.submitter == user:
            return True
        # Otherwise only users with submission rights are authorized
        return self.can_manage(user, 'submit', allow_admin=False, check_parent=False)

    def get_editable(self, editable_type):
        """Get the editable of the given type."""
        return next((e for e in self.editables if e.type == editable_type), None)

    def log(self, *args, **kwargs):
        """Log with prefilled metadata for the contribution."""
        return self.event.log(*args, meta={'contribution_id': self.id}, **kwargs)


Contribution.register_protection_events()


@listens_for(mapper, 'after_configured', once=True)
def _mapper_configured():
    # Contribution.effective_protection_mode -- the effective protection mode
    # (public/protected) of the contribution, even if it's inheriting it from
    # its event or session
    protection_mode_case = db.case([
        ((Contribution.protection_mode == ProtectionMode.inheriting) & Contribution.session_id.is_(None),
         Event.effective_protection_mode),
        ((Contribution.protection_mode == ProtectionMode.inheriting) & Contribution.session_id.isnot(None),
         select([Session.effective_protection_mode])
         .where(Session.id == Contribution.session_id)
         .correlate(Contribution)
         .scalar_subquery())
    ], else_=Contribution.protection_mode)
    query = (
        select([protection_mode_case])
        .where(Event.id == Contribution.event_id)
        .correlate(Contribution)
        .scalar_subquery()
    )
    Contribution.effective_protection_mode = column_property(query, deferred=True)

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
    sql = '''
        CREATE CONSTRAINT TRIGGER consistent_timetable
        AFTER INSERT OR UPDATE OF event_id, session_id, session_block_id, duration
        ON {}
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE PROCEDURE events.check_timetable_consistency('contribution');
    '''.format(target.fullname)
    DDL(sql).execute(conn)
