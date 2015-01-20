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

from MaKaC.webinterface.rh import conferenceModif, fileAccess
from indico.web.flask.blueprints.event.management import event_mgmt


# Tools
event_mgmt.add_url_rule('/tools/', 'confModifTools', conferenceModif.RHConfModifTools)

# Tools: Alarms
event_mgmt.add_url_rule('/tools/alarms/', 'confModifTools-displayAlarm', conferenceModif.RHConfDisplayAlarm)
event_mgmt.add_url_rule('/tools/alarms/add', 'confModifTools-addAlarm', conferenceModif.RHConfAddAlarm,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/alarms/add/save', 'confModifTools-saveAlarm', conferenceModif.RHConfSaveAlarm,
                        methods=('POST',))
event_mgmt.add_url_rule('/tools/alarms/add/trigger', 'confModifTools-sendAlarmNow', conferenceModif.RHConfSendAlarmNow,
                        methods=('POST',))
event_mgmt.add_url_rule('/tools/alarms/<alarmId>/', 'confModifTools-modifyAlarm', conferenceModif.RHConfModifyAlarm)
event_mgmt.add_url_rule('/tools/alarms/<alarmId>/', 'confModifTools-modifySaveAlarm', conferenceModif.RHConfSaveAlarm,
                        methods=('POST',))
event_mgmt.add_url_rule('/tools/alarms/<alarmId>/delete', 'confModifTools-deleteAlarm',
                        conferenceModif.RHConfDeleteAlarm)
event_mgmt.add_url_rule('/tools/alarms/<alarmId>/trigger', 'confModifTools-sendAlarmNow',
                        conferenceModif.RHConfSendAlarmNow, methods=('POST',))

# Tools: Clone
event_mgmt.add_url_rule('/tools/clone', 'confModifTools-clone', conferenceModif.RHConfClone)
event_mgmt.add_url_rule('/tools/clone', 'confModifTools-performCloning', conferenceModif.RHConfPerformCloning,
                        methods=('POST',))

# Tools: Delete
event_mgmt.add_url_rule('/tools/delete', 'confModifTools-delete', conferenceModif.RHConfDeletion,
                        methods=('GET', 'POST'))

# Tools: Lock
event_mgmt.add_url_rule('/tools/lock', 'conferenceModification-close', conferenceModif.RHConferenceClose,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/unlock', 'conferenceModification-open', conferenceModif.RHConferenceOpen,
                        methods=('GET', 'POST'))

# Tools: Posters
event_mgmt.add_url_rule('/tools/posters/', 'confModifTools-posterPrinting', conferenceModif.RHConfPosterPrinting,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/posters/poster.pdf', 'confModifTools-posterPrintingPDF',
                        conferenceModif.RHConfPosterPrintingPDF, methods=('POST',))
event_mgmt.add_url_rule('/tools/posters/design', 'confModifTools-posterDesign', conferenceModif.RHConfPosterDesign,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/posters/background', 'confModifTools-posterGetBackground',
                        conferenceModif.RHConfPosterGetBackground, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/posters/save-background', 'confModifTools-posterSaveBackground',
                        conferenceModif.RHConfPosterSaveTempBackground, methods=('POST',))

# Tools: Badges
event_mgmt.add_url_rule('/tools/badges/', 'confModifTools-badgePrinting', conferenceModif.RHConfBadgePrinting,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/badges/badges.pdf', 'confModifTools-badgePrintingPDF',
                        conferenceModif.RHConfBadgePrintingPDF, methods=('POST',))
event_mgmt.add_url_rule('/tools/badges/design', 'confModifTools-badgeDesign', conferenceModif.RHConfBadgeDesign,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/badges/background', 'confModifTools-badgeGetBackground',
                        conferenceModif.RHConfBadgeGetBackground, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/badges/save-background', 'confModifTools-badgeSaveBackground',
                        conferenceModif.RHConfBadgeSaveTempBackground, methods=('POST',))

# Tools: Material Package
event_mgmt.add_url_rule('/tools/material-package', 'confModifTools-matPkg', conferenceModif.RHFullMaterialPackage)
event_mgmt.add_url_rule('/tools/material-package', 'confModifTools-performMatPkg',
                        conferenceModif.RHFullMaterialPackagePerform, methods=('POST',))

# Tools: Offline version
event_mgmt.add_url_rule('/tools/offline/', 'confModifTools-offline', conferenceModif.RHConfOffline)
event_mgmt.add_url_rule('/tools/offline/<fileId>.zip', 'getFile-offlineEvent', fileAccess.RHOfflineEventAccess)
