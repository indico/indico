# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from indico.legacy.services.implementation.base import LoggedOnlyService
from indico.legacy.services.interface.rpc.common import ServiceError


class UserGetEmail(LoggedOnlyService):
    def _process_args(self):
        LoggedOnlyService._process_args(self)

    def _getAnswer(self):
        if session.user:
            return session.user.email
        else:
            raise ServiceError("ERR-U4", "User is not logged in")


methodMap = {
    'data.email.get': UserGetEmail
}
