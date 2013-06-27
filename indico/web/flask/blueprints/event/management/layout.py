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
from indico.web.flask.blueprints.event.management import event_mgmt


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
