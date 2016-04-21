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

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.descriptions import DescriptionMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.modules.events.contributions.models.contributions import _get_next_friendly_id
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii, MarkdownText


class Abstract(DescriptionMixin, db.Model):
    """Represents an abstract that can be associated to a Contribution."""

    __tablename__ = 'abstracts'
    __auto_table_args = (db.UniqueConstraint('friendly_id', 'event_id'),
                         {'schema': 'event_abstracts'})

    description_wrapper = MarkdownText

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The friendly ID for the abstract (same as the legacy id in ZODB)
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
    type_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contribution_types.id'),
        nullable=True,
        index=True
    )
    accepted_track_id = db.Column(
        db.Integer,
        nullable=True,
        index=True
    )
    accepted_type_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contribution_types.id'),
        nullable=True,
        index=True
    )
    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'abstracts',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    #: Data stored in abstract/contribution fields
    field_values = db.relationship(
        'AbstractFieldValue',
        lazy=True,
        cascade='all, delete-orphan',
        backref=db.backref(
            'abstract',
            lazy=True
        )
    )
    type = db.relationship(
        'ContributionType',
        lazy=True,
        foreign_keys=[type_id],
        backref=db.backref(
            'abstracts',
            lazy=True
        )
    )
    accepted_type = db.relationship(
        'ContributionType',
        lazy=True,
        foreign_keys=[accepted_type_id],
        backref=db.backref(
            'accepted_as_abstracts',
            lazy=True
        )
    )
    # relationship backrefs:
    # - contribution (Contribution.abstract)
    # - judgments (Judgment.abstract)

    @locator_property
    def locator(self):
        return dict(self.event_new.locator, abstractId=self.friendly_id, confId=self.event_id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', friendly_id=self.friendly_id)

    def get_field_value(self, field_id):
        return next((v.friendly_data for v in self.field_values if v.contribution_field_id == field_id), '')

    @property
    def as_legacy(self):
        amgr = self.event_new.as_legacy.getAbstractMgr()
        return amgr.getAbstractById(str(self.friendly_id))

    @property
    def accepted_track(self):
        return self.event_new.as_legacy.getTrackById(str(self.accepted_track_id))
