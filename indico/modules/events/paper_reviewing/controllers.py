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

import mimetypes

from flask import flash, redirect, request, session
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.events.paper_reviewing.models.papers import PaperFile
from indico.modules.events.contributions.controllers.management import RHManageContributionBase
from indico.modules.events.contributions.controllers.display import RHContributionDisplayBase
from indico.util.i18n import ngettext, _
from indico.util.fs import secure_filename
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.util import jsonify_data

from MaKaC.webinterface.rh.contribMod import RCContributionPaperReviewingStaff


def _render_paper_file_list(contrib):
    tpl = get_template_module('events/contributions/display/_paper_reviewing.html')
    return tpl.render_paper_files(contrib.paper_files.filter_by(revision_id=None).all())


class RHManagePapersBase(RHManageContributionBase):
    """Base class for all paper management RHs."""


class RHPaperSubmissionBase(RHManageContributionBase):
    def _checkProtection(self):
        if self.contrib.can_manage(session.user, 'submit'):
            return
        else:
            RHManageContributionBase._checkProtection(self)


class RHUploadPaperFiles(RHPaperSubmissionBase):
    """Upload paper file."""

    def _process(self):
        files = request.files.getlist('file')
        for f in files:
            filename = secure_filename(f.filename, 'paper')
            content_type = mimetypes.guess_type(f.filename)[0] or f.mimetype or 'application/octet-stream'
            paper_file = PaperFile(filename=filename, content_type=content_type, contribution=self.contrib)
            paper_file.save(f.file)
            db.session.flush()
            # TODO: logger logger.info('Paper file %s uploaded by %s', paper_file, session.user)
            # TODO: add signal
        flash(ngettext("The paper file has been uploaded", "{count} paper files have been uploaded", len(files))
              .format(count=len(files)), 'success')
        return jsonify_data(html=_render_paper_file_list(self.contrib))


class RHSubmitPaper(RHPaperSubmissionBase):
    """Upload paper file."""

    # TODO: allow submitters too (already the case?)

    def _process(self):
        # TODO: check status before allowing submit
        if not self.contrib.paper_files.count():
            flash(_('You need to submit at least one file'), 'error')
        else:
            self._conf.getReviewManager(self.contrib).getLastReview().setAuthorSubmitted(True)
            flash(_('The paper has been submitted!'), 'success')
        return redirect(url_for('contributions.display_contribution', self.contrib))


class RHManagePaperFileBase(RHPaperSubmissionBase):

    normalize_url_spec = {
        'locators': {
            lambda self: self.paper_file
        }
    }

    def _checkParams(self, params):
        RHPaperSubmissionBase._checkParams(self, params)
        self.paper_file = PaperFile.get_one(request.view_args['paper_file_id'])


class RHRemovePaperFile(RHManagePaperFileBase):
    """Remove paper file."""

    def _process(self):
        db.session.delete(self.paper_file)
        return jsonify_data(html=_render_paper_file_list(self.contrib))


class RHDownloadPaperFile(RHContributionDisplayBase):
    """Download paper file."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.paper_file
        }
    }

    def _checkProtection(self):
        has_pr_rights = RCContributionPaperReviewingStaff.hasRights(self)
        if not self.contrib.can_manage(session.user, 'submit') and not has_pr_rights:
            raise Forbidden

    def _checkParams(self, params):
        RHContributionDisplayBase._checkParams(self, params)
        self.paper_file = PaperFile.get_one(request.view_args['paper_file_id'])

    def _process(self):
        return self.paper_file.send()
