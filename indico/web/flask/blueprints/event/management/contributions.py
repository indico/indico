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

from MaKaC.webinterface.rh import conferenceModif, contribMod, subContribMod
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.management import event_mgmt


# Contribution list
event_mgmt.add_url_rule('/contributions/', 'confModifContribList', rh_as_view(conferenceModif.RHContributionList),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/direct-access', 'confModifContribList-contribQuickAccess',
                        rh_as_view(conferenceModif.RHContribQuickAccess), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/perform-action', 'confModifContribList-contribsActions',
                        rh_as_view(conferenceModif.RHContribsActions), methods=('POST',))
event_mgmt.add_url_rule('/contributions/pdf', 'confModifContribList-contribsToPDFMenu',
                        rh_as_view(conferenceModif.RHContribsToPDFMenu), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/material-package', 'confModifContribList-matPkg',
                        rh_as_view(conferenceModif.RHMaterialPackage), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/moveToSession', 'confModifContribList-moveToSession',
                        rh_as_view(conferenceModif.RHMoveContribsToSession), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/participants', 'confModifContribList-participantList',
                        rh_as_view(conferenceModif.RHContribsParticipantList), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/proceedings', 'confModifContribList-proceedings',
                        rh_as_view(conferenceModif.RHProceedings), methods=('GET', 'POST'))

# Main
event_mgmt.add_url_rule('/contribution/<contribId>/', 'contributionModification',
                        rh_as_view(contribMod.RHContributionModification))
event_mgmt.add_url_rule('/contribution/<contribId>/contribution.xml', 'contributionModification-xml',
                        rh_as_view(contribMod.RHContributionToXML))
event_mgmt.add_url_rule('/contribution/<contribId>/contribution.pdf', 'contributionModification-pdf',
                        rh_as_view(contribMod.RHContributionToPDF))
event_mgmt.add_url_rule('/contribution/<contribId>/modify', 'contributionModification-data',
                        rh_as_view(contribMod.RHContributionData), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contribution/<contribId>/modify/save', 'contributionModification-modifData',
                        rh_as_view(contribMod.RHContributionModifData), methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/change-track', 'contributionModification-setTrack',
                        rh_as_view(contribMod.RHSetTrack), methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/change-session', 'contributionModification-setSession',
                        rh_as_view(contribMod.RHSetSession), methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/withdraw', 'contributionModification-withdraw',
                        rh_as_view(contribMod.RHWithdraw), methods=('POST',))

# Material
event_mgmt.add_url_rule('/contribution/<contribId>/material/', 'contributionModification-materials',
                        rh_as_view(contribMod.RHMaterials), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contribution/<contribId>/material/add', 'contributionModification-materialsAdd',
                        rh_as_view(contribMod.RHMaterialsAdd), methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/material/browse/<materialId>',
                        'contributionModification-browseMaterial', rh_as_view(contribMod.RHContribModifMaterialBrowse))

# Protection
event_mgmt.add_url_rule('/contribution/<contribId>/access/', 'contributionAC', rh_as_view(contribMod.RHContributionAC),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contribution/<contribId>/access/visibility', 'contributionAC-setVisibility',
                        rh_as_view(contribMod.RHContributionSetVisibility), methods=('POST',))

# Tools
event_mgmt.add_url_rule('/contribution/<contribId>/tools/', 'contributionTools',
                        rh_as_view(contribMod.RHContributionTools))
event_mgmt.add_url_rule('/contribution/<contribId>/tools/delete', 'contributionTools-delete',
                        rh_as_view(contribMod.RHContributionDeletion), methods=('GET', 'POST'))

# Subcontributions
event_mgmt.add_url_rule('/contribution/<contribId>/subcontributions/', 'contributionModifSubCont',
                        rh_as_view(contribMod.RHContributionSC))
event_mgmt.add_url_rule('/contribution/<contribId>/subcontributions/add', 'contributionModifSubCont-add',
                        rh_as_view(contribMod.RHContributionAddSC), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contribution/<contribId>/subcontributions/add/save', 'contributionModifSubCont-create',
                        rh_as_view(contribMod.RHContributionCreateSC), methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/subcontributions/perform-action',
                        'contributionModifSubCont-actionSubContribs',
                        rh_as_view(contribMod.RHSubContribActions), methods=('GET', 'POST'))

# Subcontribution
event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/', 'subContributionModification',
                        rh_as_view(subContribMod.RHSubContributionModification), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/modify',
                        'subContributionModification-data', rh_as_view(subContribMod.RHSubContributionData),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/modify/save',
                        'subContributionModification-modifData', rh_as_view(subContribMod.RHSubContributionModifData),
                        methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/material/',
                        'subContributionModification-materials', rh_as_view(subContribMod.RHMaterials),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/material/add',
                        'subContributionModification-materialsAdd', rh_as_view(subContribMod.RHMaterialsAdd),
                        methods=('POST',))
event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/tools/', 'subContributionTools',
                        rh_as_view(subContribMod.RHSubContributionTools))
event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/tools/delete',
                        'subContributionTools-delete', rh_as_view(subContribMod.RHSubContributionDeletion),
                        methods=('GET', 'POST'))

# Paper reviewing - see the "paperreviewing" module
