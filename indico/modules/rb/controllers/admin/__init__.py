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
from werkzeug.exceptions import Forbidden

from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.util import rb_is_admin
from indico.util.i18n import _


class RHRoomBookingAdminBase(RHRoomBookingBase):
    """
    Adds admin authorization. All classes that implement admin
    tasks should be derived from this class.
    """

    def _checkProtection(self):
        if session.user is None:
            self._checkSessionUser()
        elif not rb_is_admin(session.user):
            raise Forbidden(_('You are not authorized to take this action.'))
