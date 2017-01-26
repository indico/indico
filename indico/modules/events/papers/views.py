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

from flask import session, render_template

from indico.modules.events.papers.forms import PaperCommentForm, build_review_form
from indico.util.mathjax import MathjaxMixin
from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase


class WPManagePapers(MathjaxMixin, WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/papers/'
    sidemenu_option = 'papers'

    def getJSFiles(self):
        return (WPConferenceModifBase.getJSFiles(self) +
                self._asset_env['markdown_js'].urls() +
                self._asset_env['modules_papers_js'].urls())

    def _getHeadContent(self):
        return WPConferenceModifBase._getHeadContent(self) + MathjaxMixin._getHeadContent(self)


class WPDisplayPapersBase(WPJinjaMixin, WPConferenceDefaultDisplayBase):
    template_prefix = 'events/papers/'

    def getJSFiles(self):
        return (WPConferenceDefaultDisplayBase.getJSFiles(self) +
                self._asset_env['modules_event_management_js'].urls() +
                self._asset_env['modules_reviews_js'].urls() +
                self._asset_env['modules_papers_js'].urls())

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params).encode('utf-8')


class WPDisplayJudgingArea(WPDisplayPapersBase):
    menu_entry_name = 'judging_area'


def render_paper_page(paper, view_class=None):
    comment_form = PaperCommentForm(paper=paper, user=session.user, formdata=None)
    review_form = None
    reviewed_for_groups = list(paper.last_revision.get_reviewed_for_groups(session.user))
    if len(reviewed_for_groups) == 1:
        review_form = build_review_form(paper, reviewed_for_groups[0])
    params = {'paper': paper, 'comment_form': comment_form, 'review_form': review_form}
    if view_class:
        return view_class.render_template('paper.html', paper.event_new.as_legacy, **params)
    else:
        return render_template('events/papers/paper.html', no_javascript=True, **params)
