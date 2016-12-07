# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import request, render_template, flash

from indico.modules.events.papers.controllers.base import RHManagePapersBase
from indico.modules.events.papers.forms import PaperTeamsForm
from indico.modules.events.papers.operations import set_reviewing_state, update_team_members
from indico.modules.events.papers.views import WPManagePapers
from indico.util.i18n import _
from indico.web.util import jsonify_data, jsonify_form


def _render_paper_dashboard(event, view_class=None):
    if view_class:
        return view_class.render_template('management/overview.html', event.as_legacy, event=event)
    else:
        return render_template('events/papers/management/overview.html', event=event)


class RHPapersDashboard(RHManagePapersBase):
    """Dashboard of the papers module"""

    # Allow access even if the feature is disabled
    EVENT_FEATURE = None

    def _process(self):
        if not self.event_new.has_feature('papers'):
            return WPManagePapers.render_template('management/disabled.html', self._conf, event=self.event_new)
        else:
            return _render_paper_dashboard(self.event_new, view_class=WPManagePapers)


class RHManagePaperTeams(RHManagePapersBase):
    """Modify managers of the papers module"""

    def _process(self):
        cfp = self.event_new.cfp
        form_data = {
            'managers': cfp.managers,
            'judges': cfp.judges,
            'content_reviewers': cfp.content_reviewers,
            'layout_reviewers': cfp.layout_reviewers
        }

        form = PaperTeamsForm(event=self.event_new, **form_data)
        if form.validate_on_submit():
            teams = {
                'managers': form.managers.data,
                'judges': form.judges.data
            }
            if cfp.content_reviewing_enabled:
                teams['content_reviewers'] = form.content_reviewers.data
            if cfp.layout_reviewing_enabled:
                teams['layout_reviewers'] = form.layout_reviewers.data
            update_team_members(self.event_new, **teams)
            flash(_("The members of the teams were updated successfully"), 'success')
            return jsonify_data()
        return jsonify_form(form)


class RHSwitchReviewingType(RHManagePapersBase):
    """Enable/disable the paper reviewing types"""

    def _process_PUT(self):
        set_reviewing_state(self.event_new, request.view_args['reviewing_type'], True)
        return jsonify_data(flash=False, html=_render_paper_dashboard(self.event_new))

    def _process_DELETE(self):
        set_reviewing_state(self.event_new, request.view_args['reviewing_type'], False)
        return jsonify_data(flash=False, html=_render_paper_dashboard(self.event_new))
