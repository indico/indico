# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh import sessionModif
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.management import event_mgmt


# Main
event_mgmt.add_url_rule('/session/<sessionId>/', 'sessionModification', rh_as_view(sessionModif.RHSessionModification))
event_mgmt.add_url_rule('/session/<sessionId>/modify', 'sessionModification-modify',
                        rh_as_view(sessionModif.RHSessionDataModification), methods=('GET', 'POST'))

# Contributions
event_mgmt.add_url_rule('/session/<sessionId>/contributions/', 'sessionModification-contribList',
                        rh_as_view(sessionModif.RHContribList), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/direct-access', 'sessionModification-contribQuickAccess',
                        rh_as_view(sessionModif.RHContribQuickAccess), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/add', 'sessionModification-addContribs',
                        rh_as_view(sessionModif.RHAddContribs), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/perform-action', 'sessionModification-contribAction',
                        rh_as_view(sessionModif.RHContribsActions), methods=('POST',))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/contributions.pdf', 'sessionModification-contribsToPDF',
                        rh_as_view(sessionModif.RHContribsToPDF), methods=('POST',))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/participants', 'sessionModification-participantList',
                        rh_as_view(sessionModif.RHContribsParticipantList), methods=('POST',))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/edit/<contribId>', 'sessionModification-editContrib',
                        rh_as_view(sessionModif.RHContribListEditContrib), methods=('GET', 'POST'))

# Timetable
event_mgmt.add_url_rule('/session/<sessionId>/timetable/', 'sessionModifSchedule',
                        rh_as_view(sessionModif.RHSessionModifSchedule), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/timetable/fit-slot', 'sessionModifSchedule-fitSlot',
                        rh_as_view(sessionModif.RHFitSlot), methods=('POST',))
event_mgmt.add_url_rule('/session/<sessionId>/timetable/slot-calc', 'sessionModifSchedule-slotCalc',
                        rh_as_view(sessionModif.RHSlotCalc), methods=('POST',))

# Comment
event_mgmt.add_url_rule('/session/<sessionId>/comment/', 'sessionModifComm',
                        rh_as_view(sessionModif.RHSessionModifComm))
event_mgmt.add_url_rule('/session/<sessionId>/comment/edit', 'sessionModifComm-edit',
                        rh_as_view(sessionModif.RHSessionModifCommEdit), methods=('GET', 'POST'))

# Material
event_mgmt.add_url_rule('/session/<sessionId>/material/', 'sessionModification-materials',
                        rh_as_view(sessionModif.RHMaterials))
event_mgmt.add_url_rule('/session/<sessionId>/material/add', 'sessionModification-materialsAdd',
                        rh_as_view(sessionModif.RHMaterialsAdd), methods=('POST',))

# Protection
event_mgmt.add_url_rule('/session/<sessionId>/access/', 'sessionModifAC', rh_as_view(sessionModif.RHSessionModifAC))
event_mgmt.add_url_rule('/session/<sessionId>/access/visibility', 'sessionModifAC-setVisibility',
                        rh_as_view(sessionModif.RHSessionSetVisibility), methods=('POST',))

# Tools
event_mgmt.add_url_rule('/session/<sessionId>/tools/', 'sessionModifTools',
                        rh_as_view(sessionModif.RHSessionModifTools))
event_mgmt.add_url_rule('/session/<sessionId>/tools/delete', 'sessionModifTools-delete',
                        rh_as_view(sessionModif.RHSessionDeletion), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/tools/lock', 'sessionModification-close',
                        rh_as_view(sessionModif.RHSessionClose), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/tools/unlock', 'sessionModification-open',
                        rh_as_view(sessionModif.RHSessionOpen), methods=('POST',))
