# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request, session
from marshmallow_enum import EnumField
from webargs import fields, validate
from werkzeug.exceptions import Forbidden

from indico.modules.events.papers.controllers.base import RHPaperBase
from indico.modules.events.papers.models.comments import PaperReviewComment
from indico.modules.events.papers.models.reviews import (PaperAction, PaperCommentVisibility, PaperReview,
                                                         PaperReviewType, PaperTypeProxy)
from indico.modules.events.papers.models.revisions import PaperRevisionState
from indico.modules.events.papers.operations import (create_comment, create_paper_revision, create_review,
                                                     delete_comment, judge_paper, reset_paper_state, update_comment,
                                                     update_review)
from indico.modules.events.papers.schemas import PaperSchema
from indico.modules.events.papers.util import is_type_reviewing_possible
from indico.util.i18n import _
from indico.util.marshmallow import max_words, not_empty
from indico.web.args import parser, use_kwargs


class RHPaperDetails(RHPaperBase):
    def _process(self):
        return PaperSchema(context={'user': session.user}).jsonify(self.paper)


class RHResetPaperState(RHPaperBase):
    def _check_paper_protection(self):
        if self.paper.state == PaperRevisionState.submitted:
            return False
        # managers and judges can always reset
        return self.paper.event.can_manage(session.user) or self.paper.can_judge(session.user)

    def _process(self):
        if self.paper.state != PaperRevisionState.submitted:
            reset_paper_state(self.paper)
        return '', 204


class RHCreatePaperComment(RHPaperBase):
    def _check_paper_protection(self):
        return self.paper.can_comment(session.user)

    @use_kwargs({
        'comment': fields.String(validate=not_empty),
        'visibility': EnumField(PaperCommentVisibility, missing=None)
    })
    def _process(self, comment, visibility):
        create_comment(self.paper, comment, visibility, session.user)
        return '', 204


class RHCommentActions(RHPaperBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.comment
        }
    }

    def _check_access(self):
        RHPaperBase._check_access(self)
        if not self.comment.can_edit(session.user):
            raise Forbidden

    def _process_args(self):
        RHPaperBase._process_args(self)
        self.comment = (PaperReviewComment.query
                        .filter(PaperReviewComment.id == request.view_args['comment_id'],
                                ~PaperReviewComment.is_deleted)
                        .first_or_404())

    def _process_DELETE(self):
        delete_comment(self.comment)
        return '', 204

    @use_kwargs({
        'comment': fields.String(validate=not_empty),
        'visibility': EnumField(PaperCommentVisibility)
    }, partial=True)
    def _process_PATCH(self, comment=None, visibility=None):
        update_comment(self.comment, comment, visibility)
        return '', 204


class RHJudgePaper(RHPaperBase):
    def _check_paper_protection(self):
        return self.paper.can_judge(session.user, check_state=True)

    @use_kwargs({
        'action': EnumField(PaperAction, required=True),
        'comment': fields.String()
    })
    def _process(self, action, comment):
        judge_paper(self.paper, action, comment, judge=session.user)
        return '', 204


class RHSubmitNewRevision(RHPaperBase):
    ALLOW_LOCKED = True

    def _check_paper_protection(self):
        if not RHPaperBase._check_paper_protection(self):
            return False
        if not self.contribution.can_submit_proceedings(session.user):
            return False
        return self.contribution.paper.state == PaperRevisionState.to_be_corrected

    @use_kwargs({
        'files': fields.List(fields.Field(), location='files', required=True)
    })
    def _process(self, files):
        create_paper_revision(self.paper, session.user, files)
        return '', 204


def _parse_review_args(event, review_type):
    args_schema = {
        'proposed_action': EnumField(PaperAction, required=True),
        'comment': fields.String(missing='')
    }

    for question in event.cfp.get_questions_for_review_type(review_type):
        attrs = {}
        if question.is_required:
            attrs['required'] = True
        else:
            attrs['missing'] = None

        if question.field_type == 'rating':
            field_cls = fields.Integer
        elif question.field_type == 'text':
            validators = []
            if question.field_data['max_length']:
                validators.append(validate.Length(max=question.field_data['max_length']))
            if question.field_data['max_words']:
                validators.append(max_words(question.field_data['max_words']))

            attrs['validate'] = validators
            field_cls = fields.String
        elif question.field_type == 'bool':
            field_cls = fields.Bool
        else:
            raise Exception('Invalid question field type: {}'.format(question.field_type))
        args_schema['question_{}'.format(question.id)] = field_cls(**attrs)

    data = parser.parse(args_schema)
    questions_data = {k: v for k, v in data.iteritems() if k.startswith('question_')}
    review_data = {k: v for k, v in data.iteritems() if not k.startswith('question_')}
    return questions_data, review_data


class RHCreateReview(RHPaperBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.paper,
            lambda self: self.type
        }
    }

    def _check_access(self):
        RHPaperBase._check_access(self)

        if not is_type_reviewing_possible(self.event.cfp, self.type.instance):
            raise Forbidden(_('Reviewing is currently not possible'))

    def _check_paper_protection(self):
        if self.paper.last_revision.get_reviews(user=session.user, group=self.type.instance):
            return False
        return self.paper.can_review(session.user, check_state=True)

    def _process_args(self):
        RHPaperBase._process_args(self)
        self.type = PaperTypeProxy(PaperReviewType[request.view_args['review_type']])

    def _process(self):
        questions_data, review_data = _parse_review_args(self.event, self.type)
        create_review(self.paper, self.type, session.user, review_data, questions_data)
        return '', 204


class RHUpdateReview(RHPaperBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.review
        }
    }

    def _check_paper_protection(self):
        return self.review.can_edit(session.user, check_state=True)

    def _check_access(self):
        RHPaperBase._check_access(self)

        if not is_type_reviewing_possible(self.event.cfp, self.review.type):
            raise Forbidden(_('Reviewing is currently not possible'))

    def _process_args(self):
        RHPaperBase._process_args(self)
        self.review = (PaperReview.query
                       .filter(PaperReview.id == request.view_args['review_id'])
                       .first_or_404())

    def _process(self):
        questions_data, review_data = _parse_review_args(self.event, self.review.type)
        update_review(self.review, review_data, questions_data)
        return '', 204
