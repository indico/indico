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
from indico.modules.events.papers.forms import PaperSubmissionForm, PaperCommentForm
from indico.modules.events.papers.models.files import PaperFile
from indico.modules.events.papers.operations import create_paper_revision
from indico.modules.events.papers.views import WPDisplayPapersBase
from indico.web.util import jsonify_form, jsonify_data


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
