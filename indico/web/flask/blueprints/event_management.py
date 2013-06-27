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

# Tools: Clone
event_mgmt.add_url_rule('/tools/clone', 'confModifTools-clone', rh_as_view(conferenceModif.RHConfClone))
event_mgmt.add_url_rule('/tools/clone', 'confModifTools-performCloning',
                        rh_as_view(conferenceModif.RHConfPerformCloning), methods=('POST',))

# Tools: Delete
event_mgmt.add_url_rule('/tools/delete', 'confModifTools-delete', rh_as_view(conferenceModif.RHConfDeletion),
                        methods=('GET', 'POST'))

# Tools: Lock
event_mgmt.add_url_rule('/tools/lock', 'conferenceModification-close', rh_as_view(conferenceModif.RHConferenceClose),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/unlock', 'conferenceModification-open', rh_as_view(conferenceModif.RHConferenceOpen),
                        methods=('GET', 'POST'))

# Tools: Posters
event_mgmt.add_url_rule('/tools/posters/', 'confModifTools-posterPrinting',
                        rh_as_view(conferenceModif.RHConfPosterPrinting), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/posters/poster.pdf', 'confModifTools-posterPrintingPDF',
                        rh_as_view(conferenceModif.RHConfPosterPrintingPDF), methods=('POST',))
event_mgmt.add_url_rule('/tools/posters/design', 'confModifTools-posterDesign',
                        rh_as_view(conferenceModif.RHConfPosterDesign), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/posters/background', 'confModifTools-posterGetBackground',
                        rh_as_view(conferenceModif.RHConfPosterGetBackground), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/posters/save-background', 'confModifTools-posterSaveBackground',
                        rh_as_view(conferenceModif.RHConfPosterSaveTempBackground), methods=('POST',))

# Tools: Badges
event_mgmt.add_url_rule('/tools/badges/', 'confModifTools-badgePrinting',
                        rh_as_view(conferenceModif.RHConfBadgePrinting), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/badges/badges.pdf', 'confModifTools-badgePrintingPDF',
                        rh_as_view(conferenceModif.RHConfBadgePrintingPDF), methods=('POST',))
event_mgmt.add_url_rule('/tools/badges/design', 'confModifTools-badgeDesign',
                        rh_as_view(conferenceModif.RHConfBadgeDesign), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/badges/background', 'confModifTools-badgeGetBackground',
                        rh_as_view(conferenceModif.RHConfBadgeGetBackground), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/tools/badges/save-background', 'confModifTools-badgeSaveBackground',
                        rh_as_view(conferenceModif.RHConfBadgeSaveTempBackground), methods=('POST',))

# Tools: Material Package
event_mgmt.add_url_rule('/tools/material-package', 'confModifTools-matPkg',
                        rh_as_view(conferenceModif.RHFullMaterialPackage))
event_mgmt.add_url_rule('/tools/material-package', 'confModifTools-performMatPkg',
                        rh_as_view(conferenceModif.RHFullMaterialPackagePerform), methods=('POST',))

# Logs
event_mgmt.add_url_rule('/logs', 'confModifLog', rh_as_view(conferenceModif.RHConfModifLog))

# Layout: Layout/style customization
event_mgmt.add_url_rule('/layout/style/', 'confModifDisplay',
                        rh_as_view(conferenceModif.RHConfModifDisplayCustomization))
event_mgmt.add_url_rule('/layout/style/', 'confModifDisplay-custom',
                        rh_as_view(conferenceModif.RHConfModifDisplayCustomization))
event_mgmt.add_url_rule('/layout/style/css/preview', 'confModifDisplay-previewCSS',
                        rh_as_view(conferenceModif.RHConfModifPreviewCSS), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/layout/style/css/remove', 'confModifDisplay-removeCSS',
                        rh_as_view(conferenceModif.RHConfRemoveCSS))
event_mgmt.add_url_rule('/layout/style/css/upload', 'confModifDisplay-saveCSS',
                        rh_as_view(conferenceModif.RHConfSaveCSS), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/layout/style/css/select', 'confModifDisplay-useCSS', rh_as_view(conferenceModif.RHConfUseCSS),
                        methods=('POST',))
event_mgmt.add_url_rule('/layout/style/colors/title-bg', 'confModifDisplay-formatTitleBgColor',
                        rh_as_view(conferenceModif.RHConfModifFormatTitleBgColor), methods=('POST',))
