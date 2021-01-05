# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from markupsafe import escape
from marshmallow import post_dump
from marshmallow.fields import Boolean, Decimal, Field, Function, Integer, List, Method, Nested, String
from marshmallow_enum import EnumField

from indico.core.marshmallow import mm
from indico.modules.events.contributions.schemas import ContributionSchema
from indico.modules.events.editing.models.editable import EditableType
from indico.modules.events.editing.settings import editable_type_settings, editing_settings
from indico.modules.events.models.events import Event
from indico.modules.events.papers.models.comments import PaperReviewComment
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.review_questions import PaperReviewQuestion
from indico.modules.events.papers.models.review_ratings import PaperReviewRating
from indico.modules.events.papers.models.reviews import PaperReview
from indico.modules.events.papers.models.revisions import PaperRevision, PaperRevisionState
from indico.modules.events.papers.util import is_type_reviewing_possible
from indico.modules.users.schemas import UserSchema
from indico.util.i18n import orig_string
from indico.util.mimetypes import icon_from_mimetype
from indico.web.flask.util import url_for


class CallForPapersSchema(mm.Schema):
    layout_review_questions = Nested('PaperReviewQuestionSchema', many=True)
    content_review_questions = Nested('PaperReviewQuestionSchema', many=True)
    rating_range = List(Integer())


class PaperEventSchema(mm.ModelSchema):
    cfp = Nested(CallForPapersSchema)

    class Meta:
        model = Event
        fields = ('id', 'title', 'is_locked', 'cfp')


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
        user = self.context.get('user')
        review_comment_schema = PaperReviewCommentSchema(context=self.context)
        review_schema = PaperReviewSchema(context=self.context)
        for timeline_item in value:
            if timeline_item.timeline_item_type in ('comment', 'review') and not timeline_item.can_view(user):
                continue

            serialized_item = {'timeline_item_type': timeline_item.timeline_item_type}
            if timeline_item.timeline_item_type == 'comment':
                serialized_item.update(review_comment_schema.dump(timeline_item))
            elif timeline_item.timeline_item_type == 'review':
                serialized_item.update(review_schema.dump(timeline_item))
            serialized.append(serialized_item)
        return serialized


class PaperReviewTypeSchema(mm.Schema):
    name = String()
    title = String()
    value = Integer()


class PaperRevisionSchema(mm.ModelSchema):
    submitter = Nested(UserSchema)
    judge = Nested(UserSchema)
    spotlight_file = Nested(PaperFileSchema)
    files = List(Nested(PaperFileSchema))
    state = EnumField(PaperRevisionState)
    timeline = PaperRevisionTimelineField()
    judgment_comment_html = Function(lambda revision: escape(revision.judgment_comment))
    reviewer_data = Method('_get_reviewer_data')

    class Meta:
        model = PaperRevision
        fields = ('id', 'submitted_dt', 'judgment_dt', 'submitter', 'judge', 'spotlight_file', 'files',
                  'is_last_revision', 'number', 'state', 'timeline', 'judgment_comment', 'judgment_comment_html',
                  'reviewer_data')

    def _get_reviewer_data(self, revision):
        if not revision.is_last_revision:
            return None

        data = dict(revision.get_reviewer_render_data(self.context.get('user')))
        review_type_schema = PaperReviewTypeSchema()
        for name in ('groups', 'missing_groups', 'reviewed_groups'):
            data[name] = [review_type_schema.dump(item.instance) for item in data[name]]

        reviews = {}
        for key, value in data['reviews'].viewitems():
            reviews[orig_string(key.instance.title)] = paper_review_schema.dump(value)
        data['reviews'] = reviews
        return data


class PaperReviewQuestionSchema(mm.ModelSchema):
    class Meta:
        model = PaperReviewQuestion
        fields = ('id', 'type', 'field_type', 'title', 'position', 'description', 'is_required', 'field_data')


class PaperRatingSchema(mm.ModelSchema):
    question = Nested(PaperReviewQuestionSchema)

    class Meta:
        model = PaperReviewRating
        fields = ('id', 'value', 'question')

    @post_dump(pass_many=True)
    def sort_ratings(self, data, many, **kwargs):
        if many:
            data = sorted(data, key=lambda rating: rating['question']['position'])
        return data


class PaperReviewSchema(mm.ModelSchema):
    score = Decimal(places=2, as_string=True)
    user = Nested(UserSchema)
    visibility = Nested(PaperCommentVisibilitySchema)
    proposed_action = Nested(PaperAction)
    ratings = Nested(PaperRatingSchema, many=True)
    group = Nested(PaperReviewTypeSchema, attribute='group.instance')
    comment_html = Function(lambda review: escape(review.comment))
    can_edit = Method('_can_edit_review')

    class Meta:
        model = PaperReview
        fields = ('id', 'score', 'created_dt', 'user', 'comment', 'comment_html', 'modified_dt', 'visibility',
                  'proposed_action', 'group', 'ratings', 'can_edit')

    def _can_edit_review(self, review):
        user = self.context.get('user')
        cfp = review.revision.paper.cfp
        return review.can_edit(user, check_state=True) and is_type_reviewing_possible(cfp, review.type)


class PaperReviewCommentSchema(mm.ModelSchema):
    user = Nested(UserSchema)
    visibility = Nested(PaperCommentVisibilitySchema)
    modified_by = Nested(UserSchema)
    html = Function(lambda comment: escape(comment.text))
    can_edit = Function(lambda comment, ctx: comment.can_edit(ctx.get('user')))
    can_view = Function(lambda comment, ctx: comment.can_view(ctx.get('user')))

    class Meta:
        model = PaperReviewComment
        fields = ('id', 'user', 'text', 'html', 'visibility', 'created_dt', 'modified_dt', 'modified_by', 'can_edit',
                  'can_view')


class PaperSchema(mm.Schema):
    is_in_final_state = Boolean()
    contribution = Nested(ContributionSchema)
    event = Nested(PaperEventSchema)
    revisions = List(Nested(PaperRevisionSchema))
    last_revision = Nested(PaperRevisionSchema)
    state = Nested(PaperRevisionStateSchema)
    can_manage = Function(lambda paper, ctx: paper.cfp.is_manager(ctx.get('user')))
    can_judge = Function(lambda paper, ctx: paper.can_judge(ctx.get('user')))
    can_comment = Function(lambda paper, ctx: paper.can_comment(ctx.get('user'), check_state=True))
    can_review = Function(lambda paper, ctx: paper.can_review(ctx.get('user')))
    can_submit_proceedings = Function(lambda paper, ctx: paper.contribution.can_submit_proceedings(ctx.get('user')))
    editing_open = Function(
        lambda paper, ctx: editable_type_settings[EditableType.paper].get(paper.event, 'submission_enabled')
    )
    editing_enabled = Function(
        lambda paper, ctx: paper.event.has_feature('editing')
        and 'paper' in editing_settings.get(paper.event, 'editable_types')
    )


paper_schema = PaperSchema()
paper_review_schema = PaperReviewSchema()
paper_review_comment_schema = PaperReviewCommentSchema()
