# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from marshmallow.fields import Boolean, DateTime, Field, Float, Function, Integer, List, Method, Nested, String
from marshmallow_enum import EnumField

from indico.core.marshmallow import mm
from indico.modules.events.contributions.schemas import ContributionSchema
from indico.modules.events.papers.models.comments import PaperReviewComment
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.reviews import PaperReview
from indico.modules.events.papers.models.revisions import PaperRevision, PaperRevisionState
from indico.modules.events.schemas import EventSchema
from indico.modules.users.schemas import UserSchema
from indico.util.mimetypes import icon_from_mimetype


class PaperFileSchema(mm.ModelSchema):
    icon = Method('get_icon')

    class Meta:
        model = PaperFile
        fields = ('id', 'revision_id', 'content_type', 'filename', 'icon')

    def get_icon(self, paper_file):
        return icon_from_mimetype(paper_file.content_type)


class PaperRevisionStateSchema(mm.Schema):
    title = String()
    css_class = String()


class PaperAction(mm.Schema):
    name = String()
    css_class = String()


class PaperCommentVisibilitySchema(mm.Schema):
    name = String()
    title = String()


class PaperRevisionTimelineField(Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if not value:
            return []

        serialized = []
        for timeline_item in value:
            serialized_item = {'timeline_item_type': timeline_item.timeline_item_type}
            if timeline_item.timeline_item_type == 'comment':
                serialized_item.update(paper_review_comment_schema.dump(timeline_item))
            elif timeline_item.timeline_item_type == 'review':
                serialized_item.update(paper_review_schema.dump(timeline_item))
            serialized.append(serialized_item)
        return serialized


class PaperRevisionSchema(mm.ModelSchema):
    submitter = Nested(UserSchema)
    judge = Nested(UserSchema)
    spotlight_file = Nested(PaperFileSchema)
    files = Nested(PaperFileSchema, many=True)
    state = EnumField(PaperRevisionState)
    timeline = PaperRevisionTimelineField()

    class Meta:
        model = PaperRevision
        fields = ('id', 'submitted_dt', 'judgment_dt', 'submitter', 'judge', 'spotlight_file', 'files',
                  'is_last_revision', 'number', 'state', 'timeline', 'judgment_comment')


class PaperReviewSchema(mm.ModelSchema):
    score = Float(as_string=True)
    created_dt = DateTime()
    user = Nested(UserSchema)
    modified_dt = DateTime()
    visibility = Nested(PaperCommentVisibilitySchema)
    proposed_action = Nested(PaperAction)
    group = Function(lambda review: {'title': str(review.group.title)})
    ratings = Function(lambda review: [{'value': rating.value} for rating in review.ratings])

    class Meta:
        model = PaperReview
        fields = ('id', 'score', 'created_dt', 'user', 'comment', 'modified_dt', 'visibility', 'proposed_action',
                  'group', 'ratings')


class PaperReviewCommentSchema(mm.ModelSchema):
    user = Nested(UserSchema)
    text = String()
    visibility = Nested(PaperCommentVisibilitySchema)
    created_dt = DateTime()
    modified_dt = DateTime()
    modified_by = Nested(UserSchema)

    class Meta:
        model = PaperReviewComment
        fields = ('id', 'user', 'text', 'visibility', 'created_dt', 'modified_dt', 'modified_by')


class PaperSchema(mm.Schema):
    is_in_final_state = Boolean()
    contribution = Nested(ContributionSchema)
    event = Nested(EventSchema)
    revisions = Nested(PaperRevisionSchema, many=True)
    last_revision = Nested(PaperRevisionSchema)
    state = Nested(PaperRevisionStateSchema)
    rating_range = List(Integer(), attribute='cfp.rating_range')


paper_schema = PaperSchema()
paper_review_schema = PaperReviewSchema()
paper_review_comment_schema = PaperReviewCommentSchema()
