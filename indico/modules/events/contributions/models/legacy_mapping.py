# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


class LegacyContributionMapping(db.Model):
    """Legacy contribution id mapping.

    Legacy contributions had ids unique only within their event.
    Additionally, some very old contributions had non-numeric IDs.
    This table maps those ids to the new globally unique contribution id.
    """

    __tablename__ = 'legacy_contribution_id_map'
    __table_args__ = {'schema': 'events'}

    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        primary_key=True,
        autoincrement=False
    )
    legacy_contribution_id = db.Column(
        db.String,
        primary_key=True
    )
    contribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        nullable=False,
        index=True
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'legacy_contribution_mappings',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    contribution = db.relationship(
        'Contribution',
        lazy=False,
        backref=db.backref(
            'legacy_mapping',
            cascade='all, delete-orphan',
            uselist=False,
            lazy=True
        )
    )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'event_id', 'legacy_contribution_id', 'contribution_id')


class LegacySubContributionMapping(db.Model):
    """Legacy subcontribution id mapping.

    Legacy subcontributions had ids unique only within their event
    and contribution.  This table maps those ids to the new globally
    unique subcontribution id.
    """

    __tablename__ = 'legacy_subcontribution_id_map'
    __table_args__ = {'schema': 'events'}

    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        primary_key=True,
        autoincrement=False
    )
    legacy_contribution_id = db.Column(
        db.String,
        primary_key=True
    )
    legacy_subcontribution_id = db.Column(
        db.String,
        primary_key=True
    )
    subcontribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.subcontributions.id', name='fk_legacy_subcontribution_id_map_subcontribution'),
        nullable=False,
        index=True
    )

    event = db.relationship(
        'Event',
        lazy=True,
        backref=db.backref(
            'legacy_subcontribution_mappings',
            cascade='all, delete-orphan',
            lazy='dynamic'
        )
    )
    subcontribution = db.relationship(
        'SubContribution',
        lazy=False,
        backref=db.backref(
            'legacy_mapping',
            cascade='all, delete-orphan',
            uselist=False,
            lazy=True
        )
    )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'event_id', 'legacy_contribution_id', 'legacy_subcontribution_id',
                           'subcontribution_id')
