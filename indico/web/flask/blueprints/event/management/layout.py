# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from MaKaC.webinterface.rh import conferenceModif
from indico.web.flask.blueprints.event.management import event_mgmt


# Layout: Layout/style customization
event_mgmt.add_url_rule('/layout/style/', 'confModifDisplay', conferenceModif.RHConfModifDisplayCustomization)
event_mgmt.add_url_rule('/layout/style/', 'confModifDisplay-custom', conferenceModif.RHConfModifDisplayCustomization)
event_mgmt.add_url_rule('/layout/style/css/preview', 'confModifDisplay-previewCSS',
                        conferenceModif.RHConfModifPreviewCSS, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/layout/style/css/remove', 'confModifDisplay-removeCSS', conferenceModif.RHConfRemoveCSS)
event_mgmt.add_url_rule('/layout/style/css/upload', 'confModifDisplay-saveCSS', conferenceModif.RHConfSaveCSS,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/layout/style/css/select', 'confModifDisplay-useCSS', conferenceModif.RHConfUseCSS,
                        methods=('POST',))
event_mgmt.add_url_rule('/layout/style/colors/title-bg', 'confModifDisplay-formatTitleBgColor',
                        conferenceModif.RHConfModifFormatTitleBgColor, methods=('POST',))
event_mgmt.add_url_rule('/layout/style/colors/title-text', 'confModifDisplay-formatTitleTextColor',
                        conferenceModif.RHConfModifFormatTitleTextColor, methods=('POST',))
event_mgmt.add_url_rule('/layout/style/logo/remove', 'confModifDisplay-removeLogo', conferenceModif.RHConfRemoveLogo,
                        methods=('POST',))
event_mgmt.add_url_rule('/layout/style/logo/upload', 'confModifDisplay-saveLogo', conferenceModif.RHConfSaveLogo,
                        methods=('POST',))

# Layout: Conference header
event_mgmt.add_url_rule('/layout/header/', 'confModifDisplay-confHeader', conferenceModif.RHConfModifDisplayConfHeader)
event_mgmt.add_url_rule('/layout/header/ticker', 'confModifDisplay-tickerTapeAction',
                        conferenceModif.RHConfModifTickerTapeAction, methods=('POST',))
event_mgmt.add_url_rule('/layout/header/navbar', 'confModifDisplay-toggleNavigationBar',
                        conferenceModif.RHConfModifToggleNavigationBar, methods=('POST',))
event_mgmt.add_url_rule('/layout/header/search', 'confModifDisplay-toggleSearch',
                        conferenceModif.RHConfModifToggleSearch, methods=('POST',))
