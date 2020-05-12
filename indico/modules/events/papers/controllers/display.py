# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request, session
from werkzeug.exceptions import Forbidden

from indico.modules.events.papers.controllers.base import RHPaperBase, RHPapersBase
from indico.modules.events.papers.forms import PaperSubmissionForm
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.models.papers import Paper
from indico.modules.events.papers.operations import create_paper_revision
from indico.modules.events.papers.util import (get_contributions_with_paper_submitted_by_user,
                                               get_user_contributions_to_review, get_user_reviewed_contributions,
                                               get_user_submittable_contributions)
from indico.modules.events.papers.views import (WPDisplayCallForPapers, WPDisplayCallForPapersReact,
                                                WPDisplayReviewingArea)
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHSubmitPaper(RHPaperBase):
    PAPER_REQUIRED = False
    ALLOW_LOCKED = True

    def _check_paper_protection(self):
        if not self.event.cfp.is_manager(session.user):
            if not RHPaperBase._check_paper_protection(self):
                return False
            if not self.contribution.can_submit_proceedings(session.user):
                return False
        # this RH is only used for initial submission
        return self.paper is None

    def _process(self):
        form = PaperSubmissionForm()
        if form.validate_on_submit():
            paper = Paper(self.contribution)
            create_paper_revision(paper, session.user, form.files.data)
            return jsonify_data(flash=False)
        return jsonify_form(form, form_header_kwargs={'action': request.relative_url}, disable_if_locked=False)


class RHPaperTimeline(RHPaperBase):
    def _check_paper_protection(self):
        return (self.contribution.is_user_associated(session.user, check_abstract=True) or
                self.contribution.can_submit_proceedings(session.user) or
                self.event.cfp.is_manager(session.user) or
                self.paper.can_review(session.user) or
                self.paper.can_judge(session.user))

    def _process(self):
        return WPDisplayCallForPapersReact.render_template('paper.html', self.paper.event, paper=self.paper)


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
