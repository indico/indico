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

from MaKaC.webinterface.rh import conferenceModif
from indico.web.flask.util import rh_as_view
from indico.web.flask.wrappers import IndicoBlueprint


event_mgmt = IndicoBlueprint('event_mgmt', __name__, url_prefix='/event/<confId>/manage')

# Management entrance (redirects to most appropriate page)
event_mgmt.add_url_rule('/', 'conferenceModification-managementAccess',
                        rh_as_view(conferenceModif.RHConferenceModifManagementAccess))

# General settings
event_mgmt.add_url_rule('/general/', 'conferenceModification', rh_as_view(conferenceModif.RHConferenceModification))
event_mgmt.add_url_rule('/general/screendates', 'conferenceModification-screenDates',
                        rh_as_view(conferenceModif.RHConfScreenDatesEdit), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/general/data', 'conferenceModification-data', rh_as_view(conferenceModif.RHConfDataModif),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/general/data/save', 'conferenceModification-dataPerform',
                        rh_as_view(conferenceModif.RHConfPerformDataModif), methods=('POST',))

# Contribution types
event_mgmt.add_url_rule('/contribution-types/add', 'conferenceModification-addContribType',
                        rh_as_view(conferenceModif.RHConfAddContribType), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contribution-types/delete', 'conferenceModification-removeContribType',
                        rh_as_view(conferenceModif.RHConfRemoveContribType), methods=('POST',))
event_mgmt.add_url_rule('/contribution-types/<contribTypeId>', 'conferenceModification-editContribType',
                        rh_as_view(conferenceModif.RHConfEditContribType), methods=('GET', 'POST'))

# Tools
event_mgmt.add_url_rule('/tools/', 'confModifTools', rh_as_view(conferenceModif.RHConfModifTools))

# Tools: Alarms
event_mgmt.add_url_rule('/tools/alarms/', 'confModifTools-displayAlarm', rh_as_view(conferenceModif.RHConfDisplayAlarm))
event_mgmt.add_url_rule('/tools/alarms/add', 'confModifTools-addAlarm',
                        rh_as_view(conferenceModif.RHConfAddAlarm), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/alarms/add/save', 'confModifTools-saveAlarm',
                        rh_as_view(conferenceModif.RHConfSaveAlarm), methods=('POST',))
event_mgmt.add_url_rule('/tools/alarms/add/trigger', 'confModifTools-sendAlarmNow',
                        rh_as_view(conferenceModif.RHConfSendAlarmNow), methods=('POST',))
event_mgmt.add_url_rule('/tools/alarms/<alarmId>/', 'confModifTools-modifyAlarm',
                        rh_as_view(conferenceModif.RHConfModifyAlarm))
event_mgmt.add_url_rule('/tools/alarms/<alarmId>/', 'confModifTools-modifySaveAlarm',
                        rh_as_view(conferenceModif.RHConfSaveAlarm), methods=('POST',))
event_mgmt.add_url_rule('/tools/alarms/<alarmId>/delete', 'confModifTools-deleteAlarm',
                        rh_as_view(conferenceModif.RHConfDeleteAlarm))
event_mgmt.add_url_rule('/tools/alarms/<alarmId>/trigger', 'confModifTools-sendAlarmNow',
                        rh_as_view(conferenceModif.RHConfSendAlarmNow), methods=('POST',))
