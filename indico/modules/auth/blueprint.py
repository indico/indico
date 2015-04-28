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

from flask import request

from indico.modules.auth.controllers import (RHLogin, RHLoginForm, RHLogout, RHAssociateIdentity, RHRegister,
                                             RHResetPassword, RHUserAccounts, RHUserAccountsRemove)
from indico.web.flask.wrappers import IndicoBlueprint

auth_blueprint = _bp = IndicoBlueprint('auth', __name__, template_folder='templates')


_bp.add_url_rule('/login/', 'login', RHLogin, methods=('GET', 'POST'))
_bp.add_url_rule('/login/<provider>/', 'login', RHLogin)
_bp.add_url_rule('/login/<provider>/form', 'login_form', RHLoginForm)
_bp.add_url_rule('/login/<provider>/link-account', 'associate_identity', RHAssociateIdentity, methods=('GET', 'POST'))

_bp.add_url_rule('/logout/', 'logout', RHLogout, methods=('GET', 'POST'))

_bp.add_url_rule('/register/', 'register', RHRegister, methods=('GET', 'POST'), defaults={'provider': None})
_bp.add_url_rule('/register/<provider>', 'register', RHRegister, methods=('GET', 'POST'))

_bp.add_url_rule('/reset-password/', 'resetpass', RHResetPassword, methods=('GET', 'POST'))

with _bp.add_prefixed_rules('/user/<int:user_id>', '/user'):
    _bp.add_url_rule('/accounts/', 'accounts', RHUserAccounts, methods=('GET', 'POST'))
    _bp.add_url_rule('/accounts/<identity>/remove/', 'remove_account', RHUserAccountsRemove, methods=('POST',))


@_bp.url_defaults
def _add_user_id(endpoint, values):
    if endpoint in {'auth.accounts', 'auth.remove_account'} and 'user_id' not in values:
        values['user_id'] = request.view_args.get('user_id')
