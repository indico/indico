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

from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import JSONField
from indico.web.forms.widgets import DropzoneWidget
from indico.util.i18n import _


class PaperUploadForm(IndicoForm):
    """Form to upload a new paper version."""

    paper_file = JSONField(_("Paper file"),
                           widget=DropzoneWidget(max_files=10, submit_form=False, add_remove_links=True,
                                                 handle_flashes=True))
