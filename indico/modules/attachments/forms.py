# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from wtforms.fields import SelectField, BooleanField

from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget
from indico.util.i18n import _


class UploadFilesForm(IndicoForm):
    protected = BooleanField(_('Protected'), widget=SwitchWidget(),
                             description=_('By default, the files will inherit the protection of the parent. Checking '
                                           'this field will restrict all access. The protection can be modified later '
                                           'on from the file settings.'))
    folder = SelectField(_('Folder'), choices=[(None, ''), ('lorem', 'ipsum')],
                         description=_('Adding files to folders allow grouping and easier permission management.'))
