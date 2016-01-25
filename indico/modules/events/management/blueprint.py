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

from __future__ import unicode_literals

from indico.modules.events.management.controllers import RHDeleteEvent, RHLockEvent, RHUnlockEvent, RHEmailEventPersons
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_management', __name__, template_folder='templates',
                      virtual_template_folder='events/management',
                      url_prefix='/event/<confId>/manage')

_bp.add_url_rule('/delete', 'delete', RHDeleteEvent, methods=('GET', 'POST'))
_bp.add_url_rule('/lock', 'lock', RHLockEvent, methods=('GET', 'POST'))
_bp.add_url_rule('/unlock', 'unlock', RHUnlockEvent, methods=('POST',))
_bp.add_url_rule('/manage/person-list/email', 'email_event_persons', RHEmailEventPersons, methods=('POST',))
