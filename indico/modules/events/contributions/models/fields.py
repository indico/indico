# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.enum import RichIntEnum
from indico.util.i18n import _
from indico.util.locators import locator_property
from indico.util.string import format_repr, text_to_repr


def _get_next_position(context):
    """Get the next contribution field position for the event."""
    event_id = context.current_parameters['event_id']
    res = db.session.query(db.func.max(ContributionField.position)).filter(ContributionField.event_id == event_id).one()
    return (res[0] or 0) + 1


class ContributionFieldVisibility(RichIntEnum):
    __titles__ = [None, _('Everyone'), _('Managers and submitters'), _('Only managers')]
    __css_classes__ = [None, 'public', 'submitters', 'managers']
    public = 1
    managers_and_submitters = 2
    managers_only = 3


class ContributionField(db.Model):
    __tablename__ = 'contribution_fields'
    __table_args__ = (db.UniqueConstraint('event_id', 'legacy_id'),
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
    legacy_id = db.Column(
        db.String,
        nullable=True
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
    is_user_editable = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    visibility = db.Column(
        PyIntEnum(ContributionFieldVisibility),
        nullable=False,
        default=ContributionFieldVisibility.public
    )
    field_type = db.Column(
        db.String,
        nullable=True
    )
    field_data = db.Column(
        JSONB,
        nullable=False,
        default={}
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'contribution_fields',
            order_by=position,
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - abstract_values (AbstractFieldValue.contribution_field)
    # - contribution_values (ContributionFieldValue.contribution_field)

    def _get_field(self, management=False):
        from indico.modules.events.contributions import get_contrib_field_types
        try:
            impl = get_contrib_field_types()[self.field_type]
        except KeyError:
            return None
        return impl(self, management=management)

    @property
    def field(self):
        return self._get_field()

    @property
    def mgmt_field(self):
        return self._get_field(management=True)

    @property
    def is_public(self):
        return self.visibility == ContributionFieldVisibility.public

    @property
    def filter_choices(self):
        no_value = {None: _('No value')}
        return no_value | {x['id']: x['option'] for x in self.field_data.get('options', {})}

    def __repr__(self):
        return format_repr(self, 'id', 'field_type', is_required=False, is_active=True, _text=self.title)

    @locator_property
    def locator(self):
        return dict(self.event.locator, contrib_field_id=self.id)


class ContributionFieldValueBase(db.Model):
    __abstract__ = True
    #: The name of the backref on the `ContributionField`
    contribution_field_backref_name = None

    data = db.Column(
        JSONB,
        nullable=False
    )

    @declared_attr
    def contribution_field_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('events.contribution_fields.id', name=f'fk_{cls.__tablename__}_contribution_field'),
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

    @property
    def friendly_data(self):
        return self.contribution_field.field.get_friendly_value(self.data)


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

    def __repr__(self):
        text = text_to_repr(self.data) if isinstance(self.data, str) else self.data
        return format_repr(self, 'contribution_id', 'contribution_field_id', _text=text)
