# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from authlib.oauth2.base import OAuth2Error
from authlib.oauth2.rfc6749 import scope_to_list
from authlib.oauth2.rfc8414 import AuthorizationServerMetadata
from flask import flash, jsonify, redirect, render_template, request, session
from sqlalchemy.orm import contains_eager
from werkzeug.exceptions import Forbidden

from indico.core.config import config
from indico.core.db import db
from indico.core.oauth.endpoints import IndicoIntrospectionEndpoint, IndicoRevocationEndpoint
from indico.core.oauth.grants import IndicoAuthorizationCodeGrant, IndicoCodeChallenge
from indico.core.oauth.logger import logger
from indico.core.oauth.models.applications import OAuthApplication, OAuthApplicationUserLink
from indico.core.oauth.models.personal_tokens import PersonalToken
from indico.core.oauth.models.tokens import OAuthToken
from indico.core.oauth.oauth2 import auth_server
from indico.core.oauth.scopes import SCOPES
from indico.modules.admin import RHAdminBase
from indico.modules.oauth.forms import ApplicationForm, PersonalTokenForm
from indico.modules.oauth.util import can_manage_personal_tokens
from indico.modules.oauth.views import WPOAuthAdmin, WPOAuthUserProfile
from indico.modules.users.controllers import RHUserBase
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.rh import RH, RHProtected
from indico.web.util import jsonify_data, jsonify_form


class RHOAuthMetadata(RH):
    """Return RFC8414 Authorization Server Metadata."""

    def _process(self):
        metadata = AuthorizationServerMetadata(
            authorization_endpoint=url_for('.oauth_authorize', _external=True),
            token_endpoint=url_for('.oauth_token', _external=True),
            introspection_endpoint=url_for('.oauth_introspect', _external=True),
            revocation_endpoint=url_for('.oauth_revoke', _external=True),
            issuer=config.BASE_URL,
            response_types_supported=['code'],
            response_modes_supported=['query'],
            grant_types_supported=['authorization_code'],
            scopes_supported=list(SCOPES),
            token_endpoint_auth_methods_supported=list(IndicoAuthorizationCodeGrant.TOKEN_ENDPOINT_AUTH_METHODS),
            introspection_endpoint_auth_methods_supported=list(IndicoIntrospectionEndpoint.CLIENT_AUTH_METHODS),
            revocation_endpoint_auth_methods_supported=list(IndicoRevocationEndpoint.CLIENT_AUTH_METHODS),
            code_challenge_methods_supported=list(IndicoCodeChallenge.SUPPORTED_CODE_CHALLENGE_METHOD),
        )
        metadata.validate()
        return jsonify(metadata)


class RHOAuthAuthorize(RHProtected):
    CSRF_ENABLED = False

    def _process(self):
        rv = self._process_consent()
        if rv is True:
            return auth_server.create_authorization_response(grant_user=session.user)
        elif rv is False:
            return auth_server.create_authorization_response(grant_user=None)
        else:
            return rv

    def _process_consent(self):
        try:
            grant = auth_server.get_consent_grant(end_user=session.user)
        except OAuth2Error as error:
            return render_template('oauth/authorize_errors.html', error=error.error)

        application = grant.client

        if request.method == 'POST':
            if 'confirm' not in request.form:
                return False
            logger.info('User %s authorized %s', session.user, application)
            return True
        elif application.is_trusted:
            logger.info('User %s automatically authorized %s', session.user, application)
            return True

        link = application.user_links.filter_by(user=session.user).first()
        authorized_scopes = set(link.scopes) if link else set()
        requested_scopes = set(scope_to_list(grant.request.scope)) if grant.request.scope else authorized_scopes
        if requested_scopes <= authorized_scopes:
            return True

        new_scopes = requested_scopes - authorized_scopes
        return render_template('oauth/authorize.html', application=application,
                               authorized_scopes=[_f for _f in [SCOPES.get(s) for s in authorized_scopes] if _f],
                               new_scopes=[_f for _f in [SCOPES.get(s) for s in new_scopes] if _f])


class RHOAuthToken(RH):
    CSRF_ENABLED = False

    def _process(self):
        resp = auth_server.create_token_response()
        resp.headers['Access-Control-Allow-Methods'] = 'POST'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


class RHOAuthIntrospect(RH):
    CSRF_ENABLED = False

    def _process(self):
        return auth_server.create_endpoint_response('introspection')


class RHOAuthRevoke(RH):
    CSRF_ENABLED = False

    def _process(self):
        return auth_server.create_endpoint_response('revocation')


class RHOAuthAdmin(RHAdminBase):
    """OAuth server administration settings."""

    def _process(self):
        applications = OAuthApplication.query.order_by(db.func.lower(OAuthApplication.name)).all()
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
            logger.info('Application %s updated by %s', self.application, session.user)
            flash(_('Application {} was modified').format(self.application.name), 'success')
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
        logger.info('Application %s deleted by %s', self.application, session.user)
        flash(_('Application deleted successfully'), 'success')
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
            logger.info('Application %s created by %s', application, session.user)
            flash(_('Application {} registered successfully').format(application.name), 'success')
            return redirect(url_for('.app_details', application))
        return WPOAuthAdmin.render_template('app_new.html', form=form)


