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

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.util.string import format_repr, return_ascii
from indico.util.locators import locator_property


class ContributionType(db.Model):
    __tablename__ = 'contribution_types'

    @declared_attr
    def __table_args__(cls):
        return (db.Index('ix_uq_contribution_types_event_id_name_lower', cls.event_id, db.func.lower(cls.name),
                         unique=True),
                {'schema': 'events'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        index=True,
        nullable=False
    )
    name = db.Column(
        db.String,
        nullable=False
    )
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )

    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'contribution_types',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - abstract_reviews (AbstractReview.proposed_contribution_type)
    # - abstracts_accepted (Abstract.accepted_contrib_type)
    # - contributions (Contribution.type)
    # - proposed_abstracts (Abstract.submitted_contrib_type)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.name)

    @locator_property
    def locator(self):
        return dict(self.event_new.locator, contrib_type_id=self.id)
