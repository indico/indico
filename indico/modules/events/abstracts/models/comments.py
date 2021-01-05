# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum
from indico.core.db.sqlalchemy.review_comments import ReviewCommentMixin
from indico.modules.events.abstracts.models.reviews import AbstractCommentVisibility
from indico.modules.events.models.reviews import ProposalCommentMixin
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii, text_to_repr


class AbstractComment(ProposalCommentMixin, ReviewCommentMixin, db.Model):
    __tablename__ = 'abstract_comments'
    __table_args__ = {'schema': 'event_abstracts'}
    marshmallow_aliases = {'_text': 'text'}
    user_backref_name = 'abstract_comments'
    user_modified_backref_name = 'modified_abstract_comments'

    @declared_attr
    def abstract_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey('event_abstracts.abstracts.id'),
            index=True,
            nullable=False
        )

    @declared_attr
    def visibility(cls):
        return db.Column(
            PyIntEnum(AbstractCommentVisibility),
            nullable=False,
            default=AbstractCommentVisibility.contributors
        )

    @declared_attr
    def abstract(cls):
        return db.relationship(
            'Abstract',
            lazy=True,
            backref=db.backref(
                'comments',
                primaryjoin='(AbstractComment.abstract_id == Abstract.id) & ~AbstractComment.is_deleted',
                order_by=cls.created_dt,
                cascade='all, delete-orphan',
                lazy=True,
            )
        )

    @locator_property
    def locator(self):
        return dict(self.abstract.locator, comment_id=self.id)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'abstract_id', is_deleted=False, _text=text_to_repr(self.text))

    def can_edit(self, user):
        if user is None:
            return False
        return self.user == user or self.abstract.event.can_manage(user)

    def can_view(self, user):
        if user is None:
            return False
        elif user == self.user:
            return True
        elif self.visibility == AbstractCommentVisibility.users:
            return True
        visibility_checks = {AbstractCommentVisibility.judges: [self.abstract.can_judge],
                             AbstractCommentVisibility.conveners: [self.abstract.can_judge, self.abstract.can_convene],
                             AbstractCommentVisibility.reviewers: [self.abstract.can_judge, self.abstract.can_convene,
                                                                   self.abstract.can_review],
                             AbstractCommentVisibility.contributors: [self.abstract.can_judge,
                                                                      self.abstract.can_convene,
                                                                      self.abstract.can_review,
                                                                      self.abstract.user_owns]}
        return any(fn(user) for fn in visibility_checks[self.visibility])
