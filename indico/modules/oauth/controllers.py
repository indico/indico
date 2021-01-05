# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from uuid import UUID

from flask import flash, redirect, render_template, request, session
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.admin import RHAdminBase
from indico.modules.oauth import logger
from indico.modules.oauth.forms import ApplicationForm
from indico.modules.oauth.models.applications import SCOPES, OAuthApplication
from indico.modules.oauth.models.tokens import OAuthToken
from indico.modules.oauth.provider import oauth
from indico.modules.oauth.views import WPOAuthAdmin, WPOAuthUserProfile
from indico.modules.users.controllers import RHUserBase
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.rh import RH, RHProtected


class RHOAuthAuthorize(RHProtected):
    CSRF_ENABLED = False

    def _process_args(self):
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
            logger.info('User %s authorized %s', session.user, self.application)
            return True
        if self.application.is_trusted:
            logger.info('User %s automatically authorized %s', session.user, self.application)
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
    CSRF_ENABLED = False

    @oauth.token_handler
    def _process(self, **kwargs):
        return None


class RHOAuthAdmin(RHAdminBase):
    """OAuth server administration settings."""

    def _process(self):
        applications = OAuthApplication.find().order_by(db.func.lower(OAuthApplication.name)).all()
        return WPOAuthAdmin.render_template('apps.html', applications=applications)


class RHOAuthAdminApplicationBase(RHAdminBase):
    """Base class for single OAuth application RHs."""
    def _process_args(self):
        self.application = OAuthApplication.get_or_404(request.view_args['id'])


class RHOAuthAdminApplication(RHOAuthAdminApplicationBase):
    """Handle application details page."""

    def _process(self):
        form = ApplicationForm(obj=self.application, application=self.application)
        disabled_fields = set(self.application.system_app_type.enforced_data)
        if form.validate_on_submit():
            form.populate_obj(self.application)
            logger.info("Application %s updated by %s", self.application, session.user)
            flash(_("Application {} was modified").format(self.application.name), 'success')
            return redirect(url_for('.apps'))
        return WPOAuthAdmin.render_template('app_details.html', application=self.application, form=form,
                                            disabled_fields=disabled_fields)


class RHOAuthAdminApplicationDelete(RHOAuthAdminApplicationBase):
    """Handle OAuth application deletion."""

    def _check_access(self):
        RHOAuthAdminApplicationBase._check_access(self)
        if self.application.system_app_type:
            raise Forbidden('Cannot delete system app')

    def _process(self):
        db.session.delete(self.application)
        logger.info("Application %s deleted by %s", self.application, session.user)
        flash(_("Application deleted successfully"), 'success')
        return redirect(url_for('.apps'))


class RHOAuthAdminApplicationNew(RHAdminBase):
    """Handle OAuth application registration."""

    def _process(self):
        form = ApplicationForm(obj=FormDefaults(is_enabled=True))
        if form.validate_on_submit():
            application = OAuthApplication()
            form.populate_obj(application)
            db.session.add(application)
            db.session.flush()
            logger.info("Application %s created by %s", application, session.user)
            flash(_("Application {} registered successfully").format(application.name), 'success')
            return redirect(url_for('.app_details', application))
        return WPOAuthAdmin.render_template('app_new.html', form=form)


class RHOAuthAdminApplicationReset(RHOAuthAdminApplicationBase):
    """Reset the client secret of the OAuth application."""

    def _process(self):
        self.application.reset_client_secret()
        logger.info("Client secret of %s reset by %s", self.application, session.user)
        flash(_("New client secret generated for the application"), 'success')
        return redirect(url_for('.app_details', self.application))


class RHOAuthAdminApplicationRevoke(RHOAuthAdminApplicationBase):
    """Revoke all user tokens associated to the OAuth application."""

    def _process(self):
        self.application.tokens.delete()
        logger.info("All user tokens for %s revoked by %s", self.application, session.user)
        flash(_("All user tokens for this application were revoked successfully"), 'success')
        return redirect(url_for('.app_details', self.application))


class RHOAuthUserProfile(RHUserBase):
    """OAuth overview (user)."""

    def _process(self):
        tokens = self.user.oauth_tokens.all()
        return WPOAuthUserProfile.render_template('user_profile.html', 'applications', user=self.user, tokens=tokens)


class RHOAuthUserTokenRevoke(RHUserBase):
    """Revoke user token."""

    def _process_args(self):
        RHUserBase._process_args(self)
        self.token = OAuthToken.get(request.view_args['id'])
        if self.user != self.token.user:
            raise Forbidden("You can only revoke tokens associated with your user")

    def _process(self):
        db.session.delete(self.token)
        logger.info("Token of application %s for user %s was revoked.", self.token.application, self.token.user)
        flash(_("Token for {} has been revoked successfully").format(self.token.application.name), 'success')
        return redirect(url_for('.user_profile'))
