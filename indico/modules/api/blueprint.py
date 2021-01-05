# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request

from indico.legacy.services.interface.rpc.json import process as jsonrpc_handler
from indico.modules.api.controllers import (RHAPIAdminKeys, RHAPIAdminSettings, RHAPIBlockKey, RHAPIBuildURLs,
                                            RHAPICreateKey, RHAPIDeleteKey, RHAPITogglePersistent, RHAPIUserProfile)
from indico.web.flask.wrappers import IndicoBlueprint
from indico.web.http_api.handlers import handler as api_handler


_bp = IndicoBlueprint('api', __name__, template_folder='templates', virtual_template_folder='api')

# Legacy JSON-RPC API
_bp.add_url_rule('/services/json-rpc', view_func=jsonrpc_handler, endpoint='jsonrpc', methods=('POST',))

# HTTP API
_bp.add_url_rule('/export/<path:path>', view_func=api_handler, endpoint='httpapi', defaults={'prefix': 'export'})
_bp.add_url_rule('/api/<path:path>', view_func=api_handler, endpoint='httpapi', defaults={'prefix': 'api'},
                 methods=('POST',))
_bp.add_url_rule('/<any(api, export):prefix>', endpoint='httpapi', build_only=True)
_bp.add_url_rule('/api/build-urls', 'build_urls', RHAPIBuildURLs, methods=('POST',))

# Administration
_bp.add_url_rule('/admin/api/', 'admin_settings', RHAPIAdminSettings, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/api/keys', 'admin_keys', RHAPIAdminKeys)

# User profile
with _bp.add_prefixed_rules('/user/<int:user_id>', '/user'):
    _bp.add_url_rule('/api/', 'user_profile', RHAPIUserProfile)
    _bp.add_url_rule('/api/create', 'key_create', RHAPICreateKey, methods=('POST',))
    _bp.add_url_rule('/api/delete', 'key_delete', RHAPIDeleteKey, methods=('POST',))
    _bp.add_url_rule('/api/persistent', 'key_toggle_persistent', RHAPITogglePersistent, methods=('POST',))
    _bp.add_url_rule('/api/block', 'key_block', RHAPIBlockKey, methods=('POST',))


@_bp.url_defaults
def _add_user_id(endpoint, values):
    if (endpoint == 'api.user_profile' or endpoint.startswith('api.key_')) and 'user_id' not in values:
        # Inject user id if it's present in the url
        values['user_id'] = request.view_args.get('user_id')
