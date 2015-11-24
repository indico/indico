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

from indico.core.db.sqlalchemy import db, PyIntEnum
from indico.util.string import return_ascii, format_repr
from indico.modules.events.models.persons import PersonLinkBase
from indico.util.struct.enum import IndicoEnum


class AuthorType(int, IndicoEnum):
    none = 0
    primary = 1
    secondary = 2


class ContributionPersonLink(PersonLinkBase):
    """Association between EventPerson and Contribution."""

    __tablename__ = 'contribution_person_links'
    __auto_table_args = {'schema': 'events'}
    person_link_backref_name = 'contribution_links'
    person_link_unique_columns = ('contribution_id',)

    contribution_id = db.Column(
        db.Integer,
        db.ForeignKey('events.contributions.id'),
        primary_key=True,
        index=True
    )
    is_speaker = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    author_type = db.Column(
        PyIntEnum(AuthorType),
        nullable=False,
        default=AuthorType.none
    )

    # relationship backrefs:
    # - contribution (Contribution.person_links)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'contribution_id', 'person_id', is_speaker=False, author_type=AuthorType.none,
                           _text=self.person.full_name)
