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

from flask import flash, redirect, request, render_template

from indico.core.db import db
from indico.modules.users.controllers import RHUserBase
from indico.modules.oauth.provider import oauth
from indico.modules.oauth.forms import ApplicationForm
from indico.modules.oauth.models.applications import OAuthApplication
from indico.modules.oauth.models.tokens import OAuthToken
from indico.modules.oauth.views import WPOAuthUserProfile, WPOAuthAdmin
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from MaKaC.webinterface.rh.admins import RHAdminBase
from MaKaC.webinterface.rh.base import RHProtected


class RHOAuthAuthorize(RHProtected):
    def _checkParams(self):
        self.application = OAuthApplication.find_one(client_id=request.args['client_id'])

    @oauth.authorize_handler
    def _process(self, **kwargs):
        if request.method == 'POST':
            return 'confirm' in request.form
        if self.application.is_trusted:
            return True
        return render_template('oauth/authorize.html', application=self.application)


class RHOAuthAdmin(RHAdminBase):
    """OAuth server administration settings"""

    def _process(self):
        applications = OAuthApplication.find().order_by(db.func.lower(OAuthApplication.name)).all()
        return WPOAuthAdmin.render_template('apps.html', applications=applications)


class RHOAuthAdminApplicationBase(RHAdminBase):
    """Base class for single OAuth application RHs"""
    def _checkParams(self):
        self.application = OAuthApplication.get(request.view_args['id'])


class RHOAuthAdminApplication(RHOAuthAdminApplicationBase):
    """Handles application details page"""

    def _process(self):
        defaults = FormDefaults(name=self.application.name, description=self.application.description,
                                redirect_uris=self.application.redirect_uris)
        form = ApplicationForm(obj=defaults, application=self.application)
        if form.validate_on_submit():
            form.populate_obj(self.application)
            flash(_("Application {} was modified").format(self.application.name), 'success')
            return redirect(url_for('.apps'))
        return WPOAuthAdmin.render_template('app_details.html', application=self.application, form=form,
                                            back_url=url_for('.apps'))


class RHOAuthAdminApplicationDelete(RHOAuthAdminApplicationBase):
    """Handles OAuth application deletion"""

    def _process(self):
        db.session.delete(self.application)
        flash(_("Application deleted successfully"), 'success')
        return redirect(url_for('.apps'))


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


class RHOAuthAdminApplicationReset(RHOAuthAdminApplicationBase):
    """Resets the client secret of the OAuth application"""

    def _process(self):
        self.application.reset_client_secret()
        flash(_("New client secret generated for the application"), 'success')
        return redirect(url_for('.app_details', self.application))


class RHOAuthAdminApplicationRevoke(RHOAuthAdminApplicationBase):
    """Revokes all user tokens associated to the OAuth application"""

    def _process(self):
        # TODO: revoke tokens when implemented
        flash(_("All user tokens for this application were revoked successfully"), 'success')
        return redirect(url_for('.app_details', self.application))


class RHOAuthUserProfile(RHUserBase):
    """OAuth overview (user)"""

    def _process(self):
        tokens = OAuthToken.find_all()
        return WPOAuthUserProfile.render_template('user_profile.html', user=self.user, tokens=tokens)


class RHOAuthUserTokenRevoke(RHUserBase):
    """Revokes user token"""

    def _process(self):
        # TODO: revoke token when implemented
        flash(_("Your token was revoked successfully"), 'success')
        return redirect(url_for('.user_profile'))
