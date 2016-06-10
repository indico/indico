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

from flask import session

from indico.modules.users import User
from indico.util.i18n import _

from MaKaC.common import timezoneUtils
from MaKaC.common.fossilize import fossilize
from MaKaC.services.implementation.base import AdminService, LoggedOnlyService
from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.interface.rpc.common import NoReportError


class AdminLoginAs(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        pm = ParameterManager(self._params)
        user_id = pm.extract("userId", pType=int, allowEmpty=False)
        self._user = User.get(user_id)
        if self._user is None:
            raise NoReportError(_("The user that you are trying to login as does not exist anymore in the database"))

    def _getAnswer(self):
        # We don't overwrite a previous entry - the original (admin) user should be kept there
        session.setdefault('login_as_orig_user', {
            'session_data': {k: session.pop(k) for k in session.keys() if k[0] != '_' or k in {'_timezone', '_lang'}},
            'user_id': session.user.id,
            'user_name': session.user.get_full_name(last_name_first=False, last_name_upper=False)
        })
        session.user = self._user
        session.lang = session.user.settings.get('lang')
        session.timezone = timezoneUtils.SessionTZ(self._user.as_avatar).getSessionTZ()
        return True


class AdminUndoLoginAs(LoggedOnlyService):

    def _getAnswer(self):
        try:
            entry = session.pop('login_as_orig_user')
        except KeyError:
            raise NoReportError(_('No login-as history entry found'))

        session.user = User.get(entry['user_id'])
        session.update(entry['session_data'])
        return True


class AddAdministrator(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        pm = ParameterManager(self._params)
        self._userList = pm.extract("userList", pType=list, allowEmpty=False)

    def _getAnswer(self):
        for fossil in self._userList:
            user = User.get(int(fossil['id']))
            if user is not None:
                user.is_admin = True
        return fossilize([u.as_avatar for u in User.find(is_admin=True)])


class RemoveAdministrator(AdminService):

    def _checkParams(self):
        AdminService._checkParams(self)
        pm = ParameterManager(self._params)
        self._userId = pm.extract("userId", pType=int, allowEmpty=False)

    def _getAnswer(self):
        user = User.get(self._userId)
        if user is not None:
            user.is_admin = False
        return fossilize([u.as_avatar for u in User.find(is_admin=True)])


methodMap = {
    "general.addExistingAdmin": AddAdministrator,
    "general.removeAdmin": RemoveAdministrator,

    "header.loginAs": AdminLoginAs,
    "header.undoLoginAs": AdminUndoLoginAs
}
