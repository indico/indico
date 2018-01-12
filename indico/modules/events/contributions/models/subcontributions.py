# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.core.db import db
from indico.core.db.sqlalchemy.attachments import AttachedItemsMixin
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin, RenderMode
from indico.core.db.sqlalchemy.notes import AttachedNotesMixin
from indico.core.db.sqlalchemy.util.queries import increment_and_get
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


def _get_next_friendly_id(context):
    """Get the next friendly id for a sub-contribution."""
    from indico.modules.events.contributions.models.contributions import Contribution
    contribution_id = context.current_parameters['contribution_id']
    assert contribution_id is not None
    return increment_and_get(Contribution._last_friendly_subcontribution_id, Contribution.id == contribution_id)


def _get_next_position(context):
    """Get the next menu entry position for the event."""
    contribution_id = context.current_parameters['contribution_id']
    res = db.session.query(db.func.max(SubContribution.position)).filter_by(contribution_id=contribution_id).one()
    return (res[0] or 0) + 1


class SubContribution(DescriptionMixin, AttachedItemsMixin, AttachedNotesMixin, db.Model):
    __tablename__ = 'subcontributions'
    __table_args__ = (db.Index(None, 'friendly_id', 'contribution_id', unique=True),
                      {'schema': 'events'})

    PRELOAD_EVENT_ATTACHED_ITEMS = True
    PRELOAD_EVENT_NOTES = True
    ATTACHMENT_FOLDER_ID_COLUMN = 'subcontribution_id'
    possible_render_modes = {RenderMode.html, RenderMode.markdown}
    default_render_mode = RenderMode.markdown

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The human-friendly ID for the sub-contribution
    friendly_id = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_friendly_id
    )
    contribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        index=True,
        nullable=False
    )
    position = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_position
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    duration = db.Column(
        db.Interval,
        nullable=False
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    #: External references associated with this contribution
    references = db.relationship(
        'SubContributionReference',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'subcontribution',
            lazy=True
        )
    )
    #: Persons associated with this contribution
    person_links = db.relationship(
        'SubContributionPersonLink',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'subcontribution',
            lazy=True
        )
    )

    # relationship backrefs:
    # - attachment_folders (AttachmentFolder.subcontribution)
    # - contribution (Contribution.subcontributions)
    # - legacy_mapping (LegacySubContributionMapping.subcontribution)
    # - note (EventNote.subcontribution)

    def __init__(self, **kwargs):
        # explicitly initialize this relationship with None to avoid
        # an extra query to check whether there is an object associated
        # when assigning a new one (e.g. during cloning)
        kwargs.setdefault('note', None)
        super(SubContribution, self).__init__(**kwargs)

    @property
    def event(self):
        return self.contribution.event

    @locator_property
    def locator(self):
        return dict(self.contribution.locator, subcontrib_id=self.id)

    @property
    def is_protected(self):
        return self.contribution.is_protected

    @property
    def session(self):
        """Convenience property so all event entities have it"""
        return self.contribution.session if self.contribution.session_id is not None else None

    @property
    def timetable_entry(self):
        """Convenience property so all event entities have it"""
        return self.contribution.timetable_entry

    @property
    def speakers(self):
        return self.person_links

    @speakers.setter
    def speakers(self, value):
        self.person_links = value.keys()

    @property
    def location_parent(self):
        return self.contribution

    def get_access_list(self):
        return self.contribution.get_access_list()

    def get_manager_list(self, recursive=False):
        return self.contribution.get_manager_list(recursive=recursive)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', is_deleted=False, _text=self.title)

    def can_access(self, user, **kwargs):
        return self.contribution.can_access(user, **kwargs)

    def can_manage(self, user, permission=None, **kwargs):
        return self.contribution.can_manage(user, permission=permission, **kwargs)
