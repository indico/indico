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

from indico.web.flask.wrappers import IndicoBlueprint
from indico.modules.events.paper_reviewing.controllers import (RHDownloadPaperFile, RHRemovePaperFile,
                                                               RHSubmitPaper, RHUploadPaperFiles)

_bp = IndicoBlueprint('paper_reviewing', __name__, template_folder='templates',
                      virtual_template_folder='events/paper_reviewing',
                      url_prefix='/event/<confId>/contributions/<contrib_id>')

_bp.add_url_rule('/paper/files/', 'upload_paper_files', RHUploadPaperFiles, methods=('POST',))
_bp.add_url_rule('/paper/submit/', 'submit_paper', RHSubmitPaper, methods=('POST',))
_bp.add_url_rule('/paper/<paper_file_id>/<filename>', 'remove_paper_file', RHRemovePaperFile, methods=('DELETE',))
_bp.add_url_rule('/paper/<paper_file_id>/<filename>', 'download_paper_file', RHDownloadPaperFile)
