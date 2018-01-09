# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import jsonify, session

from indico.modules.oauth import oauth
from indico.modules.users import User
from indico.web.http_api.hooks.base import HTTPAPIHook
from indico.web.http_api.responses import HTTPAPIError


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