class RHOAuthAdminApplicationReset(RHOAuthAdminApplicationBase):
    """Reset the client secret of the OAuth application."""

    def _process(self):
        self.application.reset_client_secret()
        logger.info('Client secret of %s reset by %s', self.application, session.user)
        flash(_('New client secret generated for the application'), 'success')
        return redirect(url_for('.app_details', self.application))


class RHOAuthAdminApplicationRevoke(RHOAuthAdminApplicationBase):
    """Revoke all user tokens associated to the OAuth application."""

    def _process(self):
        self.application.user_links.delete()
        logger.info('Deauthorizing app %r for all users', self.application)
        flash(_('App authorization revoked for all users.'), 'success')
        return redirect(url_for('.app_details', self.application))


class RHOAuthUserApps(RHUserBase):
    """OAuth overview (user)."""

    def _process(self):
        authorizations = (
            db.session.query(OAuthApplicationUserLink, db.func.max(OAuthToken.last_used_dt))
            .with_parent(self.user)
            .join(OAuthToken, OAuthToken.app_user_link_id == OAuthApplicationUserLink.id)
            .join(OAuthApplication)
            .options(contains_eager('application'))
            .group_by(OAuthApplication.id, OAuthApplicationUserLink.id)
            .order_by(OAuthApplication.name)
            .all()
        )
        return WPOAuthUserProfile.render_template('user_apps.html', 'applications', user=self.user,
                                                  authorizations=authorizations)


class RHOAuthUserAppRevoke(RHUserBase):
    """Revoke an oauth application's access to a user."""

    def _process_args(self):
        RHUserBase._process_args(self)
        self.application = OAuthApplication.get_or_404(request.view_args['id'])

    def _process(self):
        link = OAuthApplicationUserLink.query.with_parent(self.user).with_parent(self.application).first()
        if link:
            logger.info('Deauthorizing app %r for user %r (scopes: %r)', self.application, self.user, link.scopes)
            db.session.delete(link)
        flash(_("Access for '{}' has been successfully revoked.").format(self.application.name), 'success')
        return redirect(url_for('.user_apps'))


class RHPersonalTokensUserBase(RHUserBase):
    """Base class for personal token management"""

    allow_system_user = True


class RHPersonalTokens(RHPersonalTokensUserBase):
    """Personal tokens page for a user."""

    def _process(self):
        tokens = self.user.query_personal_tokens().order_by(db.func.lower(PersonalToken.name)).all()
        created_token = session.pop('personal_token_created', None)
        return WPOAuthUserProfile.render_template('user_tokens.html', 'tokens', user=self.user, tokens=tokens,
                                                  created_token=created_token, can_manage=can_manage_personal_tokens())


class RHPersonalTokenBase(RHPersonalTokensUserBase):
    """Base class for actions involving a specific personal token of a user."""

    def _process_args(self):
        RHPersonalTokensUserBase._process_args(self)
        self.token: PersonalToken = (
            PersonalToken.query
            .with_parent(self.user)
            .filter_by(id=request.view_args['id'], revoked_dt=None)
            .first_or_404()
        )


class RHEditPersonalToken(RHPersonalTokenBase):
    """Edit a personal access token of a user."""

    def _check_access(self):
        RHPersonalTokenBase._check_access(self)
        if not can_manage_personal_tokens():
            raise Forbidden(_('You cannot manage API tokens'))

    def _process(self):
        form = PersonalTokenForm(user=self.user, token=self.token, obj=self.token)
        if form.validate_on_submit():
            old_name = self.token.name
            form.populate_obj(self.token)
            logger.info('Updated token %r', self.token)
            flash(_("Token '{}' updated").format(old_name), 'success')
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHCreatePersonalToken(RHPersonalTokensUserBase):
    """Create a personal access token for a user."""

    def _check_access(self):
        RHPersonalTokensUserBase._check_access(self)
        if not can_manage_personal_tokens():
            raise Forbidden(_('You cannot manage API tokens'))

    def _process(self):
        form = PersonalTokenForm(user=self.user)
        if form.validate_on_submit():
            token = PersonalToken(user=self.user)
            form.populate_obj(token)
            access_token = token.generate_token()
            db.session.flush()
            logger.info('Created token %r', token)
            session['personal_token_created'] = (token.id, access_token)
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHRevokePersonalToken(RHPersonalTokenBase):
    """Revoke a personal access token of a user."""

    def _process(self):
        self.token.revoke()
        logger.info('Revoked token %r', self.token)
        flash(_("The token '{}' has been successfully revoked.").format(self.token.name), 'success')
        return redirect(url_for('.user_tokens'))


class RHResetPersonalToken(RHPersonalTokenBase):
    """Reset a personal access token of a user."""

    def _process(self):
        access_token = self.token.generate_token()
        logger.info('Regenerated token %r', self.token)
        session['personal_token_created'] = (self.token.id, access_token)
        return redirect(url_for('.user_tokens'))
