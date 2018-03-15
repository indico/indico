# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import render_template, session

from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.papers.forms import (PaperCommentForm, PaperJudgmentForm, PaperSubmissionForm,
                                                build_review_form)
from indico.modules.events.views import WPConferenceDisplayBase
from indico.util.mathjax import MathjaxMixin


class WPManagePapers(MathjaxMixin, WPEventManagement):
    template_prefix = 'events/papers/'
    sidemenu_option = 'papers'
    bundles = WPEventManagement.bundles + ('markdown.js', 'module_events.papers.js')

    def _getHeadContent(self):
        return WPEventManagement._getHeadContent(self) + MathjaxMixin._getHeadContent(self)


class WPDisplayPapersBase(WPConferenceDisplayBase):
    template_prefix = 'events/papers/'
    bundles = WPEventManagement.bundles + ('markdown.js', 'module_events.management.js',
                                           'module_events.papers.js')


class WPDisplayJudgingArea(WPDisplayPapersBase):
    menu_entry_name = 'paper_judging_area'


def render_paper_page(paper, view_class=None):
    comment_form = (PaperCommentForm(paper=paper, user=session.user, formdata=None)
                    if not paper.is_in_final_state else None)
    review_form = None
    reviewed_for_groups = list(paper.last_revision.get_reviewed_for_groups(session.user))
    if len(reviewed_for_groups) == 1:
        review_form = build_review_form(paper.last_revision, reviewed_for_groups[0])
    judgment_form = PaperJudgmentForm(formdata=None, paper=paper)
    revision_form = PaperSubmissionForm(formdata=None)
    params = {
        'paper': paper,
        'comment_form': comment_form,
        'review_form': review_form,
        'judgment_form': judgment_form,
        'revision_form': revision_form
    }
    if view_class:
        return view_class.render_template('paper.html', paper.event, **params)
    else:
        return render_template('events/papers/paper.html', no_javascript=True, standalone=True, **params)


class WPDisplayReviewingArea(WPDisplayPapersBase):
    menu_entry_name = 'paper_reviewing_area'


class WPDisplayCallForPapers(WPDisplayPapersBase):
    menu_entry_name = 'call_for_papers'
