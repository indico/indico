# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db.sqlalchemy import PyIntEnum, db
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.models.persons import PersonLinkBase
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


class AbstractPersonLink(PersonLinkBase):
    """Association between EventPerson and Abstract."""

    __tablename__ = 'abstract_person_links'
    __auto_table_args = {'schema': 'event_abstracts'}
    person_link_backref_name = 'abstract_links'
    person_link_unique_columns = ('abstract_id',)
    object_relationship_name = 'abstract'

    abstract_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        index=True,
        nullable=False
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
    # - abstract (Abstract.person_links)

    @locator_property
    def locator(self):
        return dict(self.abstract.locator, person_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'person_id', 'abstract_id', is_speaker=False, author_type=None,
                           _text=self.full_name)
