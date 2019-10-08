# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from markupsafe import escape
from marshmallow.fields import Boolean, DateTime, Field, Float, Function, Integer, List, Nested, String
from marshmallow_enum import EnumField

from indico.core.marshmallow import mm
from indico.modules.events.contributions.schemas import ContributionSchema
from indico.modules.events.models.events import Event
from indico.modules.events.papers.models.comments import PaperReviewComment
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.reviews import PaperReview
from indico.modules.events.papers.models.revisions import PaperRevision, PaperRevisionState
from indico.modules.users.schemas import UserSchema
from indico.util.mimetypes import icon_from_mimetype
from indico.web.flask.util import url_for


class PaperEventSchema(mm.ModelSchema):
    class Meta:
        model = Event
        fields = ('id', 'title', 'is_locked')


class PaperFileSchema(mm.ModelSchema):
    icon = Function(lambda paper_file: icon_from_mimetype(paper_file.content_type))
    download_url = Function(lambda paper_file: url_for('papers.download_file', paper_file))

    class Meta:
        model = PaperFile
        fields = ('id', 'revision_id', 'content_type', 'filename', 'icon', 'download_url')


class PaperRevisionStateSchema(mm.Schema):
    name = String()
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
    files = List(Nested(PaperFileSchema))
    state = EnumField(PaperRevisionState)
    timeline = PaperRevisionTimelineField()
    judgment_comment_html = Function(lambda revision: escape(revision.judgment_comment))

    class Meta:
        model = PaperRevision
        fields = ('id', 'submitted_dt', 'judgment_dt', 'submitter', 'judge', 'spotlight_file', 'files',
                  'is_last_revision', 'number', 'state', 'timeline', 'judgment_comment', 'judgment_comment_html')


class PaperReviewSchema(mm.ModelSchema):
    score = Float(as_string=True)
    user = Nested(UserSchema)
    visibility = Nested(PaperCommentVisibilitySchema)
    proposed_action = Nested(PaperAction)
    group = Function(lambda review: {'title': unicode(review.group.title)})
    ratings = Function(lambda review: [{'value': rating.value} for rating in review.ratings])
    comment_html = Function(lambda review: escape(review.comment))

    class Meta:
        model = PaperReview
        fields = ('id', 'score', 'created_dt', 'user', 'comment', 'comment_html', 'modified_dt', 'visibility',
                  'proposed_action', 'group', 'ratings')


class PaperReviewCommentSchema(mm.ModelSchema):
    user = Nested(UserSchema)
    visibility = Nested(PaperCommentVisibilitySchema)
    modified_by = Nested(UserSchema)
    html = Function(lambda comment: escape(comment.text))

    class Meta:
        model = PaperReviewComment
        fields = ('id', 'user', 'text', 'html', 'visibility', 'created_dt', 'modified_dt', 'modified_by')


class PaperSchema(mm.Schema):
    is_in_final_state = Boolean()
    contribution = Nested(ContributionSchema)
    event = Nested(PaperEventSchema)
    revisions = List(Nested(PaperRevisionSchema))
    last_revision = Nested(PaperRevisionSchema)
    state = Nested(PaperRevisionStateSchema)
    rating_range = List(Integer(), attribute='cfp.rating_range')


paper_schema = PaperSchema()
paper_review_schema = PaperReviewSchema()
paper_review_comment_schema = PaperReviewCommentSchema()
