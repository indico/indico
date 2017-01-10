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

import os

from flask import flash, request, session

from indico.modules.events.papers.forms import BulkPaperJudgmentForm
from indico.modules.events.papers.models.revisions import PaperRevisionState
from indico.modules.events.papers.operations import judge_paper
from indico.modules.events.util import ZipGeneratorMixin
from indico.util.fs import secure_filename
from indico.util.i18n import ngettext, _
from indico.web.util import jsonify_data, jsonify_form


class DownloadPapersMixin(ZipGeneratorMixin):
    """Generate a ZIP file with paper files for a given list of contributions"""

    def _prepare_folder_structure(self, item):
        paper_title = secure_filename('{}_{}'.format(item.paper.contribution.title,
                                                     unicode(item.paper.contribution.id)), 'paper')
        file_name = secure_filename('{}_{}'.format(unicode(item.id), item.filename), item.filename)
        return os.path.join(*self._adjust_path_length([paper_title, file_name]))

    def _iter_items(self, contributions):
        contributions_with_paper = [c for c in self.contributions if c.paper]
        for contrib in contributions_with_paper:
            for f in contrib.paper.last_revision.files:
                yield f


class PaperJudgmentMixin:
    """Perform bulk judgment operations on selected papers"""

    def _process(self):
        form = BulkPaperJudgmentForm(event=self.event_new, judgment=request.form.get('judgment'),
                                     contribution_id=[c.id for c in self.contributions])
        if form.validate_on_submit():
            judgment_data, contrib_data = form.split_data
            submitted_papers = [c for c in self.contributions if
                                c._paper_last_revision and c._paper_last_revision.state == PaperRevisionState.submitted]
            for submitted_paper in submitted_papers:
                judge_paper(submitted_paper, contrib_data, judge=session.user, **judgment_data)
            num_submitted_papers = len(submitted_papers)
            num_not_submitted_papers = len(self.contributions) - num_submitted_papers
            if num_submitted_papers:
                flash(ngettext("One paper has been judged.",
                               "{num} papers have been judged.",
                               num_submitted_papers).format(num=num_submitted_papers), 'success')
            if num_not_submitted_papers:
                flash(ngettext("One contribution has been skipped since it has no paper submitted yet or it is in "
                               "a final state.",
                               "{num} contributions have been skipped since they have no paper submitted yet or they "
                               "are in a final state.",
                               num_not_submitted_papers).format(num=num_not_submitted_papers), 'warning')
            return jsonify_data(**self.list_generator.render_list())
        return jsonify_form(form=form, submit=_('Judge'), disabled_until_change=False)
