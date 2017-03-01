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

from __future__ import unicode_literals

from flask import session
from werkzeug.exceptions import NotFound, Forbidden

from indico.core.config import Config
from indico.modules.rb.util import rb_check_user_access
from indico.util.i18n import _
from indico.legacy.webinterface.rh.base import RHProtected


class RHRoomBookingProtected(RHProtected):
    def _checkSessionUser(self):
        if not Config.getInstance().getIsRoomBookingActive():
            raise NotFound(_('The room booking module is not enabled.'))
        RHProtected._checkSessionUser(self)
        if not rb_check_user_access(session.user):
            raise Forbidden(_('Your are not authorized to access the room booking system.'))


class RHRoomBookingBase(RHRoomBookingProtected):
    """Base class for room booking RHs"""
    pass