event_mgmt.add_url_rule('/layout/style/colors/title-text', 'confModifDisplay-formatTitleTextColor',
                        rh_as_view(conferenceModif.RHConfModifFormatTitleTextColor), methods=('POST',))
event_mgmt.add_url_rule('/layout/style/logo/remove', 'confModifDisplay-removeLogo',
                        rh_as_view(conferenceModif.RHConfRemoveLogo), methods=('POST',))
event_mgmt.add_url_rule('/layout/style/logo/upload', 'confModifDisplay-saveLogo',
                        rh_as_view(conferenceModif.RHConfSaveLogo), methods=('POST',))

# Layout: Conference header
event_mgmt.add_url_rule('/layout/header/', 'confModifDisplay-confHeader',
                        rh_as_view(conferenceModif.RHConfModifDisplayConfHeader))
event_mgmt.add_url_rule('/layout/header/ticker', 'confModifDisplay-tickerTapeAction',
                        rh_as_view(conferenceModif.RHConfModifTickerTapeAction), methods=('POST',))
event_mgmt.add_url_rule('/layout/header/navbar', 'confModifDisplay-toggleNavigationBar',
                        rh_as_view(conferenceModif.RHConfModifToggleNavigationBar), methods=('POST',))
event_mgmt.add_url_rule('/layout/header/search', 'confModifDisplay-toggleSearch',
                        rh_as_view(conferenceModif.RHConfModifToggleSearch), methods=('POST',))

# Layout: Menu
event_mgmt.add_url_rule('/layout/menu/', 'confModifDisplay-menu', rh_as_view(conferenceModif.RHConfModifDisplayMenu))
event_mgmt.add_url_rule('/layout/menu/<linkId>/', 'confModifDisplay-menu',
                        rh_as_view(conferenceModif.RHConfModifDisplayMenu))
event_mgmt.add_url_rule('/layout/menu/<linkId>/up', 'confModifDisplay-upLink',
                        rh_as_view(conferenceModif.RHConfModifDisplayUpLink))
event_mgmt.add_url_rule('/layout/menu/<linkId>/down', 'confModifDisplay-downLink',
                        rh_as_view(conferenceModif.RHConfModifDisplayDownLink))
event_mgmt.add_url_rule('/layout/menu/<linkId>/toggle', 'confModifDisplay-toggleLinkStatus',
                        rh_as_view(conferenceModif.RHConfModifDisplayToggleLinkStatus), methods=('POST',))
event_mgmt.add_url_rule('/layout/menu/<linkId>/remove', 'confModifDisplay-removeLink',
                        rh_as_view(conferenceModif.RHConfModifDisplayRemoveLink), methods=('POST',))
event_mgmt.add_url_rule('/layout/menu/<linkId>/modify', 'confModifDisplay-modifyData',
                        rh_as_view(conferenceModif.RHConfModifDisplayModifyData), methods=('POST',))
event_mgmt.add_url_rule('/layout/menu/<linkId>/modify-sys', 'confModifDisplay-modifySystemData',
                        rh_as_view(conferenceModif.RHConfModifDisplayModifySystemData), methods=('POST',))
event_mgmt.add_url_rule('/layout/menu/<linkId>/homepage', 'confModifDisplay-toggleHomePage',
                        rh_as_view(conferenceModif.RHConfModifDisplayToggleHomePage), methods=('POST',))
event_mgmt.add_url_rule('/layout/menu/add/link/<linkId>', 'confModifDisplay-addLink',
                        rh_as_view(conferenceModif.RHConfModifDisplayAddLink), methods=('POST',))
event_mgmt.add_url_rule('/layout/menu/add/link', 'confModifDisplay-addLink',
                        rh_as_view(conferenceModif.RHConfModifDisplayAddLink), methods=('POST',))
event_mgmt.add_url_rule('/layout/menu/add/spacer', 'confModifDisplay-addSpacer',
                        rh_as_view(conferenceModif.RHConfModifDisplayAddSpacer), methods=('POST',))
event_mgmt.add_url_rule('/layout/menu/add/page', 'confModifDisplay-addPage',
                        rh_as_view(conferenceModif.RHConfModifDisplayAddPage), methods=('POST',))

# Layout: Images
event_mgmt.add_url_rule('/layout/images/', 'confModifDisplay-resources',
                        rh_as_view(conferenceModif.RHConfModifDisplayResources))
event_mgmt.add_url_rule('/layout/images/upload', 'confModifDisplay-savePic', rh_as_view(conferenceModif.RHConfSavePic),
                        methods=('POST',))
