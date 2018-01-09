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
from indico.modules.events.contributions.models.fields import ContributionFieldValueBase
from indico.util.string import format_repr, return_ascii, text_to_repr


class AbstractFieldValue(ContributionFieldValueBase):
    """Store a field values related to abstracts."""

    __tablename__ = 'abstract_field_values'
    __table_args__ = {'schema': 'event_abstracts'}
    contribution_field_backref_name = 'abstract_values'

    abstract_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        index=True,
        nullable=False,
        primary_key=True
    )

    # relationship backrefs:
    # - abstract (Abstract.field_values)

    @return_ascii
    def __repr__(self):
        text = text_to_repr(self.data) if isinstance(self.data, unicode) else self.data
        return format_repr(self, 'abstract_id', 'contribution_field_id', _text=text)
