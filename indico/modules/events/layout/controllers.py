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

from indico.modules.events.layout import layout_settings
from indico.modules.events.layout.forms import LayoutForm
from indico.modules.events.layout.views import WPLayoutEdit, WPMenuEdit
from indico.web.forms.base import FormDefaults
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHLayoutEdit(RHConferenceModifBase):
    def _process(self):
        defaults = FormDefaults(**layout_settings.get_all(self._conf))
        form = LayoutForm(obj=defaults)
        if form.validate_on_submit():
            pass
        return WPLayoutEdit.render_template('layout.html', self._conf, form=form)


class RHMenuEdit(RHConferenceModifBase):
    def _process(self):
        return WPMenuEdit.render_template('menu_edit.html', self._conf)
