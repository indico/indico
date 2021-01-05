# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import jsonify, request, session

from indico.modules.oauth import oauth
from indico.modules.users import User
from indico.web.http_api.hooks.base import HTTPAPIHook
from indico.web.http_api.responses import HTTPAPIError
from indico.web.rh import RHProtected


def fetch_authenticated_user():
    valid, req = oauth.verify_request(['read:user'])
    user = req.user if valid else session.user
    if not user:
        return jsonify()
    return jsonify(id=user.id, email=user.email, first_name=user.first_name, last_name=user.last_name,
                   admin=user.is_admin)


@HTTPAPIHook.register
class UserInfoHook(HTTPAPIHook):
    TYPES = ('user',)
    RE = r'(?P<user_id>[\d]+)'
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):
        super(UserInfoHook, self)._getParams()
        self._user_id = self._pathParams['user_id']

    def export_user(self, user):
        if not user:
            raise HTTPAPIError('You need to be logged in', 403)
        user = User.get(self._user_id, is_deleted=False)
        if not user:
            raise HTTPAPIError('Requested user not found', 404)
        if not user.can_be_modified(user):
            raise HTTPAPIError('You do not have access to that info', 403)
        return [user.as_avatar.fossilize()]


class RHUserFavoritesAPI(RHProtected):
    def _process_args(self):
        self.user = User.get_or_404(request.view_args['user_id']) if 'user_id' in request.view_args else None

    def _process_GET(self):
        return jsonify(sorted(u.id for u in session.user.favorite_users))

    def _process_PUT(self):
        session.user.favorite_users.add(self.user)
        return jsonify(self.user.id), 201

    def _process_DELETE(self):
        session.user.favorite_users.discard(self.user)
        return '', 204
