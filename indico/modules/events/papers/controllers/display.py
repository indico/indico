# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, request, session
from werkzeug.exceptions import Forbidden

from indico.modules.events.papers.controllers.base import RHPaperBase, RHPapersBase
from indico.modules.events.papers.forms import (PaperCommentForm, PaperJudgmentForm, PaperSubmissionForm,
                                                build_review_form)
from indico.modules.events.papers.models.comments import PaperReviewComment
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.papers import Paper
from indico.modules.events.papers.models.reviews import PaperReview, PaperReviewType, PaperTypeProxy
from indico.modules.events.papers.models.revisions import PaperRevisionState
from indico.modules.events.papers.operations import (create_comment, create_paper_revision, create_review,
                                                     delete_comment, judge_paper, reset_paper_state, update_comment,
                                                     update_review)
from indico.modules.events.papers.util import (get_contributions_with_paper_submitted_by_user,
                                               get_user_contributions_to_review, get_user_reviewed_contributions,
                                               get_user_submittable_contributions)
from indico.modules.events.papers.views import WPDisplayCallForPapers, WPDisplayReviewingArea, render_paper_page
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.util import _pop_injected_js, jsonify, jsonify_data, jsonify_form, jsonify_template


class RHSubmitPaper(RHPaperBase):
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

    def _process(self):
        form = PaperSubmissionForm()
        if form.validate_on_submit():
            if self.paper is None:
                paper = Paper(self.contribution)
                create_paper_revision(paper, session.user, form.files.data)
                return jsonify_data(flash=False)
            else:
                create_paper_revision(self.paper, session.user, form.files.data)
                return jsonify_data(flash=False, html=render_paper_page(self.paper))
        return jsonify_form(form, form_header_kwargs={'action': request.relative_url}, disable_if_locked=False)


class RHPaperTimeline(RHPaperBase):
    def _process(self):
        return render_paper_page(self.paper, view_class=WPDisplayCallForPapers)

    def _check_paper_protection(self):
        return (self.contribution.is_user_associated(session.user, check_abstract=True) or
                self.event.cfp.is_manager(session.user) or
                self.paper.can_review(session.user) or
                self.paper.can_judge(session.user))


class RHDownloadPaperFile(RHPaperBase):
    """Download a paper file"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.file
        }
    }

    def _process_args(self):
        RHPaperBase._process_args(self)
        self.file = PaperFile.get_one(request.view_args['file_id'])

    def _process(self):
        return self.file.send()


class RHSubmitPaperReview(RHPaperBase):
    """Review an paper in a specific reviewing type"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.paper,
            lambda self: self.type
        }
    }

    def _check_paper_protection(self):
        if self.paper.last_revision.get_reviews(user=session.user, group=self.type.instance):
            return False
        return self.paper.can_review(session.user, check_state=True)

    def _process_args(self):
        RHPaperBase._process_args(self)
        self.type = PaperTypeProxy(PaperReviewType[request.view_args['review_type']])

    def _process(self):
        form = build_review_form(self.paper.last_revision, self.type)
        if form.validate_on_submit():
            create_review(self.paper, self.type, session.user, **form.split_data)
            return jsonify_data(flash=False, html=render_paper_page(self.paper))
        tpl = get_template_module('events/reviews/forms.html')
        return jsonify(html=tpl.render_review_form(form, proposal=self.paper, group=self.type), js=_pop_injected_js())


class RHEditPaperReview(RHPaperBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.review
        }
    }

    def _check_paper_protection(self):
        return self.review.can_edit(session.user, check_state=True)

    def _process_args(self):
        RHPaperBase._process_args(self)
        self.review = PaperReview.get_one(request.view_args['review_id'])

    def _process(self):
        form = build_review_form(review=self.review)
        if form.validate_on_submit():
            update_review(self.review, **form.split_data)
            return jsonify_data(flash=False, html=render_paper_page(self.paper))
        tpl = get_template_module('events/reviews/forms.html')
        return jsonify(html=tpl.render_review_form(form, review=self.review), js=_pop_injected_js())


