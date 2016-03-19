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

from uuid import UUID

from flask import flash, redirect, request, render_template, session
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.users.controllers import RHUserBase
from indico.modules.oauth import logger
from indico.modules.oauth.provider import oauth
from indico.modules.oauth.forms import ApplicationForm
from indico.modules.oauth.models.applications import OAuthApplication, SCOPES
from indico.modules.oauth.models.tokens import OAuthToken
from indico.modules.oauth.views import WPOAuthUserProfile, WPOAuthAdmin
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from MaKaC.webinterface.rh.admins import RHAdminBase
from MaKaC.webinterface.rh.base import RH, RHProtected


class RHOAuthAuthorize(RHProtected):
    def _checkParams(self):
        try:
            UUID(hex=request.args['client_id'])
        except ValueError:
            raise NoResultFound
        self.application = OAuthApplication.find_one(client_id=request.args['client_id'])

    @oauth.authorize_handler
    def _process(self, **kwargs):
        if request.method == 'POST':
            if 'confirm' not in request.form:
                return False
            logger.info('User {} authorized {}'.format(session.user, self.application))
            return True
        if self.application.is_trusted:
            logger.info('User {} automatically authorized {}'.format(session.user, self.application))
            return True
        requested_scopes = set(kwargs['scopes'])
        token = self.application.tokens.filter_by(user=session.user).first()
        authorized_scopes = token.scopes if token else set()
        if requested_scopes <= authorized_scopes:
            return True
        new_scopes = requested_scopes - authorized_scopes
        return render_template('oauth/authorize.html', application=self.application,
                               authorized_scopes=filter(None, [SCOPES.get(s) for s in authorized_scopes]),
                               new_scopes=filter(None, [SCOPES.get(s) for s in new_scopes]))


class RHOAuthErrors(RHProtected):
    def _process(self, **kwargs):
        return render_template('oauth/authorize_errors.html', error=request.args['error'])


class RHOAuthToken(RH):
    @oauth.token_handler
    def _process(self, **kwargs):
        return None


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
        form = ApplicationForm(obj=self.application, application=self.application)
        if form.validate_on_submit():
            form.populate_obj(self.application)
            flash(_("Application {} was modified").format(self.application.name), 'success')
            return redirect(url_for('.apps'))
        return WPOAuthAdmin.render_template('app_details.html', application=self.application, form=form)


class RHOAuthAdminApplicationDelete(RHOAuthAdminApplicationBase):
    """Handles OAuth application deletion"""

    CSRF_ENABLED = True

    def _process(self):
        db.session.delete(self.application)
        logger.info("Application {} was deleted.".format(self.application))
        flash(_("Application deleted successfully"), 'success')
        return redirect(url_for('.apps'))


class RHOAuthAdminApplicationNew(RHAdminBase):
    """Handles OAuth application registration"""

    def _process(self):
        form = ApplicationForm(obj=FormDefaults(is_enabled=True))
        if form.validate_on_submit():
            application = OAuthApplication()
            form.populate_obj(application)
            db.session.add(application)
            db.session.flush()
            flash(_("Application {} registered successfully").format(application.name), 'success')
            return redirect(url_for('.app_details', application))
        return WPOAuthAdmin.render_template('app_new.html', form=form)


class RHOAuthAdminApplicationReset(RHOAuthAdminApplicationBase):
    """Resets the client secret of the OAuth application"""

    CSRF_ENABLED = True

    def _process(self):
        self.application.reset_client_secret()
        flash(_("New client secret generated for the application"), 'success')
        return redirect(url_for('.app_details', self.application))


class RHOAuthAdminApplicationRevoke(RHOAuthAdminApplicationBase):
    """Revokes all user tokens associated to the OAuth application"""

    CSRF_ENABLED = True

    def _process(self):
        self.application.tokens.delete()
        logger.info("All user tokens for {} have been revoked.".format(self.application))
        flash(_("All user tokens for this application were revoked successfully"), 'success')
        return redirect(url_for('.app_details', self.application))


class RHOAuthUserProfile(RHUserBase):
    """OAuth overview (user)"""

    def _process(self):
        tokens = self.user.oauth_tokens.all()
        return WPOAuthUserProfile.render_template('user_profile.html', user=self.user, tokens=tokens)


class RHOAuthUserTokenRevoke(RHUserBase):
    """Revokes user token"""

    CSRF_ENABLED = True

    def _checkParams(self):
        RHUserBase._checkParams(self)
        self.token = OAuthToken.get(request.view_args['id'])
        if self.user != self.token.user:
            raise Forbidden("You can only revoke tokens associated with your user")

    def _process(self):
        db.session.delete(self.token)
        logger.info("Token of application {} for user {} was revoked.".format(self.token.application, self.token.user))
        flash(_("Token for {} has been revoked successfully").format(self.token.application.name), 'success')
        return redirect(url_for('.user_profile'))
