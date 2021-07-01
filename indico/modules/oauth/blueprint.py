# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request

from indico.modules.oauth.controllers import (RHCreatePersonalToken, RHEditPersonalToken, RHOAuthAdmin,
                                              RHOAuthAdminApplication, RHOAuthAdminApplicationDelete,
                                              RHOAuthAdminApplicationNew, RHOAuthAdminApplicationReset,
                                              RHOAuthAdminApplicationRevoke, RHOAuthAuthorize, RHOAuthIntrospect,
                                              RHOAuthMetadata, RHOAuthRevoke, RHOAuthToken, RHOAuthUserAppRevoke,
                                              RHOAuthUserApps, RHPersonalTokens, RHResetPersonalToken,
                                              RHRevokePersonalToken)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('oauth', __name__, template_folder='templates', virtual_template_folder='oauth')

# Application endpoints
_bp.add_url_rule('/.well-known/oauth-authorization-server', 'oauth_metadata', RHOAuthMetadata)
_bp.add_url_rule('/oauth/authorize', 'oauth_authorize', RHOAuthAuthorize, methods=('GET', 'POST'))
_bp.add_url_rule('/oauth/token', 'oauth_token', RHOAuthToken, methods=('POST',))
_bp.add_url_rule('/oauth/introspect', 'oauth_introspect', RHOAuthIntrospect, methods=('POST',))
_bp.add_url_rule('/oauth/revoke', 'oauth_revoke', RHOAuthRevoke, methods=('POST',))

# Server administration
_bp.add_url_rule('/admin/apps/', 'apps', RHOAuthAdmin)
_bp.add_url_rule('/admin/apps/new', 'app_new', RHOAuthAdminApplicationNew, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/apps/<int:id>/', 'app_details', RHOAuthAdminApplication, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/apps/<int:id>/delete', 'app_delete', RHOAuthAdminApplicationDelete, methods=('POST',))
_bp.add_url_rule('/admin/apps/<int:id>/reset', 'app_reset', RHOAuthAdminApplicationReset, methods=('POST',))
_bp.add_url_rule('/admin/apps/<int:id>/revoke', 'app_revoke', RHOAuthAdminApplicationRevoke, methods=('POST',))

# User profile
with _bp.add_prefixed_rules('/user/<int:user_id>', '/user'):
    # OAuth app authorizations
    _bp.add_url_rule('/applications/', 'user_apps', RHOAuthUserApps)
    _bp.add_url_rule('/applications/<int:id>/revoke', 'user_app_revoke', RHOAuthUserAppRevoke, methods=('POST',))
    # Personal tokens
    _bp.add_url_rule('/tokens/', 'user_tokens', RHPersonalTokens)
    _bp.add_url_rule('/tokens/new', 'user_token_new', RHCreatePersonalToken, methods=('GET', 'POST'))
    _bp.add_url_rule('/tokens/<int:id>/', 'user_token_edit', RHEditPersonalToken, methods=('GET', 'POST'))
    _bp.add_url_rule('/tokens/<int:id>/revoke', 'user_token_revoke', RHRevokePersonalToken, methods=('POST',))
    _bp.add_url_rule('/tokens/<int:id>/reset', 'user_token_reset', RHResetPersonalToken, methods=('POST',))


@_bp.url_defaults
def _add_user_id(endpoint, values):
    if endpoint.startswith('oauth.user_') and 'user_id' not in values:
        # Inject user id if it's present in the url
        values['user_id'] = request.view_args.get('user_id')
