# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db.sqlalchemy import db
from indico.modules.events.models.persons import PersonLinkBase
from indico.util.string import format_repr, return_ascii


class SessionBlockPersonLink(PersonLinkBase):
    """Association between EventPerson and SessionBlock.

    Also known as a 'session convener'.
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
