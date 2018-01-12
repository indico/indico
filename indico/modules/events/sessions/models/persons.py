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

from indico.core.db.sqlalchemy import db
from indico.modules.events.models.persons import PersonLinkBase
from indico.util.string import format_repr, return_ascii


class SessionBlockPersonLink(PersonLinkBase):
    """Association between EventPerson and SessionBlock.

    Also known as a 'session convener'
    """

    __tablename__ = 'session_block_person_links'
    __auto_table_args = {'schema': 'events'}
    person_link_backref_name = 'session_block_links'
    person_link_unique_columns = ('session_block_id',)
    object_relationship_name = 'session_block'

    session_block_id = db.Column(
        db.Integer,
        db.ForeignKey('events.session_blocks.id'),
        index=True,
        nullable=False
    )

    # relationship backrefs:
    # - session_block (SessionBlock.person_links)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'person_id', 'session_block_id', _text=self.full_name)
