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
from werkzeug.exceptions import Forbidden

from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.papers.controllers.base import RHPapersBase
from indico.modules.events.papers.forms import PaperSubmissionForm
from indico.modules.events.papers.lists import PaperJudgingAreaListGeneratorDisplay
from indico.modules.events.papers.operations import create_paper_revision
from indico.modules.events.papers.views import WPDisplayJudgingArea
from indico.web.util import jsonify_form, jsonify_data


class RHSubmitPaper(RHPapersBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.contribution
        }
    }

    def _checkParams(self, params):
        RHPapersBase._checkParams(self, params)
        self.contribution = Contribution.get_one(request.view_args['contrib_id'], is_deleted=False)

    def _checkProtection(self):
        RHPapersBase._checkProtection(self)
        if not self.contribution.can_manage(session.user, role='submit'):
            raise Forbidden

    def _process(self):
        form = PaperSubmissionForm()
        if form.validate_on_submit():
            create_paper_revision(self.contribution, session.user, form.files.data)
            return jsonify_data(flash=False)
        return jsonify_form(form, form_header_kwargs={'action': request.relative_url})


class RHPaperTimeline(RHPapersBase):
    def _process(self):
        return NotImplementedError


class RHDisplayJudgingArea(RHPapersBase):
    def _checkProtection(self):
        if not session.user:
            raise Forbidden
            RHPapersBase._checkProtection(self)

    def _checkParams(self, params):
        RHPapersBase._checkParams(self, params)
        self.list_generator = PaperJudgingAreaListGeneratorDisplay(event=self.event_new, user=session.user)

    def _process(self):
        return WPDisplayJudgingArea.render_template('display/judging_area.html', self._conf, event=self.event_new,
                                                    **self.list_generator.get_list_kwargs())


class RHDisplayCustomizeJudgingAreaList(RHPapersBase):
    """Display dialog with filters"""

    def _checkParams(self, params):
        RHPapersBase._checkParams(self, params)
        self.list_generator = PaperJudgingAreaListGeneratorDisplay(event=self.event_new, user=session.user)

    def _process_GET(self):
        list_config = self.list_generator.list_config
        return WPDisplayJudgingArea.render_template('management/assignment_list_filter.html', self._conf,
                                                    event=self.event_new,
                                                    static_items=self.list_generator.static_items,
                                                    filters=list_config['filters'],
                                                    visible_items=list_config['items'])

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(flash=False, **self.list_generator.render_list())
