# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
from MaKaC.webinterface.rh import conferenceModif
from indico.web.flask.blueprints.event.management import event_mgmt


# Main

event_mgmt.add_url_rule('/sessions', 'conferenceSessions-query', conferenceModif.RConferenceGetSessions,
                        methods=('GET',))

event_mgmt.add_url_rule('/session/<sessionId>/', 'sessionModification', sessionModif.RHSessionModification)
event_mgmt.add_url_rule('/session/<sessionId>/modify', 'sessionModification-modify',
                        sessionModif.RHSessionDataModification, methods=('GET', 'POST'))

# Contributions
event_mgmt.add_url_rule('/session/<sessionId>/contributions/', 'sessionModification-contribList',
                        sessionModif.RHContribList, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/direct-access', 'sessionModification-contribQuickAccess',
                        sessionModif.RHContribQuickAccess, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/add', 'sessionModification-addContribs',
                        sessionModif.RHAddContribs, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/perform-action', 'sessionModification-contribAction',
                        sessionModif.RHContribsActions, methods=('POST',))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/contributions.pdf', 'sessionModification-contribsToPDF',
                        sessionModif.RHContribsToPDF, methods=('POST',))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/participants', 'sessionModification-participantList',
                        sessionModif.RHContribsParticipantList, methods=('POST',))
event_mgmt.add_url_rule('/session/<sessionId>/contributions/edit/<contribId>', 'sessionModification-editContrib',
                        sessionModif.RHContribListEditContrib, methods=('GET', 'POST'))

# Timetable
event_mgmt.add_url_rule('/session/<sessionId>/timetable/', 'sessionModifSchedule', sessionModif.RHSessionModifSchedule,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/timetable/fit-slot', 'sessionModifSchedule-fitSlot',
                        sessionModif.RHFitSlot, methods=('POST',))
event_mgmt.add_url_rule('/session/<sessionId>/timetable/slot-calc', 'sessionModifSchedule-slotCalc',
                        sessionModif.RHSlotCalc, methods=('POST',))

# Comment
event_mgmt.add_url_rule('/session/<sessionId>/comment/', 'sessionModifComm', sessionModif.RHSessionModifComm)
event_mgmt.add_url_rule('/session/<sessionId>/comment/edit', 'sessionModifComm-edit',
                        sessionModif.RHSessionModifCommEdit, methods=('GET', 'POST'))

# Material
event_mgmt.add_url_rule('/session/<sessionId>/material/', 'sessionModification-materials', sessionModif.RHMaterials)
event_mgmt.add_url_rule('/session/<sessionId>/material/add', 'sessionModification-materialsAdd',
                        sessionModif.RHMaterialsAdd, methods=('POST',))

# Protection
event_mgmt.add_url_rule('/session/<sessionId>/access/', 'sessionModifAC', sessionModif.RHSessionModifAC)
event_mgmt.add_url_rule('/session/<sessionId>/access/visibility', 'sessionModifAC-setVisibility',
                        sessionModif.RHSessionSetVisibility, methods=('POST',))

# Tools
event_mgmt.add_url_rule('/session/<sessionId>/tools/', 'sessionModifTools', sessionModif.RHSessionModifTools)
event_mgmt.add_url_rule('/session/<sessionId>/tools/delete', 'sessionModifTools-delete', sessionModif.RHSessionDeletion,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/tools/lock', 'sessionModification-close', sessionModif.RHSessionClose,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/session/<sessionId>/tools/unlock', 'sessionModification-open', sessionModif.RHSessionOpen,
                        methods=('POST',))
