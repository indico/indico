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
