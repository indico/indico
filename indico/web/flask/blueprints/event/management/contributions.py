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

from MaKaC.webinterface.rh import conferenceModif, contribMod, subContribMod
from indico.web.flask.blueprints.event.management import event_mgmt


# Contribution list
event_mgmt.add_url_rule('/contributions/', 'confModifContribList', conferenceModif.RHContributionList,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/direct-access', 'confModifContribList-contribQuickAccess',
                        conferenceModif.RHContribQuickAccess, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/perform-action', 'confModifContribList-contribsActions',
                        conferenceModif.RHContribsActions, methods=('POST',))
event_mgmt.add_url_rule('/contributions/pdf', 'confModifContribList-contribsToPDFMenu',
                        conferenceModif.RHContribsToPDFMenu, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/material-package', 'confModifContribList-matPkg',
                        conferenceModif.RHMaterialPackage, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/moveToSession', 'confModifContribList-moveToSession',
                        conferenceModif.RHMoveContribsToSession, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/participants', 'confModifContribList-participantList',
                        conferenceModif.RHContribsParticipantList, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/contributions/proceedings', 'confModifContribList-proceedings', conferenceModif.RHProceedings,
                        methods=('GET', 'POST'))

with event_mgmt.add_prefixed_rules('/session/<sessionId>'):
    # Main
    event_mgmt.add_url_rule('/contribution/<contribId>/', 'contributionModification',
                            contribMod.RHContributionModification)
    event_mgmt.add_url_rule('/contribution/<contribId>/contribution.xml', 'contributionModification-xml',
                            contribMod.RHContributionToXML)
    event_mgmt.add_url_rule('/contribution/<contribId>/contribution.pdf', 'contributionModification-pdf',
                            contribMod.RHContributionToPDF)
    event_mgmt.add_url_rule('/contribution/<contribId>/modify', 'contributionModification-data',
                            contribMod.RHContributionData, methods=('GET', 'POST'))
    event_mgmt.add_url_rule('/contribution/<contribId>/modify/save', 'contributionModification-modifData',
                            contribMod.RHContributionModifData, methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/change-track', 'contributionModification-setTrack',
                            contribMod.RHSetTrack, methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/change-session', 'contributionModification-setSession',
                            contribMod.RHSetSession, methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/withdraw', 'contributionModification-withdraw',
                            contribMod.RHWithdraw, methods=('POST',))

    # Material
    event_mgmt.add_url_rule('/contribution/<contribId>/material/', 'contributionModification-materials',
                            contribMod.RHMaterials, methods=('GET', 'POST'))
    event_mgmt.add_url_rule('/contribution/<contribId>/material/add', 'contributionModification-materialsAdd',
                            contribMod.RHMaterialsAdd, methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/material/browse/<materialId>',
                            'contributionModification-browseMaterial', contribMod.RHContribModifMaterialBrowse)

    # Protection
    event_mgmt.add_url_rule('/contribution/<contribId>/access/', 'contributionAC', contribMod.RHContributionAC,
                            methods=('GET', 'POST'))
    event_mgmt.add_url_rule('/contribution/<contribId>/access/visibility', 'contributionAC-setVisibility',
                            contribMod.RHContributionSetVisibility, methods=('POST',))

    # Tools
    event_mgmt.add_url_rule('/contribution/<contribId>/tools/', 'contributionTools', contribMod.RHContributionTools)
    event_mgmt.add_url_rule('/contribution/<contribId>/tools/delete', 'contributionTools-delete',
                            contribMod.RHContributionDeletion, methods=('GET', 'POST'))

    # Subcontributions
    event_mgmt.add_url_rule('/contribution/<contribId>/subcontributions/', 'contributionModifSubCont',
                            contribMod.RHContributionSC)
    event_mgmt.add_url_rule('/contribution/<contribId>/subcontributions/add', 'contributionModifSubCont-add',
                            contribMod.RHContributionAddSC, methods=('GET', 'POST'))
    event_mgmt.add_url_rule('/contribution/<contribId>/subcontributions/add/save', 'contributionModifSubCont-create',
                            contribMod.RHContributionCreateSC, methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/subcontributions/perform-action',
                            'contributionModifSubCont-actionSubContribs', contribMod.RHSubContribActions,
                            methods=('GET', 'POST'))

    # Subcontribution
    event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/', 'subContributionModification',
                            subContribMod.RHSubContributionModification, methods=('GET', 'POST'))
    event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/modify',
                            'subContributionModification-data', subContribMod.RHSubContributionData,
                            methods=('GET', 'POST'))
    event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/modify/save',
                            'subContributionModification-modifData', subContribMod.RHSubContributionModifData,
                            methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/material/',
                            'subContributionModification-materials', subContribMod.RHMaterials, methods=('GET', 'POST'))
    event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/material/add',
                            'subContributionModification-materialsAdd', subContribMod.RHMaterialsAdd, methods=('POST',))
    event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/tools/', 'subContributionTools',
                            subContribMod.RHSubContributionTools)
    event_mgmt.add_url_rule('/contribution/<contribId>/subcontribution/<subContId>/tools/delete',
                            'subContributionTools-delete', subContribMod.RHSubContributionDeletion,
                            methods=('GET', 'POST'))

# Paper reviewing - see the "paperreviewing" module
