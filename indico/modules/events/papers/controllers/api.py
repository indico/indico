# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import jsonify, request, session
from marshmallow_enum import EnumField
from webargs import fields
from werkzeug.exceptions import Forbidden

from indico.modules.events.papers.controllers.base import RHPaperBase
from indico.modules.events.papers.models.comments import PaperReviewComment
from indico.modules.events.papers.models.reviews import PaperAction, PaperCommentVisibility
from indico.modules.events.papers.models.revisions import PaperRevisionState
from indico.modules.events.papers.operations import (create_comment, create_paper_revision, delete_comment, judge_paper,
                                                     reset_paper_state)
from indico.modules.events.papers.schemas import PaperSchema, paper_schema
from indico.web.args import use_kwargs


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


class RHSubmitPaperComment(RHPaperBase):
    def _check_paper_protection(self):
        return self.paper.can_comment(session.user)

    @use_kwargs({
        'comment': fields.String(required=True),
        'visibility': EnumField(PaperCommentVisibility, required=True)
    })
    def _process(self, comment, visibility):
        create_comment(self.paper, comment, visibility, session.user)
        return '', 204


class RHDeleteComment(RHPaperBase):
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
        self.comment = PaperReviewComment.get_one(request.view_args['comment_id'], is_deleted=False)

    def _process_DELETE(self):
        delete_comment(self.comment)
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
    PAPER_REQUIRED = False
    ALLOW_LOCKED = True

    def _check_paper_protection(self):
        if not self.event.cfp.is_manager(session.user):
            if not RHPaperBase._check_paper_protection(self):
                return False
            if not self.contribution.is_user_associated(session.user, check_abstract=True):
                return False
        paper = self.contribution.paper
        return paper is None or paper.state == PaperRevisionState.to_be_corrected

    @use_kwargs({
        'files': fields.List(fields.Field(), location='files', required=True)
    })
    def _process(self, files):
        create_paper_revision(self.paper, session.user, files)
        return '', 204
