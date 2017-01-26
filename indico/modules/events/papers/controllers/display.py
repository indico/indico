# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from flask import request, session

from indico.modules.events.papers.controllers.base import RHPaperBase
from indico.modules.events.papers.forms import PaperSubmissionForm, PaperCommentForm, build_review_form
from indico.modules.events.papers.models.comments import PaperReviewComment
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.reviews import PaperReviewType, PaperTypeProxy
from indico.modules.events.papers.operations import (create_paper_revision, create_review, create_comment,
                                                     update_comment, delete_comment)
from indico.modules.events.papers.views import WPDisplayPapersBase, render_paper_page
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_form, jsonify_data, jsonify


class RHSubmitPaper(RHPaperBase):
    def _process(self):
        form = PaperSubmissionForm()
        if form.validate_on_submit():
            create_paper_revision(self.contribution, session.user, form.files.data)
            return jsonify_data(flash=False)
        return jsonify_form(form, form_header_kwargs={'action': request.relative_url})


class RHPaperTimeline(RHPaperBase):
    def _process(self):
        comment_form = PaperCommentForm(paper=self.paper, user=session.user, formdata=None)
        return WPDisplayPapersBase.render_template('paper.html', self._conf, paper=self.paper,
                                                   comment_form=comment_form, review_form=None)


class RHDownloadPaperFile(RHPaperBase):
    """Download a paper file"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.file
        }
    }

    def _checkParams(self, params):
        RHPaperBase._checkParams(self, params)
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

    def _checkParams(self, params):
        RHPaperBase._checkParams(self, params)
        self.type = PaperTypeProxy(PaperReviewType[request.view_args['review_type']])

    def _process(self):
        form = build_review_form(self.paper.last_revision, self.type.instance)
        if form.validate_on_submit():
            create_review(self.paper, self.type, session.user, **form.split_data)
            return jsonify_data(flash=False, html=render_paper_page(self.paper))
        tpl = get_template_module('events/reviews/forms.html')
        return jsonify(html=tpl.render_review_form(form, proposal=self.paper, group=self.type))


class RHEditPaperReview(RHPaperBase):
    # TODO
    pass


class RHSubmitPaperComment(RHPaperBase):
    def _check_paper_protection(self):
        return self.paper.can_comment(session.user)

    def _process(self):
        form = PaperCommentForm(paper=self.paper, user=session.user)
        if form.validate_on_submit():
            create_comment(self.paper, form.text.data, form.visibility.data, session.user)
            return jsonify_data(flash=False, html=render_paper_page(self.paper))
        tpl = get_template_module('events/reviews/forms.html')
        return jsonify(html=tpl.render_comment_form(form, proposal=self.paper))


class RHPaperCommentBase(RHPaperBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.comment
        }
    }

    def _checkParams(self, params):
        RHPaperBase._checkParams(self, params)
        self.comment = PaperReviewComment.get_one(request.view_args['comment_id'], is_deleted=False)

    def _checkProtection(self):
        RHPaperBase._checkProtection(self)
        if not self.comment.can_edit(session.user):
            raise Forbidden


class RHEditPaperComment(RHPaperCommentBase):
    def _process(self):
        form = PaperCommentForm(obj=self.comment, paper=self.paper, user=session.user,
                                prefix='edit-comment-{}-'.format(self.comment.id))
        if form.validate_on_submit():
            update_comment(self.comment, form.text.data, form.visibility.data)
            return jsonify_data(flash=False, html=render_paper_page(self.paper))
        tpl = get_template_module('events/reviews/forms.html')
        return jsonify(html=tpl.render_comment_form(form, proposal=self.paper, comment=self.comment))


class RHDeletePaperComment(RHPaperCommentBase):
    def _process(self):
        delete_comment(self.comment)
        return jsonify_data(flash=False)
