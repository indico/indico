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

from indico.modules.events.util import ZipGeneratorMixin
from indico.util.fs import secure_filename


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
