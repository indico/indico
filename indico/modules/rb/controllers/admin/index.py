# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import flash, redirect

from indico.modules.admin import RHAdminBase
from indico.modules.admin.views import WPAdmin
from indico.modules.rb import rb_settings
from indico.modules.rb.forms.settings import SettingsForm
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHRoomBookingSettings(RHAdminBase):
    def _process(self):
        defaults = FormDefaults(**rb_settings.get_all())
        form = SettingsForm(obj=defaults)
        if form.validate_on_submit():
            rb_settings.set_multi(form.data)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.settings'))

        return WPAdmin.render_template('rb/settings.html', 'rb-settings', form=form)
