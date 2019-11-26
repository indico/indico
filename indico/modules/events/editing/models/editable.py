# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii
from indico.util.struct.enum import IndicoEnum


class EditableType(int, IndicoEnum):
    paper = 1
    slides = 2


class Editable(db.Model):
    __tablename__ = 'editables'
    __table_args__ = (db.UniqueConstraint('contribution_id', 'type'),
                      {'schema': 'event_editing'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    contribution_id = db.Column(
        db.ForeignKey('events.contributions.id'),
        index=True,
        nullable=False
    )
    type = db.Column(
        PyIntEnum(EditableType),
        nullable=False
    )
    editor_id = db.Column(
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    published_revision_id = db.Column(
        db.ForeignKey('event_editing.revisions.id'),
        index=True,
        nullable=True
    )

    contribution = db.relationship(
        'Contribution',
        lazy=True,
        backref=db.backref(
            'editables',
            lazy=True,
        )
    )
    editor = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'editor_for_editables',
            lazy='dynamic'
        )
    )
    published_revision = db.relationship(
        'EditingRevision',
        foreign_keys=published_revision_id,
        lazy=True,
    )

    # relationship backrefs:
    # - revisions (EditingRevision.editable)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'contribution_id', 'type')

    # TODO: state - either a column property referencing the newest revision's state or a normal column

    @locator_property
    def locator(self):
        return dict(self.contribution.locator, type=self.type.name)

    def can_comment(self, user):
        return self.editor == user or self.contribution.is_user_associated(user, check_abstract=True)

    @property
    def editors(self):
        editors = [self.editor] if self.editor else []
        editors.extend([revision.editor for revision in self.revisions
                        if revision.editor and revision.editor != self.editor])
        return editors
