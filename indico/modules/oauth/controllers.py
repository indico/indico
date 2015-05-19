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

from flask import flash, redirect, request

from indico.core.index import Catalog

from indico.core.db import db
from indico.modules.users.controllers import RHUserBase
from indico.modules.oauth.forms import ApplicationForm
from indico.modules.oauth.models.applications import OAuthApplication
from indico.modules.oauth.views import WPOAuthUserProfile, WPOAuthAdmin
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from MaKaC.webinterface.rh.admins import RHAdminBase


class RHOAuthAdmin(RHAdminBase):
    """OAuth server administration settings"""

    def _process(self):
        applications = OAuthApplication.find().order_by(db.func.lower(OAuthApplication.name)).all()
        return WPOAuthAdmin.render_template('apps.html', applications=applications)


class RHOAuthAdminApplication(RHAdminBase):
    """Handles application details page"""

    def _checkParams(self):
        self.application = OAuthApplication.get(request.view_args['id'])

    def _process(self):
        defaults = FormDefaults(name=self.application.name, description=self.application.description,
                                redirect_uris=self.application.redirect_uris)
        form = ApplicationForm(obj=defaults, application=self.application)
        if form.validate_on_submit():
            self.application.name = form.name.data
            self.application.description = form.description.data
            flash(_("Application {} was modified").format(self.application.name), 'success')
            return redirect(url_for('.apps'))
        return WPOAuthAdmin.render_template('app_details.html', application=self.application, form=form,
                                            back_url=url_for('.apps'))


class RHOAuthAdminApplicationNew(RHAdminBase):
    """Handles OAuth application registration"""

    def _process(self):
        form = ApplicationForm()
        if form.validate_on_submit():
            application = OAuthApplication.create(name=form.name.data, description=form.description.data,
                                                  redirect_uris=form.redirect_uris.data)
            db.session.add(application)
            flash(_("Application {} registered successfully").format(application.name), 'success')
            return redirect(url_for('.apps'))
        return WPOAuthAdmin.render_template('app_new.html', form=form, back_url=url_for('.apps'))


class RHOAuthUserProfile(RHUserBase):
    """OAuth overview (user)"""

    def _process(self):
        tokens = Catalog.getIdx('user_oauth_access_token').get(str(self.user.id), [])
        return WPOAuthUserProfile.render_template('user_profile.html', user=self.user, tokens=tokens)
