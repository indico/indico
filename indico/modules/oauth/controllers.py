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

from flask import redirect, flash

from indico.core.index import Catalog

from indico.core.db import db
from indico.modules.users.controllers import RHUserBase
from indico.modules.oauth.forms import ApplicationForm
from indico.modules.oauth.models.clients import OAuthClient
from indico.modules.oauth.views import WPOAuthUserProfile, WPOAuthAdmin
from indico.util.i18n import _
from indico.web.flask.util import url_for
from MaKaC.webinterface.rh.admins import RHAdminBase


class RHOAuthAdmin(RHAdminBase):
    """OAuth server administration settings"""

    def _process(self):
        clients = OAuthClient.find_all()
        return WPOAuthAdmin.render_template('admin.html', clients=clients)


class RHOAuthAdminRegisterApplication(RHAdminBase):
    """Handles OAuth application registration"""

    def _process(self):
        form = ApplicationForm()
        if form.validate_on_submit():
            client = OAuthClient.create(name=form.name.data, description=form.description.data)
            db.session.add(client)
            flash(_("Application {} registered successfully").format(client.name), 'success')
            return redirect(url_for('.admin'))
        return WPOAuthAdmin.render_template('admin_register.html', form=form, back_url=url_for('.admin'))


class RHOAuthUserProfile(RHUserBase):
    """OAuth overview (user)"""

    def _process(self):
        tokens = Catalog.getIdx('user_oauth_access_token').get(str(self.user.id), [])
        return WPOAuthUserProfile.render_template('user_profile.html', user=self.user, tokens=tokens)
