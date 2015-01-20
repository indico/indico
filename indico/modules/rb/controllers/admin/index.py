## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

from flask import flash

from indico.core.config import Config
from indico.modules.rb import settings
from indico.modules.rb.forms.settings import SettingsForm
from indico.modules.rb.views.admin.index import WPRoomBookingPluginAdmin
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from MaKaC.webinterface.rh.admins import RHAdminBase


class RHRoomBookingPluginAdmin(RHAdminBase):
    def _process(self):
        defaults = FormDefaults(**settings.get_all())
        form = SettingsForm(obj=defaults)
        if form.validate_on_submit():
            settings.set_multi(form.data)
            flash(_(u'Settings saved'), 'success')
            self._redirect(url_for('rooms_admin.roomBookingPluginAdmin'))
            return
        rb_active = Config.getInstance().getIsRoomBookingActive()
        return WPRoomBookingPluginAdmin(self, rb_active=rb_active, form=form).display()
