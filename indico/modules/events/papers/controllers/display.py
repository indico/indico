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
from indico.modules.events.papers.operations import create_paper_revision
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
