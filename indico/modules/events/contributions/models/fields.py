# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


def _get_next_position(context):
    """Get the next contribution field position for the event."""
    event_id = context.current_parameters['event_id']
    res = db.session.query(db.func.max(ContributionField.position)).filter_by(event_id=event_id).one()
    return (res[0] or 0) + 1


class ContributionField(db.Model):
    __tablename__ = 'contribution_fields'
    __table_args__ = {'schema': 'events'}

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
    position = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_position
    )
    title = db.Column(
        db.String,
        nullable=False
    )
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    is_required = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    field_type = db.Column(
        db.String,
        nullable=True
    )
    field_data = db.Column(
        JSON,
        nullable=False,
        default={}
    )

    event_new = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'contribution_fields',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - contribution_values (ContributionFieldValue.contribution_field)

    # TODO: add field logic similar to what we did for survey fields

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'field_type', is_required=False, is_active=True, _text=self.title)


class ContributionFieldValueBase(db.Model):
    __abstract__ = True
    #: The name of the backref on the `ContributionField`
    contribution_field_backref_name = None

    data = db.Column(
        JSON,
        nullable=False
    )

    @declared_attr
    def contribution_field_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('events.contribution_fields.id'),
            primary_key=True,
            index=True
        )

    @declared_attr
    def contribution_field(cls):
        return db.relationship(
            'ContributionField',
            lazy=False,
            backref=db.backref(
                cls.contribution_field_backref_name,
                cascade='all, delete-orphan',
                lazy=True
            )
        )


class ContributionFieldValue(ContributionFieldValueBase):
    __tablename__ = 'contribution_field_values'
    __table_args__ = {'schema': 'events'}
    contribution_field_backref_name = 'contribution_values'

    contribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        index=True,
        nullable=False,
        primary_key=True
    )

    # relationship backrefs:
    # - contribution (Contribution.field_values)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'contribution_id', 'contribution_field_id', _text=self.data)
