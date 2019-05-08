# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


class SuggestedCategory(db.Model):
    __tablename__ = 'suggested_categories'
    __table_args__ = {'schema': 'users'}

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        index=True,
        autoincrement=False
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('categories.categories.id'),
        primary_key=True,
        index=True,
        autoincrement=False
    )
    is_ignored = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    score = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    category = db.relationship(
        'Category',
        lazy=False,
        backref=db.backref(
            'suggestions',
            lazy=True,
            cascade='all, delete-orphan'
        )
    )

    # relationship backrefs:
    # - user (User.suggested_categories)

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'user_id', 'category_id', 'score', is_ignored=False)

    @classmethod
    def merge_users(cls, target, source):
        """Merge the suggestions for two users.

        :param target: The target user of the merge.
        :param source: The user that is being merged into `target`.
        """
        target_suggestions = {x.category: x for x in target.suggested_categories}
        for suggestion in source.suggested_categories:
            new_suggestion = target_suggestions.get(suggestion.category) or cls(user=target,
                                                                                category=suggestion.category)
            new_suggestion.score = max(new_suggestion.score, suggestion.score)
            new_suggestion.is_ignored = new_suggestion.is_ignored or suggestion.is_ignored
        db.session.flush()
