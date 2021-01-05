# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request

from indico.modules.oauth.controllers import (RHOAuthAdmin, RHOAuthAdminApplication, RHOAuthAdminApplicationDelete,
                                              RHOAuthAdminApplicationNew, RHOAuthAdminApplicationReset,
                                              RHOAuthAdminApplicationRevoke, RHOAuthAuthorize, RHOAuthErrors,
                                              RHOAuthToken, RHOAuthUserProfile, RHOAuthUserTokenRevoke)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('oauth', __name__, template_folder='templates', virtual_template_folder='oauth')

# Application endpoints
_bp.add_url_rule('/oauth/authorize', 'oauth_authorize', RHOAuthAuthorize, methods=('GET', 'POST'))
_bp.add_url_rule('/oauth/errors', 'oauth_errors', RHOAuthErrors)
_bp.add_url_rule('/oauth/token', 'oauth_token', RHOAuthToken, methods=('POST',))

# Server administration
_bp.add_url_rule('/admin/apps/', 'apps', RHOAuthAdmin)
_bp.add_url_rule('/admin/apps/new', 'app_new', RHOAuthAdminApplicationNew, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/apps/<int:id>/', 'app_details', RHOAuthAdminApplication, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/apps/<int:id>/delete', 'app_delete', RHOAuthAdminApplicationDelete, methods=('POST',))
_bp.add_url_rule('/admin/apps/<int:id>/reset', 'app_reset', RHOAuthAdminApplicationReset, methods=('POST',))
_bp.add_url_rule('/admin/apps/<int:id>/revoke', 'app_revoke', RHOAuthAdminApplicationRevoke, methods=('POST',))

# User profile
with _bp.add_prefixed_rules('/user/<int:user_id>', '/user'):
    _bp.add_url_rule('/applications/', 'user_profile', RHOAuthUserProfile)
    _bp.add_url_rule('/applications/<int:id>/revoke', 'user_token_revoke', RHOAuthUserTokenRevoke, methods=('POST',))


@_bp.url_defaults
def _add_user_id(endpoint, values):
    if endpoint in {'oauth.user_profile', 'oauth.user_token_revoke'} and 'user_id' not in values:
        # Inject user id if it's present in the url
        values['user_id'] = request.view_args.get('user_id')