class RHSubmitPaperComment(RHPaperBase):
    def _check_paper_protection(self):
        return self.paper.can_comment(session.user)

    def _process(self):
        form = PaperCommentForm(paper=self.paper, user=session.user)
        if form.validate_on_submit():
            visibility = form.visibility.data if form.visibility else None
            create_comment(self.paper, form.text.data, visibility, session.user)
            return jsonify_data(flash=False, html=render_paper_page(self.paper))
        tpl = get_template_module('events/reviews/forms.html')
        return jsonify(html=tpl.render_comment_form(form, proposal=self.paper))


class RHPaperCommentBase(RHPaperBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.comment
        }
    }

    def _process_args(self):
        RHPaperBase._process_args(self)
        self.comment = PaperReviewComment.get_one(request.view_args['comment_id'], is_deleted=False)

    def _check_access(self):
        RHPaperBase._check_access(self)
        if not self.comment.can_edit(session.user):
            raise Forbidden


class RHEditPaperComment(RHPaperCommentBase):
    def _process(self):
        form = PaperCommentForm(obj=self.comment, paper=self.paper, user=session.user,
                                prefix='edit-comment-{}-'.format(self.comment.id))
        if form.validate_on_submit():
            visibility = form.visibility.data if form.visibility else self.comment.visibility
            update_comment(self.comment, form.text.data, visibility)
            return jsonify_data(flash=False, html=render_paper_page(self.paper))
        tpl = get_template_module('events/reviews/forms.html')
        return jsonify(html=tpl.render_comment_form(form, proposal=self.paper, comment=self.comment, edit=True))


class RHDeletePaperComment(RHPaperCommentBase):
    def _process(self):
        delete_comment(self.comment)
        return jsonify_data(flash=False)


class RHReviewingArea(RHPapersBase):
    def _check_access(self):
        if not session.user:
            raise Forbidden
        if not self.event.cfp.can_access_reviewing_area(session.user):
            raise Forbidden
        RHPapersBase._check_access(self)

    def _process(self):
        contribs_to_review = get_user_contributions_to_review(self.event, session.user)
        reviewed_contribs = get_user_reviewed_contributions(self.event, session.user)
        return WPDisplayReviewingArea.render_template('display/reviewing_area.html', self.event,
                                                      contribs_to_review=contribs_to_review,
                                                      reviewed_contribs=reviewed_contribs)


class RHJudgePaper(RHPaperBase):
    def _check_paper_protection(self):
        return self.paper.can_judge(session.user, check_state=True)

    def _process(self):
        form = PaperJudgmentForm(paper=self.paper)
        if form.validate_on_submit():
            judge_paper(self.paper, form.judgment.data, form.judgment_comment.data, judge=session.user)
            return jsonify_data(flash=False, html=render_paper_page(self.paper))


class RHResetPaperState(RHPaperBase):
    def _check_paper_protection(self):
        if self.paper.state == PaperRevisionState.submitted:
            return False
        # managers and judges can always reset
        if self.paper.event.can_manage(session.user) or self.paper.can_judge(session.user):
            return True

    def _process(self):
        if self.paper.state != PaperRevisionState.submitted:
            reset_paper_state(self.paper)
            flash(_("The paper judgment has been reset"), 'success')
        return jsonify_data(html=render_paper_page(self.paper))


class RHCallForPapers(RHPapersBase):
    """Show the main CFP page"""

    def _check_access(self):
        if not session.user:
            raise Forbidden
        RHPapersBase._check_access(self)

    def _process_args(self):
        RHPapersBase._process_args(self)
        if not session.user:
            # _check_access aborts in this case, but the functions below fail with a None user
            return
        self.papers = set(get_contributions_with_paper_submitted_by_user(self.event, session.user))
        contribs = set(get_user_submittable_contributions(self.event, session.user))
        self.contribs = contribs - self.papers

    def _process(self):
        return WPDisplayCallForPapers.render_template('display/call_for_papers.html', self.event,
                                                      contributions=self.contribs, papers=self.papers)


class RHSelectContribution(RHCallForPapers):
    """Select a contribution for which the user wants to submit a paper"""

    def _process(self):
        return jsonify_template('events/papers/display/select_contribution.html', contributions=self.contribs)
