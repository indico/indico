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

from flask import session

from indico.modules.events.papers import logger
from indico.modules.events.papers.controllers.base import RHManagePapersBase
from indico.modules.events.papers.forms import PaperManagersForm
from indico.modules.events.papers.views import WPManagePapers
from indico.modules.events.util import update_object_principals
from indico.web.util import jsonify_data, jsonify_form


class RHPapersDashboard(RHManagePapersBase):
    """Dashboard of the papers module"""

    # Allow access even if the feature is disabled
    EVENT_FEATURE = None

    def _process(self):
        if not self.event_new.has_feature('papers'):
            return WPManagePapers.render_template('management/disabled.html', self._conf, event=self.event_new)
        else:
            return WPManagePapers.render_template('management/overview.html', self._conf, event=self.event_new)


class RHManagePaperTeams(RHManagePapersBase):
    """Modify managers of the papers module"""

    def _process(self):
        managers = {p.principal for p in self.event_new.acl_entries
                    if p.has_management_role('paper_manager', explicit=True)}
        form = PaperManagersForm(managers=managers)
        if form.validate_on_submit():
            update_object_principals(self.event_new, form.managers.data, role='paper_manager')
            logger.info("Paper managers of %r updated by %r", self.event_new, session.user)
            return jsonify_data(flash=False)
        return jsonify_form(form)
