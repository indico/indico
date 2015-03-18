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

from flask import flash, redirect

from indico.modules.api import settings as api_settings
from indico.modules.api.forms import AdminSettingsForm
from indico.modules.api.models.keys import APIKey
from indico.modules.api.views import WPAPIAdmin, WPAPIUserProfile
from indico.modules.users.controllers import RHUserBase
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults

from MaKaC.webinterface.rh.admins import RHAdminBase


class RHAPIAdminSettings(RHAdminBase):
    """API settings (admin)"""

    def _process(self):
        form = AdminSettingsForm(obj=FormDefaults(**api_settings.get_all()))
        if form.validate_on_submit():
            api_settings.set_multi(form.data)
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.admin_settings'))
        count = APIKey.find(is_active=True).count()
        return WPAPIAdmin.render_template('admin_settings.html', form=form, count=count)


class RHAPIAdminKeys(RHAdminBase):
    """API key list (admin)"""

    def _process(self):
        keys = sorted(APIKey.find_all(is_active=True), key=lambda ak: (ak.use_count == 0, ak.user.getFullName()))
        return WPAPIAdmin.render_template('admin_keys.html', keys=keys)


class RHAPIUserProfile(RHUserBase):
    """API key details (user)"""

    def _process(self):
        return WPAPIUserProfile.render_template('user_profile.html', user=self.user)
