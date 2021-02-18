# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from authlib.integrations.flask_oauth2 import current_token
from flask import jsonify

from indico.core.oauth import require_oauth
from indico.modules.users import User
from indico.web.http_api.hooks.base import HTTPAPIHook
from indico.web.http_api.responses import HTTPAPIError


@require_oauth('read:user')
def fetch_authenticated_user():
    user = current_token.user
    return jsonify(id=user.id, email=user.email, first_name=user.first_name, last_name=user.last_name,
                   admin=user.is_admin)


@HTTPAPIHook.register
class UserInfoHook(HTTPAPIHook):
    TYPES = ('user',)
    RE = r'(?P<user_id>[\d]+)'
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):
        super()._getParams()
        self._user_id = self._pathParams['user_id']

    def export_user(self, user):
        from indico.modules.users.schemas import UserSchema

        if not user:
            raise HTTPAPIError('You need to be logged in', 403)
        user = User.get(self._user_id, is_deleted=False)
        if not user:
            raise HTTPAPIError('Requested user not found', 404)
        if not user.can_be_modified(user):
            raise HTTPAPIError('You do not have access to that info', 403)
        return [UserSchema().dump(user)]
