# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.modules.events.models.references import ReferenceModelBase
from indico.util.string import format_repr, return_ascii


class ContributionReference(ReferenceModelBase):
    __tablename__ = 'contribution_references'
    __table_args__ = {'schema': 'events'}
    reference_backref_name = 'contribution_references'

    contribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - contribution (Contribution.references)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'contribution_id', 'reference_type_id', _text=self.value)


class SubContributionReference(ReferenceModelBase):
    __tablename__ = 'subcontribution_references'
    __table_args__ = {'schema': 'events'}
    reference_backref_name = 'subcontribution_references'

    subcontribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.subcontributions.id'),
        nullable=False,
        index=True
    )

    # relationship backrefs:
    # - subcontribution (SubContribution.references)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'subcontribution_id', 'reference_type_id', _text=self.value)
