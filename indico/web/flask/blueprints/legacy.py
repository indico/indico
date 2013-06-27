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

from indico.web.flask.util import rh_as_view
from indico.web.flask.wrappers import IndicoBlueprint

import MaKaC.webinterface.rh.abstractModif as mod_rh_abstractModif
import MaKaC.webinterface.rh.abstractReviewing as mod_rh_abstractReviewing
import MaKaC.webinterface.rh.collaboration as mod_rh_collaboration
import MaKaC.webinterface.rh.conferenceDisplay as mod_rh_conferenceDisplay
import MaKaC.webinterface.rh.conferenceModif as mod_rh_conferenceModif
import MaKaC.webinterface.rh.contribMod as mod_rh_contribMod
import MaKaC.webinterface.rh.contribReviewingModif as mod_rh_contribReviewingModif
import MaKaC.webinterface.rh.ePaymentModif as mod_rh_ePaymentModif
import MaKaC.webinterface.rh.evaluationModif as mod_rh_evaluationModif
import MaKaC.webinterface.rh.registrantsModif as mod_rh_registrantsModif
import MaKaC.webinterface.rh.registrationFormModif as mod_rh_registrationFormModif
import MaKaC.webinterface.rh.reviewingAssignContributions as mod_rh_reviewingAssignContributions
import MaKaC.webinterface.rh.reviewingControlModif as mod_rh_reviewingControlModif
import MaKaC.webinterface.rh.reviewingListContribToJudge as mod_rh_reviewingListContribToJudge
import MaKaC.webinterface.rh.reviewingModif as mod_rh_reviewingModif
import MaKaC.webinterface.rh.reviewingUserCompetencesModif as mod_rh_reviewingUserCompetencesModif
import MaKaC.webinterface.rh.sessionModif as mod_rh_sessionModif
import MaKaC.webinterface.rh.subContribDisplay as mod_rh_subContribDisplay
import MaKaC.webinterface.rh.subContribMod as mod_rh_subContribMod
import MaKaC.webinterface.rh.trackModif as mod_rh_trackModif
import MaKaC.webinterface.rh.users as mod_rh_users
import MaKaC.webinterface.rh.xmlGateway as mod_rh_xmlGateway


legacy = IndicoBlueprint('legacy', __name__)


# Routes for EMail.py
# Inactive: /EMail.py (mod_rh_conferenceDisplay.RHConferenceEmail)
# Inactive: /EMail.py/send (mod_rh_conferenceDisplay.RHConferenceSendEmail)

legacy.add_url_rule('/EMail.py/sendcontribparticipants',
                    'EMail-sendcontribparticipants',
                    rh_as_view(mod_rh_conferenceModif.RHContribParticipantsSendEmail),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/EMail.py/sendconvener',
                    'EMail-sendconvener',
                    rh_as_view(mod_rh_conferenceModif.RHConvenerSendEmail),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/EMail.py/sendreg',
                    'EMail-sendreg',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantSendEmail),
                    methods=('GET', 'POST'))


# Routes for JSContent.py
# Inactive: /JSContent.py/getVars (mod_rh_JSContent.RHGetVarsJs)


# Routes for about.py
# Inactive: /about.py (mod_rh_about.RHAbout)


# Routes for abstractDisplay.py
# Inactive: /abstractDisplay.py (mod_rh_CFADisplay.RHAbstractDisplay)
# Inactive: /abstractDisplay.py/getAttachedFile (mod_rh_CFADisplay.RHGetAttachedFile)
# Inactive: /abstractDisplay.py/pdf (mod_rh_CFADisplay.RHAbstractDisplayPDF)


# Routes for abstractManagment.py
legacy.add_url_rule('/abstractManagment.py',
                    'abstractManagment',
                    rh_as_view(mod_rh_abstractModif.RHAbstractManagment),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/abstractToPDF',
                    'abstractManagment-abstractToPDF',
                    rh_as_view(mod_rh_abstractModif.RHAbstractToPDF),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/ac',
                    'abstractManagment-ac',
                    rh_as_view(mod_rh_abstractModif.RHAC),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/accept',
                    'abstractManagment-accept',
                    rh_as_view(mod_rh_abstractModif.RHAbstractManagmentAccept),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/acceptMultiple',
                    'abstractManagment-acceptMultiple',
                    rh_as_view(mod_rh_conferenceModif.RHAbstractManagmentAcceptMultiple),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/backToSubmitted',
                    'abstractManagment-backToSubmitted',
                    rh_as_view(mod_rh_abstractModif.RHBackToSubmitted),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/changeTrack',
                    'abstractManagment-changeTrack',
                    rh_as_view(mod_rh_abstractModif.RHAbstractManagmentChangeTrack),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/comments',
                    'abstractManagment-comments',
                    rh_as_view(mod_rh_abstractModif.RHIntComments),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/directAccess',
                    'abstractManagment-directAccess',
                    rh_as_view(mod_rh_abstractModif.RHAbstractDirectAccess),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/editComment',
                    'abstractManagment-editComment',
                    rh_as_view(mod_rh_abstractModif.RHIntCommentEdit),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/editData',
                    'abstractManagment-editData',
                    rh_as_view(mod_rh_abstractModif.RHEditData),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/markAsDup',
                    'abstractManagment-markAsDup',
                    rh_as_view(mod_rh_abstractModif.RHMarkAsDup),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/mergeInto',
                    'abstractManagment-mergeInto',
                    rh_as_view(mod_rh_abstractModif.RHMergeInto),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/newComment',
                    'abstractManagment-newComment',
                    rh_as_view(mod_rh_abstractModif.RHNewIntComment),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/notifLog',
                    'abstractManagment-notifLog',
                    rh_as_view(mod_rh_abstractModif.RHNotifLog),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/orderByRating',
                    'abstractManagment-orderByRating',
                    rh_as_view(mod_rh_abstractModif.RHAbstractTrackOrderByRating),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/propToAcc',
                    'abstractManagment-propToAcc',
                    rh_as_view(mod_rh_abstractModif.RHPropToAcc),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/propToRej',
                    'abstractManagment-propToRej',
                    rh_as_view(mod_rh_abstractModif.RHPropToRej),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/reject',
                    'abstractManagment-reject',
                    rh_as_view(mod_rh_abstractModif.RHAbstractManagmentReject),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/rejectMultiple',
                    'abstractManagment-rejectMultiple',
                    rh_as_view(mod_rh_conferenceModif.RHAbstractManagmentRejectMultiple),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/remComment',
                    'abstractManagment-remComment',
                    rh_as_view(mod_rh_abstractModif.RHIntCommentRem),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/trackProposal',
                    'abstractManagment-trackProposal',
                    rh_as_view(mod_rh_abstractModif.RHAbstractTrackManagment),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/unMarkAsDup',
                    'abstractManagment-unMarkAsDup',
                    rh_as_view(mod_rh_abstractModif.RHUnMarkAsDup),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/unmerge',
                    'abstractManagment-unmerge',
                    rh_as_view(mod_rh_abstractModif.RHUnMerge),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/withdraw',
                    'abstractManagment-withdraw',
                    rh_as_view(mod_rh_abstractModif.RHWithdraw),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractManagment.py/xml',
                    'abstractManagment-xml',
                    rh_as_view(mod_rh_abstractModif.RHAbstractToXML),
                    methods=('GET', 'POST'))


# Routes for abstractModify.py
# Inactive: /abstractModify.py (mod_rh_CFADisplay.RHAbstractModify)


# Routes for abstractReviewing.py
legacy.add_url_rule('/abstractReviewing.py/notifTpl',
                    'abstractReviewing-notifTpl',
                    rh_as_view(mod_rh_abstractReviewing.RHNotifTpl),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractReviewing.py/notifTplCondNew',
                    'abstractReviewing-notifTplCondNew',
                    rh_as_view(mod_rh_abstractReviewing.RHNotifTplConditionNew),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractReviewing.py/notifTplCondRem',
                    'abstractReviewing-notifTplCondRem',
                    rh_as_view(mod_rh_abstractReviewing.RHNotifTplConditionRem),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractReviewing.py/notifTplDisplay',
                    'abstractReviewing-notifTplDisplay',
                    rh_as_view(mod_rh_abstractReviewing.RHCFANotifTplDisplay),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractReviewing.py/notifTplDown',
                    'abstractReviewing-notifTplDown',
                    rh_as_view(mod_rh_abstractReviewing.RHCFANotifTplDown),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractReviewing.py/notifTplEdit',
                    'abstractReviewing-notifTplEdit',
                    rh_as_view(mod_rh_abstractReviewing.RHCFANotifTplEdit),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractReviewing.py/notifTplNew',
                    'abstractReviewing-notifTplNew',
                    rh_as_view(mod_rh_abstractReviewing.RHCFANotifTplNew),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractReviewing.py/notifTplPreview',
                    'abstractReviewing-notifTplPreview',
                    rh_as_view(mod_rh_abstractReviewing.RHCFANotifTplPreview),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractReviewing.py/notifTplRem',
                    'abstractReviewing-notifTplRem',
                    rh_as_view(mod_rh_abstractReviewing.RHCFANotifTplRem),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractReviewing.py/notifTplUp',
                    'abstractReviewing-notifTplUp',
                    rh_as_view(mod_rh_abstractReviewing.RHCFANotifTplUp),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractReviewing.py/reviewingSetup',
                    'abstractReviewing-reviewingSetup',
                    rh_as_view(mod_rh_abstractReviewing.RHAbstractReviewingSetup),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractReviewing.py/reviewingTeam',
                    'abstractReviewing-reviewingTeam',
                    rh_as_view(mod_rh_abstractReviewing.RHAbstractReviewingTeam),
                    methods=('GET', 'POST'))


# Routes for abstractSubmission.py
# Inactive: /abstractSubmission.py (mod_rh_CFADisplay.RHAbstractSubmission)
# Inactive: /abstractSubmission.py/confirmation (mod_rh_CFADisplay.RHAbstractSubmissionConfirmation)


# Routes for abstractTools.py
legacy.add_url_rule('/abstractTools.py',
                    'abstractTools',
                    rh_as_view(mod_rh_abstractModif.RHTools),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractTools.py/delete',
                    'abstractTools-delete',
                    rh_as_view(mod_rh_abstractModif.RHAbstractDelete),
                    methods=('GET', 'POST'))


# Routes for abstractWithdraw.py
# Inactive: /abstractWithdraw.py (mod_rh_CFADisplay.RHAbstractWithdraw)
# Inactive: /abstractWithdraw.py/recover (mod_rh_CFADisplay.RHAbstractRecovery)


# Routes for abstractsManagment.py
legacy.add_url_rule('/abstractsManagment.py',
                    'abstractsManagment',
                    rh_as_view(mod_rh_conferenceModif.RHAbstractList),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractsManagment.py/abstractsActions',
                    'abstractsManagment-abstractsActions',
                    rh_as_view(mod_rh_conferenceModif.RHAbstractsActions),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractsManagment.py/mergeAbstracts',
                    'abstractsManagment-mergeAbstracts',
                    rh_as_view(mod_rh_conferenceModif.RHAbstractsMerge),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractsManagment.py/newAbstract',
                    'abstractsManagment-newAbstract',
                    rh_as_view(mod_rh_conferenceModif.RHNewAbstract),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/abstractsManagment.py/participantList',
                    'abstractsManagment-participantList',
                    rh_as_view(mod_rh_conferenceModif.RHAbstractsParticipantList),
                    methods=('GET', 'POST'))


# Routes for adminAnnouncement.py
# Inactive: /adminAnnouncement.py (mod_rh_announcement.RHAnnouncementModif)
# Inactive: /adminAnnouncement.py/save (mod_rh_announcement.RHAnnouncementModifSave)


# Routes for adminCollaboration.py
# Inactive: /adminCollaboration.py (mod_rh_collaboration.RHAdminCollaboration)


# Routes for adminConferenceStyles.py
# Inactive: /adminConferenceStyles.py (mod_rh_admins.RHConferenceStyles)


# Routes for adminLayout.py
# Inactive: /adminLayout.py (mod_rh_admins.RHAdminLayoutGeneral)
# Inactive: /adminLayout.py/addStyle (mod_rh_admins.RHAddStyle)
# Inactive: /adminLayout.py/deleteStyle (mod_rh_admins.RHDeleteStyle)
# Inactive: /adminLayout.py/saveSocial (mod_rh_admins.RHAdminLayoutSaveSocial)
# Inactive: /adminLayout.py/saveTemplateSet (mod_rh_admins.RHAdminLayoutSaveTemplateSet)
# Inactive: /adminLayout.py/setDefaultPDFOptions (mod_rh_templates.RHSetDefaultPDFOptions)
# Inactive: /adminLayout.py/styles (mod_rh_admins.RHStyles)


# Routes for adminList.py
# Inactive: /adminList.py (mod_rh_admins.RHAdminArea)
# Inactive: /adminList.py/switchCacheActive (mod_rh_admins.RHAdminSwitchCacheActive)
# Inactive: /adminList.py/switchDebugActive (mod_rh_admins.RHAdminSwitchDebugActive)
# Inactive: /adminList.py/switchNewsActive (mod_rh_admins.RHAdminSwitchNewsActive)


# Routes for adminMaintenance.py
# Inactive: /adminMaintenance.py (mod_rh_maintenance.RHMaintenance)
# Inactive: /adminMaintenance.py/pack (mod_rh_maintenance.RHMaintenancePack)
# Inactive: /adminMaintenance.py/performPack (mod_rh_maintenance.RHMaintenancePerformPack)
# Inactive: /adminMaintenance.py/performTmpCleanup (mod_rh_maintenance.RHMaintenancePerformTmpCleanup)
# Inactive: /adminMaintenance.py/tmpCleanup (mod_rh_maintenance.RHMaintenanceTmpCleanup)


# Routes for adminPlugins.py
# Inactive: /adminPlugins.py (mod_rh_admins.RHAdminPlugins)
# Inactive: /adminPlugins.py/clearAllInfo (mod_rh_admins.RHAdminPluginsClearAllInfo)
# Inactive: /adminPlugins.py/reload (mod_rh_admins.RHAdminPluginsReload)
# Inactive: /adminPlugins.py/reloadAll (mod_rh_admins.RHAdminPluginsReloadAll)
# Inactive: /adminPlugins.py/saveOptionReloadAll (mod_rh_admins.RHAdminPluginsSaveOptionReloadAll)
# Inactive: /adminPlugins.py/savePluginOptions (mod_rh_admins.RHAdminPluginsSaveOptions)
# Inactive: /adminPlugins.py/savePluginTypeOptions (mod_rh_admins.RHAdminPluginsSaveTypeOptions)
# Inactive: /adminPlugins.py/toggleActive (mod_rh_admins.RHAdminTogglePlugin)
# Inactive: /adminPlugins.py/toggleActivePluginType (mod_rh_admins.RHAdminTogglePluginType)


# Routes for adminProtection.py
# Inactive: /adminProtection.py (mod_rh_admins.RHAdminProtection)


# Routes for adminServices.py
# Inactive: /adminServices.py/analytics (mod_rh_services.RHAnalytics)
# Inactive: /adminServices.py/apiKeys (mod_rh_api.RHAdminAPIKeys)
# Inactive: /adminServices.py/apiOptions (mod_rh_api.RHAdminAPIOptions)
# Inactive: /adminServices.py/apiOptionsSet (mod_rh_api.RHAdminAPIOptionsSet)
# Inactive: /adminServices.py/ipbasedacl (mod_rh_services.RHIPBasedACL)
# Inactive: /adminServices.py/ipbasedacl_fagrant (mod_rh_services.RHIPBasedACLFullAccessGrant)
# Inactive: /adminServices.py/ipbasedacl_farevoke (mod_rh_services.RHIPBasedACLFullAccessRevoke)
# Inactive: /adminServices.py/oauthAuthorized (mod_rh_oauth.RHAdminOAuthAuthorized)
# Inactive: /adminServices.py/oauthConsumers (mod_rh_oauth.RHAdminOAuthConsumers)
# Inactive: /adminServices.py/saveAnalytics (mod_rh_services.RHSaveAnalytics)
# Inactive: /adminServices.py/webcast (mod_rh_services.RHWebcast)
# Inactive: /adminServices.py/webcastAddChannel (mod_rh_services.RHWebcastAddChannel)
# Inactive: /adminServices.py/webcastAddOnAir (mod_rh_services.RHWebcastAddOnAir)
# Inactive: /adminServices.py/webcastAddStream (mod_rh_services.RHWebcastAddStream)
# Inactive: /adminServices.py/webcastAddWebcast (mod_rh_services.RHWebcastAddWebcast)
# Inactive: /adminServices.py/webcastArchive (mod_rh_services.RHWebcastArchive)
# Inactive: /adminServices.py/webcastArchiveWebcast (mod_rh_services.RHWebcastArchiveWebcast)
# Inactive: /adminServices.py/webcastManualSynchronization (mod_rh_services.RHWebcastManuelSynchronizationURL)
# Inactive: /adminServices.py/webcastModifyChannel (mod_rh_services.RHWebcastModifyChannel)
# Inactive: /adminServices.py/webcastMoveChannelDown (mod_rh_services.RHWebcastMoveChannelDown)
# Inactive: /adminServices.py/webcastMoveChannelUp (mod_rh_services.RHWebcastMoveChannelUp)
# Inactive: /adminServices.py/webcastRemoveChannel (mod_rh_services.RHWebcastRemoveChannel)
# Inactive: /adminServices.py/webcastRemoveFromAir (mod_rh_services.RHWebcastRemoveFromAir)
# Inactive: /adminServices.py/webcastRemoveStream (mod_rh_services.RHWebcastRemoveStream)
# Inactive: /adminServices.py/webcastRemoveWebcast (mod_rh_services.RHWebcastRemoveWebcast)
# Inactive: /adminServices.py/webcastSaveWebcastSynchronizationURL (mod_rh_services.RHWebcastSaveWebcastSynchronizationURL)
# Inactive: /adminServices.py/webcastSetup (mod_rh_services.RHWebcastSetup)
# Inactive: /adminServices.py/webcastSwitchChannel (mod_rh_services.RHWebcastSwitchChannel)
# Inactive: /adminServices.py/webcastUnArchiveWebcast (mod_rh_services.RHWebcastUnArchiveWebcast)


# Routes for adminSystem.py
# Inactive: /adminSystem.py (mod_rh_admins.RHSystem)
# Inactive: /adminSystem.py/modify (mod_rh_admins.RHSystemModify)


# Routes for adminUpcomingEvents.py
# Inactive: /adminUpcomingEvents.py (mod_rh_admins.RHConfigUpcoming)


# Routes for assignContributions.py
legacy.add_url_rule('/assignContributions.py',
                    'assignContributions',
                    rh_as_view(mod_rh_reviewingAssignContributions.RHReviewingAssignContributionsList),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/assignContributions.py/downloadAcceptedPapers',
                    'assignContributions-downloadAcceptedPapers',
                    rh_as_view(mod_rh_reviewingAssignContributions.RHDownloadAcceptedPapers),
                    methods=('GET', 'POST'))


# Routes for badgeTemplates.py
# Inactive: /badgeTemplates.py (mod_rh_templates.RHBadgeTemplates)
# Inactive: /badgeTemplates.py/badgeDesign (mod_rh_templates.RHConfBadgeDesign)
# Inactive: /badgeTemplates.py/badgePrinting (mod_rh_templates.RHBadgeTemplates)


# Routes for categOverview.py
# Inactive: /categOverview.py (mod_rh_categoryDisplay.RHCategOverviewDisplay)
# Inactive: /categOverview.py/rss (mod_rh_categoryDisplay.RHTodayCategoryToRSS)


# Routes for categoryAC.py
# Inactive: /categoryAC.py (mod_rh_categoryMod.RHCategoryAC)
# Inactive: /categoryAC.py/setVisibility (mod_rh_categoryMod.RHCategorySetVisibility)


# Routes for categoryConfCreationControl.py
# Inactive: /categoryConfCreationControl.py/setCreateConferenceControl (mod_rh_categoryMod.RHCategorySetConfControl)
# Inactive: /categoryConfCreationControl.py/setNotifyCreation (mod_rh_categoryMod.RHCategorySetNotifyCreation)


# Routes for categoryCreation.py
# Inactive: /categoryCreation.py (mod_rh_categoryMod.RHCategoryCreation)
# Inactive: /categoryCreation.py/create (mod_rh_categoryMod.RHCategoryPerformCreation)


# Routes for categoryDataModification.py
# Inactive: /categoryDataModification.py (mod_rh_categoryMod.RHCategoryDataModif)
# Inactive: /categoryDataModification.py/modify (mod_rh_categoryMod.RHCategoryPerformModification)
# Inactive: /categoryDataModification.py/tasksOption (mod_rh_categoryMod.RHCategoryTaskOption)


# Routes for categoryDisplay.py
# Inactive: /categoryDisplay.py (mod_rh_categoryDisplay.RHCategoryDisplay)
# Inactive: /categoryDisplay.py/atom (mod_rh_categoryDisplay.RHCategoryToAtom)
# Inactive: /categoryDisplay.py/getIcon (mod_rh_categoryDisplay.RHCategoryGetIcon)
# Inactive: /categoryDisplay.py/ical (mod_rh_categoryDisplay.RHCategoryToiCal)
# Inactive: /categoryDisplay.py/rss (mod_rh_categoryDisplay.RHCategoryToRSS)


# Routes for categoryFiles.py
# Inactive: /categoryFiles.py (mod_rh_categoryMod.RHCategoryFiles)
# Inactive: /categoryFiles.py/addMaterial (mod_rh_categoryMod.RHAddMaterial)


# Routes for categoryMap.py
# Inactive: /categoryMap.py (mod_rh_categoryDisplay.RHCategoryMap)


# Routes for categoryModification.py
# Inactive: /categoryModification.py (mod_rh_categoryMod.RHCategoryModification)
# Inactive: /categoryModification.py/actionConferences (mod_rh_categoryMod.RHCategoryActionConferences)
# Inactive: /categoryModification.py/actionSubCategs (mod_rh_categoryMod.RHCategoryActionSubCategs)
# Inactive: /categoryModification.py/clearCache (mod_rh_categoryMod.RHCategoryClearCache)
# Inactive: /categoryModification.py/clearConferenceCaches (mod_rh_categoryMod.RHCategoryClearConferenceCaches)


# Routes for categoryStatistics.py
# Inactive: /categoryStatistics.py (mod_rh_categoryDisplay.RHCategoryStatistics)


# Routes for categoryTasks.py
# Inactive: /categoryTasks.py (mod_rh_categoryMod.RHCategoryTasks)
# Inactive: /categoryTasks.py/taskAction (mod_rh_categoryMod.RHCategoryTasksAction)


# Routes for categoryTools.py
# Inactive: /categoryTools.py (mod_rh_categoryMod.RHCategoryTools)
# Inactive: /categoryTools.py/delete (mod_rh_categoryMod.RHCategoryDeletion)


# Routes for changeLang.py
# Inactive: /changeLang.py (mod_rh_lang.RHChangeLang)


# Routes for collaborationDisplay.py
# Inactive: /collaborationDisplay.py (mod_rh_collaboration.RHCollaborationDisplay)


# Routes for confAbstractBook.py
# Inactive: /confAbstractBook.py (mod_rh_conferenceDisplay.RHAbstractBook)


# Routes for confAuthorIndex.py
# Inactive: /confAuthorIndex.py (mod_rh_conferenceDisplay.RHAuthorIndex)


# Routes for confDisplayEvaluation.py
# Inactive: /confDisplayEvaluation.py (mod_rh_evaluationDisplay.RHEvaluationMainInformation)
# Inactive: /confDisplayEvaluation.py/display (mod_rh_evaluationDisplay.RHEvaluationDisplay)
# Inactive: /confDisplayEvaluation.py/modif (mod_rh_evaluationDisplay.RHEvaluationDisplay)
# Inactive: /confDisplayEvaluation.py/signIn (mod_rh_evaluationDisplay.RHEvaluationSignIn)
# Inactive: /confDisplayEvaluation.py/submit (mod_rh_evaluationDisplay.RHEvaluationSubmit)
# Inactive: /confDisplayEvaluation.py/submitted (mod_rh_evaluationDisplay.RHEvaluationSubmitted)


# Routes for confListContribToJudge.py
legacy.add_url_rule('/confListContribToJudge.py',
                    'confListContribToJudge',
                    rh_as_view(mod_rh_reviewingListContribToJudge.RHContribListToJudge),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confListContribToJudge.py/asEditor',
                    'confListContribToJudge-asEditor',
                    rh_as_view(mod_rh_reviewingListContribToJudge.RHContribListToJudgeAsEditor),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confListContribToJudge.py/asReviewer',
                    'confListContribToJudge-asReviewer',
                    rh_as_view(mod_rh_reviewingListContribToJudge.RHContribListToJudgeAsReviewer),
                    methods=('GET', 'POST'))


# Routes for confLogin.py
# Inactive: /confLogin.py (mod_rh_conferenceDisplay.RHConfSignIn)
# Inactive: /confLogin.py/active (mod_rh_conferenceDisplay.RHConfActivate)
# Inactive: /confLogin.py/disabledAccount (mod_rh_conferenceDisplay.RHConfDisabledAccount)
# Inactive: /confLogin.py/sendActivation (mod_rh_conferenceDisplay.RHConfSendActivation)
# Inactive: /confLogin.py/sendLogin (mod_rh_conferenceDisplay.RHConfSendLogin)
# Inactive: /confLogin.py/unactivatedAccount (mod_rh_conferenceDisplay.RHConfUnactivatedAccount)


# Routes for confModBOA.py
legacy.add_url_rule('/confModBOA.py',
                    'confModBOA',
                    rh_as_view(mod_rh_conferenceModif.RHAbstractBook),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModBOA.py/edit',
                    'confModBOA-edit',
                    rh_as_view(mod_rh_conferenceModif.RHAbstractBookEdit),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModBOA.py/toogleShowIds',
                    'confModBOA-toogleShowIds',
                    rh_as_view(mod_rh_conferenceModif.RHAbstractBookToogleShowIds),
                    methods=('GET', 'POST'))


# Routes for confModifAC.py
legacy.add_url_rule('/confModifAC.py',
                    'confModifAC',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifAC),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifAC.py/grantModificationToAllConveners',
                    'confModifAC-grantModificationToAllConveners',
                    rh_as_view(mod_rh_conferenceModif.RHConfGrantModificationToAllConveners),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifAC.py/grantSubmissionToAllSpeakers',
                    'confModifAC-grantSubmissionToAllSpeakers',
                    rh_as_view(mod_rh_conferenceModif.RHConfGrantSubmissionToAllSpeakers),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifAC.py/modifySessionCoordRights',
                    'confModifAC-modifySessionCoordRights',
                    rh_as_view(mod_rh_conferenceModif.RHModifSessionCoordRights),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifAC.py/removeAllSubmissionRights',
                    'confModifAC-removeAllSubmissionRights',
                    rh_as_view(mod_rh_conferenceModif.RHConfRemoveAllSubmissionRights),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifAC.py/setVisibility',
                    'confModifAC-setVisibility',
                    rh_as_view(mod_rh_conferenceModif.RHConfSetVisibility),
                    methods=('GET', 'POST'))


# Routes for confModifCFA.py
legacy.add_url_rule('/confModifCFA.py',
                    'confModifCFA',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifCFA),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/absFieldDown',
                    'confModifCFA-absFieldDown',
                    rh_as_view(mod_rh_conferenceModif.RHConfMoveAbsFieldDown),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/absFieldUp',
                    'confModifCFA-absFieldUp',
                    rh_as_view(mod_rh_conferenceModif.RHConfMoveAbsFieldUp),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/abstractFields',
                    'confModifCFA-abstractFields',
                    rh_as_view(mod_rh_conferenceModif.RHConfAbstractFields),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/addAbstractField',
                    'confModifCFA-addAbstractField',
                    rh_as_view(mod_rh_conferenceModif.RHConfAddAbstractField),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/addType',
                    'confModifCFA-addType',
                    rh_as_view(mod_rh_conferenceModif.RHCFAAddType),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/changeStatus',
                    'confModifCFA-changeStatus',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifCFAStatus),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/editAbstractField',
                    'confModifCFA-editAbstractField',
                    rh_as_view(mod_rh_conferenceModif.RHConfEditAbstractField),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/makeTracksMandatory',
                    'confModifCFA-makeTracksMandatory',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifCFAMakeTracksMandatory),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/modifyData',
                    'confModifCFA-modifyData',
                    rh_as_view(mod_rh_conferenceModif.RHCFADataModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/performAddAbstractField',
                    'confModifCFA-performAddAbstractField',
                    rh_as_view(mod_rh_conferenceModif.RHConfPerformAddAbstractField),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/performModifyData',
                    'confModifCFA-performModifyData',
                    rh_as_view(mod_rh_conferenceModif.RHCFAPerformDataModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/preview',
                    'confModifCFA-preview',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifCFAPreview),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/removeAbstractField',
                    'confModifCFA-removeAbstractField',
                    rh_as_view(mod_rh_conferenceModif.RHConfRemoveAbstractField),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/removeType',
                    'confModifCFA-removeType',
                    rh_as_view(mod_rh_conferenceModif.RHCFARemoveType),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/switchAttachFiles',
                    'confModifCFA-switchAttachFiles',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifCFASwitchAttachFiles),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/switchMultipleTracks',
                    'confModifCFA-switchMultipleTracks',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifCFASwitchMultipleTracks),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/switchSelectSpeakerMandatory',
                    'confModifCFA-switchSelectSpeakerMandatory',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifCFASwitchSelectSpeakerMandatory),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/switchShowAttachedFiles',
                    'confModifCFA-switchShowAttachedFiles',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifCFASwitchShowAttachedFilesContribList),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCFA.py/switchShowSelectSpeaker',
                    'confModifCFA-switchShowSelectSpeaker',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifCFASwitchShowSelectAsSpeaker),
                    methods=('GET', 'POST'))


# Routes for confModifCollaboration.py
legacy.add_url_rule('/confModifCollaboration.py',
                    'confModifCollaboration',
                    rh_as_view(mod_rh_collaboration.RHConfModifCSBookings),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifCollaboration.py/managers',
                    'confModifCollaboration-managers',
                    rh_as_view(mod_rh_collaboration.RHConfModifCSProtection),
                    methods=('GET', 'POST'))


# Routes for confModifContribList.py
legacy.add_url_rule('/confModifContribList.py',
                    'confModifContribList',
                    rh_as_view(mod_rh_conferenceModif.RHContributionList),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifContribList.py/contribQuickAccess',
                    'confModifContribList-contribQuickAccess',
                    rh_as_view(mod_rh_conferenceModif.RHContribQuickAccess),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifContribList.py/contribsActions',
                    'confModifContribList-contribsActions',
                    rh_as_view(mod_rh_conferenceModif.RHContribsActions),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifContribList.py/contribsToPDF',
                    'confModifContribList-contribsToPDF',
                    rh_as_view(mod_rh_conferenceModif.RHContribsToPDF),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifContribList.py/contribsToPDFMenu',
                    'confModifContribList-contribsToPDFMenu',
                    rh_as_view(mod_rh_conferenceModif.RHContribsToPDFMenu),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifContribList.py/matPkg',
                    'confModifContribList-matPkg',
                    rh_as_view(mod_rh_conferenceModif.RHMaterialPackage),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifContribList.py/moveToSession',
                    'confModifContribList-moveToSession',
                    rh_as_view(mod_rh_conferenceModif.RHMoveContribsToSession),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifContribList.py/participantList',
                    'confModifContribList-participantList',
                    rh_as_view(mod_rh_conferenceModif.RHContribsParticipantList),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifContribList.py/proceedings',
                    'confModifContribList-proceedings',
                    rh_as_view(mod_rh_conferenceModif.RHProceedings),
                    methods=('GET', 'POST'))


# Routes for confModifDisplay.py
legacy.add_url_rule('/confModifDisplay.py',
                    'confModifDisplay',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayCustomization),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/addLink',
                    'confModifDisplay-addLink',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayAddLink),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/addPage',
                    'confModifDisplay-addPage',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayAddPage),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/addPageFile',
                    'confModifDisplay-addPageFile',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayAddPageFile),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/addPageFileBrowser',
                    'confModifDisplay-addPageFileBrowser',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayAddPageFileBrowser),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/addSpacer',
                    'confModifDisplay-addSpacer',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayAddSpacer),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/confHeader',
                    'confModifDisplay-confHeader',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayConfHeader),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/custom',
                    'confModifDisplay-custom',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayCustomization),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/downLink',
                    'confModifDisplay-downLink',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayDownLink),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/formatTitleBgColor',
                    'confModifDisplay-formatTitleBgColor',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifFormatTitleBgColor),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/formatTitleTextColor',
                    'confModifDisplay-formatTitleTextColor',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifFormatTitleTextColor),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/menu',
                    'confModifDisplay-menu',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayMenu),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/modifyData',
                    'confModifDisplay-modifyData',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayModifyData),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/modifySystemData',
                    'confModifDisplay-modifySystemData',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayModifySystemData),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/previewCSS',
                    'confModifDisplay-previewCSS',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifPreviewCSS),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/removeCSS',
                    'confModifDisplay-removeCSS',
                    rh_as_view(mod_rh_conferenceModif.RHConfRemoveCSS),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/removeLink',
                    'confModifDisplay-removeLink',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayRemoveLink),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/removeLogo',
                    'confModifDisplay-removeLogo',
                    rh_as_view(mod_rh_conferenceModif.RHConfRemoveLogo),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/resources',
                    'confModifDisplay-resources',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayResources),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/saveCSS',
                    'confModifDisplay-saveCSS',
                    rh_as_view(mod_rh_conferenceModif.RHConfSaveCSS),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/saveLogo',
                    'confModifDisplay-saveLogo',
                    rh_as_view(mod_rh_conferenceModif.RHConfSaveLogo),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/savePic',
                    'confModifDisplay-savePic',
                    rh_as_view(mod_rh_conferenceModif.RHConfSavePic),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/tickerTapeAction',
                    'confModifDisplay-tickerTapeAction',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifTickerTapeAction),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/toggleHomePage',
                    'confModifDisplay-toggleHomePage',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayToggleHomePage),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/toggleLinkStatus',
                    'confModifDisplay-toggleLinkStatus',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayToggleLinkStatus),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/toggleNavigationBar',
                    'confModifDisplay-toggleNavigationBar',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifToggleNavigationBar),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/toggleSearch',
                    'confModifDisplay-toggleSearch',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifToggleSearch),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/upLink',
                    'confModifDisplay-upLink',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifDisplayUpLink),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifDisplay.py/useCSS',
                    'confModifDisplay-useCSS',
                    rh_as_view(mod_rh_conferenceModif.RHConfUseCSS),
                    methods=('GET', 'POST'))


# Routes for confModifEpayment.py
legacy.add_url_rule('/confModifEpayment.py',
                    'confModifEpayment',
                    rh_as_view(mod_rh_ePaymentModif.RHEPaymentModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEpayment.py/changeStatus',
                    'confModifEpayment-changeStatus',
                    rh_as_view(mod_rh_ePaymentModif.RHEPaymentModifChangeStatus),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEpayment.py/dataModif',
                    'confModifEpayment-dataModif',
                    rh_as_view(mod_rh_ePaymentModif.RHEPaymentModifDataModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEpayment.py/enableSection',
                    'confModifEpayment-enableSection',
                    rh_as_view(mod_rh_ePaymentModif.RHEPaymentModifEnableSection),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEpayment.py/modifModule',
                    'confModifEpayment-modifModule',
                    rh_as_view(mod_rh_ePaymentModif.RHModifModule),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEpayment.py/performDataModif',
                    'confModifEpayment-performDataModif',
                    rh_as_view(mod_rh_ePaymentModif.RHEPaymentModifPerformDataModification),
                    methods=('GET', 'POST'))


# Routes for confModifEvaluation.py
legacy.add_url_rule('/confModifEvaluation.py',
                    'confModifEvaluation',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationSetup),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEvaluation.py/changeStatus',
                    'confModifEvaluation-changeStatus',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationSetupChangeStatus),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEvaluation.py/dataModif',
                    'confModifEvaluation-dataModif',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationSetupDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEvaluation.py/edit',
                    'confModifEvaluation-edit',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationEdit),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEvaluation.py/editPerformChanges',
                    'confModifEvaluation-editPerformChanges',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationEditPerformChanges),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEvaluation.py/performDataModif',
                    'confModifEvaluation-performDataModif',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationSetupPerformDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEvaluation.py/preview',
                    'confModifEvaluation-preview',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationPreview),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEvaluation.py/results',
                    'confModifEvaluation-results',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationResults),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEvaluation.py/resultsOptions',
                    'confModifEvaluation-resultsOptions',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationResultsOptions),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEvaluation.py/resultsSubmittersActions',
                    'confModifEvaluation-resultsSubmittersActions',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationResultsSubmittersActions),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEvaluation.py/setup',
                    'confModifEvaluation-setup',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationSetup),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifEvaluation.py/specialAction',
                    'confModifEvaluation-specialAction',
                    rh_as_view(mod_rh_evaluationModif.RHEvaluationSetupSpecialAction),
                    methods=('GET', 'POST'))


# Routes for confModifListings.py
legacy.add_url_rule('/confModifListings.py',
                    'confModifListings',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifListings),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifListings.py/allSessionsConveners',
                    'confModifListings-allSessionsConveners',
                    rh_as_view(mod_rh_conferenceModif.RHConfAllSessionsConveners),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifListings.py/allSpeakers',
                    'confModifListings-allSpeakers',
                    rh_as_view(mod_rh_conferenceModif.RHConfAllSpeakers),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifListings.py/allSpeakersAction',
                    'confModifListings-allSpeakersAction',
                    rh_as_view(mod_rh_conferenceModif.RHConfAllSpeakersAction),
                    methods=('GET', 'POST'))


# Routes for confModifLog.py
legacy.add_url_rule('/confModifLog.py',
                    'confModifLog',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifLog),
                    methods=('GET', 'POST'))


# Routes for confModifParticipants.py
legacy.add_url_rule('/confModifParticipants.py',
                    'confModifParticipants',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifParticipants),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifParticipants.py/action',
                    'confModifParticipants-action',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifParticipantsAction),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifParticipants.py/declinedParticipants',
                    'confModifParticipants-declinedParticipants',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifParticipantsDeclined),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifParticipants.py/invitation',
                    'confModifParticipants-invitation',
                    rh_as_view(mod_rh_conferenceDisplay.RHConfParticipantsInvitation),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifParticipants.py/pendingParticipants',
                    'confModifParticipants-pendingParticipants',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifParticipantsPending),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifParticipants.py/refusal',
                    'confModifParticipants-refusal',
                    rh_as_view(mod_rh_conferenceDisplay.RHConfParticipantsRefusal),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifParticipants.py/setup',
                    'confModifParticipants-setup',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifParticipantsSetup),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifParticipants.py/statistics',
                    'confModifParticipants-statistics',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifParticipantsStatistics),
                    methods=('GET', 'POST'))


# Routes for confModifPendingQueues.py
legacy.add_url_rule('/confModifPendingQueues.py',
                    'confModifPendingQueues',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifPendingQueues),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifPendingQueues.py/actionConfSubmitters',
                    'confModifPendingQueues-actionConfSubmitters',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifPendingQueuesActionConfSubm),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifPendingQueues.py/actionCoordinators',
                    'confModifPendingQueues-actionCoordinators',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifPendingQueuesActionCoord),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifPendingQueues.py/actionManagers',
                    'confModifPendingQueues-actionManagers',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifPendingQueuesActionMgr),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifPendingQueues.py/actionSubmitters',
                    'confModifPendingQueues-actionSubmitters',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifPendingQueuesActionSubm),
                    methods=('GET', 'POST'))


# Routes for confModifProgram.py
legacy.add_url_rule('/confModifProgram.py',
                    'confModifProgram',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifProgram),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifProgram.py/addTrack',
                    'confModifProgram-addTrack',
                    rh_as_view(mod_rh_conferenceModif.RHConfAddTrack),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifProgram.py/deleteTracks',
                    'confModifProgram-deleteTracks',
                    rh_as_view(mod_rh_conferenceModif.RHConfDelTracks),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifProgram.py/moveTrackDown',
                    'confModifProgram-moveTrackDown',
                    rh_as_view(mod_rh_conferenceModif.RHProgramTrackDown),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifProgram.py/moveTrackUp',
                    'confModifProgram-moveTrackUp',
                    rh_as_view(mod_rh_conferenceModif.RHProgramTrackUp),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifProgram.py/performAddTrack',
                    'confModifProgram-performAddTrack',
                    rh_as_view(mod_rh_conferenceModif.RHConfPerformAddTrack),
                    methods=('GET', 'POST'))


# Routes for confModifRegistrants.py
legacy.add_url_rule('/confModifRegistrants.py',
                    'confModifRegistrants',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantListModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/action',
                    'confModifRegistrants-action',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantListModifAction),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/closeMenu',
                    'confModifRegistrants-closeMenu',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantListMenuClose),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/getAttachedFile',
                    'confModifRegistrants-getAttachedFile',
                    rh_as_view(mod_rh_registrantsModif.RHGetAttachedFile),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/modification',
                    'confModifRegistrants-modification',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/modifyAccommodation',
                    'confModifRegistrants-modifyAccommodation',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantAccommodationModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/modifyMiscInfo',
                    'confModifRegistrants-modifyMiscInfo',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantMiscInfoModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/modifyReasonParticipation',
                    'confModifRegistrants-modifyReasonParticipation',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantReasonParticipationModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/modifySessions',
                    'confModifRegistrants-modifySessions',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantSessionModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/modifySocialEvents',
                    'confModifRegistrants-modifySocialEvents',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantSocialEventsModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/modifyStatuses',
                    'confModifRegistrants-modifyStatuses',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantStatusesModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/modifyTransaction',
                    'confModifRegistrants-modifyTransaction',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantTransactionModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/newRegistrant',
                    'confModifRegistrants-newRegistrant',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantNewForm),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/openMenu',
                    'confModifRegistrants-openMenu',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantListMenuOpen),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/peformModifyTransaction',
                    'confModifRegistrants-peformModifyTransaction',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantTransactionPerformModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/performModifyAccommodation',
                    'confModifRegistrants-performModifyAccommodation',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantAccommodationPerformModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/performModifyMiscInfo',
                    'confModifRegistrants-performModifyMiscInfo',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantMiscInfoPerformModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/performModifyReasonParticipation',
                    'confModifRegistrants-performModifyReasonParticipation',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantReasonParticipationPerformModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/performModifySessions',
                    'confModifRegistrants-performModifySessions',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantSessionPerformModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/performModifySocialEvents',
                    'confModifRegistrants-performModifySocialEvents',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantSocialEventsPerformModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/performModifyStatuses',
                    'confModifRegistrants-performModifyStatuses',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantStatusesPerformModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrants.py/remove',
                    'confModifRegistrants-remove',
                    rh_as_view(mod_rh_registrantsModif.RHRegistrantListRemove),
                    methods=('GET', 'POST'))


# Routes for confModifRegistrationForm.py
legacy.add_url_rule('/confModifRegistrationForm.py',
                    'confModifRegistrationForm',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/actionSection',
                    'confModifRegistrationForm-actionSection',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormActionSection),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/actionStatuses',
                    'confModifRegistrationForm-actionStatuses',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormActionStatuses),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/addAccommodationType',
                    'confModifRegistrationForm-addAccommodationType',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifAccommodationTypeAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/addGeneralField',
                    'confModifRegistrationForm-addGeneralField',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionFieldAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/addSession',
                    'confModifRegistrationForm-addSession',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSessionsAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/addSocialEvent',
                    'confModifRegistrationForm-addSocialEvent',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSocialEventAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/changeStatus',
                    'confModifRegistrationForm-changeStatus',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifChangeStatus),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/dataModif',
                    'confModifRegistrationForm-dataModif',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifDataModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/enablePersonalField',
                    'confModifRegistrationForm-enablePersonalField',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifEnablePersonalField),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/enableSection',
                    'confModifRegistrationForm-enableSection',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifEnableSection),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifAccommodation',
                    'confModifRegistrationForm-modifAccommodation',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifAccommodation),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifAccommodationData',
                    'confModifRegistrationForm-modifAccommodationData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifAccommodationDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifFurtherInformation',
                    'confModifRegistrationForm-modifFurtherInformation',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifFurtherInformation),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifFurtherInformationData',
                    'confModifRegistrationForm-modifFurtherInformationData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifFurtherInformationDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifGeneralField',
                    'confModifRegistrationForm-modifGeneralField',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionFieldModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifGeneralSection',
                    'confModifRegistrationForm-modifGeneralSection',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSection),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifGeneralSectionData',
                    'confModifRegistrationForm-modifGeneralSectionData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifReasonParticipation',
                    'confModifRegistrationForm-modifReasonParticipation',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifReasonParticipation),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifReasonParticipationData',
                    'confModifRegistrationForm-modifReasonParticipationData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifReasonParticipationDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifSessions',
                    'confModifRegistrationForm-modifSessions',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSessions),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifSessionsData',
                    'confModifRegistrationForm-modifSessionsData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSessionsDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifSocialEvent',
                    'confModifRegistrationForm-modifSocialEvent',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSocialEvent),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifSocialEventData',
                    'confModifRegistrationForm-modifSocialEventData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSocialEventDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifStatus',
                    'confModifRegistrationForm-modifStatus',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormStatusModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifyAccommodationType',
                    'confModifRegistrationForm-modifyAccommodationType',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormAccommodationTypeModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifySessionItem',
                    'confModifRegistrationForm-modifySessionItem',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormSessionItemModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/modifySocialEventItem',
                    'confModifRegistrationForm-modifySocialEventItem',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormSocialEventItemModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performAddAccommodationType',
                    'confModifRegistrationForm-performAddAccommodationType',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifAccommodationTypePerformAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performAddGeneralField',
                    'confModifRegistrationForm-performAddGeneralField',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionFieldPerformAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performAddSession',
                    'confModifRegistrationForm-performAddSession',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSessionsPerformAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performAddSocialEvent',
                    'confModifRegistrationForm-performAddSocialEvent',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSocialEventPerformAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performDataModif',
                    'confModifRegistrationForm-performDataModif',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifPerformDataModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performModifAccommodationData',
                    'confModifRegistrationForm-performModifAccommodationData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifAccommodationPerformDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performModifFurtherInformationData',
                    'confModifRegistrationForm-performModifFurtherInformationData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifFurtherInformationPerformDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performModifGeneralField',
                    'confModifRegistrationForm-performModifGeneralField',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionFieldPerformModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performModifGeneralSectionData',
                    'confModifRegistrationForm-performModifGeneralSectionData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionPerformDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performModifReasonParticipationData',
                    'confModifRegistrationForm-performModifReasonParticipationData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifReasonParticipationPerformDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performModifSessionsData',
                    'confModifRegistrationForm-performModifSessionsData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSessionsPerformDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performModifSocialEventData',
                    'confModifRegistrationForm-performModifSocialEventData',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSocialEventPerformDataModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performModifStatus',
                    'confModifRegistrationForm-performModifStatus',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifStatusPerformModif),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performModifyAccommodationType',
                    'confModifRegistrationForm-performModifyAccommodationType',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormAccommodationTypePerformModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performModifySessionItem',
                    'confModifRegistrationForm-performModifySessionItem',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormSessionItemPerformModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/performModifySocialEventItem',
                    'confModifRegistrationForm-performModifySocialEventItem',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormSocialEventItemPerformModify),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/removeAccommodationType',
                    'confModifRegistrationForm-removeAccommodationType',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifAccommodationTypeRemove),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/removeGeneralField',
                    'confModifRegistrationForm-removeGeneralField',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionFieldProcess),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/removeSession',
                    'confModifRegistrationForm-removeSession',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSessionsRemove),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifRegistrationForm.py/removeSocialEvent',
                    'confModifRegistrationForm-removeSocialEvent',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationFormModifSocialEventRemove),
                    methods=('GET', 'POST'))


# Routes for confModifRegistrationPreview.py
legacy.add_url_rule('/confModifRegistrationPreview.py',
                    'confModifRegistrationPreview',
                    rh_as_view(mod_rh_registrationFormModif.RHRegistrationPreview),
                    methods=('GET', 'POST'))


# Routes for confModifReviewing.py
legacy.add_url_rule('/confModifReviewing.py/access',
                    'confModifReviewing-access',
                    rh_as_view(mod_rh_reviewingModif.RHConfModifReviewingAccess),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifReviewing.py/addCriteria',
                    'confModifReviewing-addCriteria',
                    rh_as_view(mod_rh_reviewingModif.RHAddCriteria),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifReviewing.py/addQuestion',
                    'confModifReviewing-addQuestion',
                    rh_as_view(mod_rh_reviewingModif.RHAddQuestion),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifReviewing.py/addState',
                    'confModifReviewing-addState',
                    rh_as_view(mod_rh_reviewingModif.RHAddState),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifReviewing.py/chooseReviewing',
                    'confModifReviewing-chooseReviewing',
                    rh_as_view(mod_rh_reviewingModif.RHChooseReviewing),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifReviewing.py/deleteTemplate',
                    'confModifReviewing-deleteTemplate',
                    rh_as_view(mod_rh_reviewingModif.RHDeleteTemplate),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifReviewing.py/downloadTemplate',
                    'confModifReviewing-downloadTemplate',
                    rh_as_view(mod_rh_reviewingModif.RHDownloadTemplate),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifReviewing.py/paperSetup',
                    'confModifReviewing-paperSetup',
                    rh_as_view(mod_rh_reviewingModif.RHConfModifReviewingPaperSetup),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifReviewing.py/removeCriteria',
                    'confModifReviewing-removeCriteria',
                    rh_as_view(mod_rh_reviewingModif.RHRemoveCriteria),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifReviewing.py/removeQuestion',
                    'confModifReviewing-removeQuestion',
                    rh_as_view(mod_rh_reviewingModif.RHRemoveQuestion),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifReviewing.py/removeState',
                    'confModifReviewing-removeState',
                    rh_as_view(mod_rh_reviewingModif.RHRemoveState),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifReviewing.py/setTemplate',
                    'confModifReviewing-setTemplate',
                    rh_as_view(mod_rh_reviewingModif.RHSetTemplate),
                    methods=('GET', 'POST'))


# Routes for confModifReviewingControl.py
legacy.add_url_rule('/confModifReviewingControl.py',
                    'confModifReviewingControl',
                    rh_as_view(mod_rh_reviewingControlModif.RHConfModifReviewingControl),
                    methods=('GET', 'POST'))


# Routes for confModifSchedule.py
legacy.add_url_rule('/confModifSchedule.py',
                    'confModifSchedule',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifSchedule),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifSchedule.py/customizePdf',
                    'confModifSchedule-customizePdf',
                    rh_as_view(mod_rh_conferenceDisplay.RHTimeTableCustomizePDF),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifSchedule.py/edit',
                    'confModifSchedule-edit',
                    rh_as_view(mod_rh_conferenceModif.RHScheduleDataEdit),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifSchedule.py/pdf',
                    'confModifSchedule-pdf',
                    rh_as_view(mod_rh_conferenceDisplay.RHTimeTablePDF),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifSchedule.py/reschedule',
                    'confModifSchedule-reschedule',
                    rh_as_view(mod_rh_conferenceModif.RHReschedule),
                    methods=('GET', 'POST'))


# Routes for confModifTools.py
# Inactive: /confModifTools.py (mod_rh_conferenceModif.RHConfModifTools)
# Inactive: /confModifTools.py/addAlarm (mod_rh_conferenceModif.RHConfAddAlarm)

legacy.add_url_rule('/confModifTools.py/allSessionsConveners',
                    'confModifTools-allSessionsConveners',
                    rh_as_view(mod_rh_conferenceModif.RHConfAllSessionsConveners),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/allSessionsConvenersAction',
                    'confModifTools-allSessionsConvenersAction',
                    rh_as_view(mod_rh_conferenceModif.RHConfAllSessionsConvenersAction),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/badgeDesign',
                    'confModifTools-badgeDesign',
                    rh_as_view(mod_rh_conferenceModif.RHConfBadgeDesign),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/badgeGetBackground',
                    'confModifTools-badgeGetBackground',
                    rh_as_view(mod_rh_conferenceModif.RHConfBadgeGetBackground),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/badgePrinting',
                    'confModifTools-badgePrinting',
                    rh_as_view(mod_rh_conferenceModif.RHConfBadgePrinting),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/badgePrintingPDF',
                    'confModifTools-badgePrintingPDF',
                    rh_as_view(mod_rh_conferenceModif.RHConfBadgePrintingPDF),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/badgeSaveBackground',
                    'confModifTools-badgeSaveBackground',
                    rh_as_view(mod_rh_conferenceModif.RHConfBadgeSaveTempBackground),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/clone',
                    'confModifTools-clone',
                    rh_as_view(mod_rh_conferenceModif.RHConfClone),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/delete',
                    'confModifTools-delete',
                    rh_as_view(mod_rh_conferenceModif.RHConfDeletion),
                    methods=('GET', 'POST'))
# Inactive: /confModifTools.py/deleteAlarm (mod_rh_conferenceModif.RHConfDeleteAlarm)
# Inactive: /confModifTools.py/displayAlarm (mod_rh_conferenceModif.RHConfDisplayAlarm)

legacy.add_url_rule('/confModifTools.py/dvdCreation',
                    'confModifTools-dvdCreation',
                    rh_as_view(mod_rh_conferenceModif.RHConfDVDCreation),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/dvdDone',
                    'confModifTools-dvdDone',
                    rh_as_view(mod_rh_conferenceModif.RHConfDVDDone),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/matPkg',
                    'confModifTools-matPkg',
                    rh_as_view(mod_rh_conferenceModif.RHFullMaterialPackage),
                    methods=('GET', 'POST'))
# Inactive: /confModifTools.py/modifyAlarm (mod_rh_conferenceModif.RHConfModifyAlarm)

legacy.add_url_rule('/confModifTools.py/performCloning',
                    'confModifTools-performCloning',
                    rh_as_view(mod_rh_conferenceModif.RHConfPerformCloning),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/performMatPkg',
                    'confModifTools-performMatPkg',
                    rh_as_view(mod_rh_conferenceModif.RHFullMaterialPackagePerform),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/posterDesign',
                    'confModifTools-posterDesign',
                    rh_as_view(mod_rh_conferenceModif.RHConfPosterDesign),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/posterGetBackground',
                    'confModifTools-posterGetBackground',
                    rh_as_view(mod_rh_conferenceModif.RHConfPosterGetBackground),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/posterPrinting',
                    'confModifTools-posterPrinting',
                    rh_as_view(mod_rh_conferenceModif.RHConfPosterPrinting),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/posterPrintingPDF',
                    'confModifTools-posterPrintingPDF',
                    rh_as_view(mod_rh_conferenceModif.RHConfPosterPrintingPDF),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/posterSaveBackground',
                    'confModifTools-posterSaveBackground',
                    rh_as_view(mod_rh_conferenceModif.RHConfPosterSaveTempBackground),
                    methods=('GET', 'POST'))
# Inactive: /confModifTools.py/saveAlarm (mod_rh_conferenceModif.RHConfSaveAlarm)
# Inactive: /confModifTools.py/sendAlarmNow (mod_rh_conferenceModif.RHConfSendAlarmNow)


# Routes for confModifUserCompetences.py
legacy.add_url_rule('/confModifUserCompetences.py',
                    'confModifUserCompetences',
                    rh_as_view(mod_rh_reviewingUserCompetencesModif.RHConfModifUserCompetences),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifUserCompetences.py/Abstracts',
                    'confModifUserCompetences-Abstracts',
                    rh_as_view(mod_rh_reviewingUserCompetencesModif.RHConfModifUserCompetencesAbstracts),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifUserCompetences.py/modifyCompetences',
                    'confModifUserCompetences-modifyCompetences',
                    rh_as_view(mod_rh_reviewingUserCompetencesModif.RHConfModifModifyUserCompetences),
                    methods=('GET', 'POST'))


# Routes for confRegistrantsDisplay.py
# Inactive: /confRegistrantsDisplay.py/list (mod_rh_registrantsDisplay.RHRegistrantsList)


# Routes for confRegistrationFormDisplay.py
# Inactive: /confRegistrationFormDisplay.py (mod_rh_registrationFormDisplay.RHRegistrationForm)
# Inactive: /confRegistrationFormDisplay.py/conditions (mod_rh_registrationFormDisplay.RHRegistrationFormConditions)
# Inactive: /confRegistrationFormDisplay.py/confirmBooking (mod_rh_registrationFormDisplay.RHRegistrationFormconfirmBooking)
# Inactive: /confRegistrationFormDisplay.py/confirmBookingDone (mod_rh_registrationFormDisplay.RHRegistrationFormconfirmBookingDone)
# Inactive: /confRegistrationFormDisplay.py/creation (mod_rh_registrationFormDisplay.RHRegistrationFormCreation)
# Inactive: /confRegistrationFormDisplay.py/creationDone (mod_rh_registrationFormDisplay.RHRegistrationFormCreationDone)
# Inactive: /confRegistrationFormDisplay.py/display (mod_rh_registrationFormDisplay.RHRegistrationFormDisplay)
# Inactive: /confRegistrationFormDisplay.py/modify (mod_rh_registrationFormDisplay.RHRegistrationFormModify)
# Inactive: /confRegistrationFormDisplay.py/performModify (mod_rh_registrationFormDisplay.RHRegistrationFormPerformModify)
# Inactive: /confRegistrationFormDisplay.py/signIn (mod_rh_registrationFormDisplay.RHRegistrationFormSignIn)


# Routes for confSpeakerIndex.py
# Inactive: /confSpeakerIndex.py (mod_rh_conferenceDisplay.RHSpeakerIndex)


# Routes for confUser.py
# Inactive: /confUser.py (mod_rh_conferenceDisplay.RHConfUserCreation)
# Inactive: /confUser.py/created (mod_rh_conferenceDisplay.RHConfUserCreated)
# Inactive: /confUser.py/userExists (mod_rh_conferenceDisplay.RHConfUserExistWithIdentity)


# Routes for conferenceCFA.py
# Inactive: /conferenceCFA.py (mod_rh_CFADisplay.RHConferenceCFA)


# Routes for conferenceCreation.py
# Inactive: /conferenceCreation.py (mod_rh_categoryDisplay.RHConferenceCreation)
# Inactive: /conferenceCreation.py/createConference (mod_rh_categoryDisplay.RHConferencePerformCreation)


# Routes for conferenceDisplay.py
# Inactive: /conferenceDisplay.py (mod_rh_conferenceDisplay.RHConferenceDisplay)
# Inactive: /conferenceDisplay.py/abstractBook (mod_rh_conferenceDisplay.RHAbstractBook)
# Inactive: /conferenceDisplay.py/abstractBookLatex (mod_rh_conferenceDisplay.RHConferenceLatexPackage)
# Inactive: /conferenceDisplay.py/accessKey (mod_rh_conferenceDisplay.RHConferenceAccessKey)
# Inactive: /conferenceDisplay.py/getCSS (mod_rh_conferenceDisplay.RHConferenceGetCSS)
# Inactive: /conferenceDisplay.py/getLogo (mod_rh_conferenceDisplay.RHConferenceGetLogo)
# Inactive: /conferenceDisplay.py/getPic (mod_rh_conferenceDisplay.RHConferenceGetPic)
# Inactive: /conferenceDisplay.py/ical (mod_rh_conferenceDisplay.RHConferenceToiCal)
# Inactive: /conferenceDisplay.py/marcxml (mod_rh_conferenceDisplay.RHConferenceToMarcXML)
# Inactive: /conferenceDisplay.py/matPkg (mod_rh_conferenceDisplay.RHFullMaterialPackage)
# Inactive: /conferenceDisplay.py/next (mod_rh_conferenceDisplay.RHRelativeEvent)
# Inactive: /conferenceDisplay.py/performMatPkg (mod_rh_conferenceDisplay.RHFullMaterialPackagePerform)
# Inactive: /conferenceDisplay.py/prev (mod_rh_conferenceDisplay.RHRelativeEvent)
# Inactive: /conferenceDisplay.py/xml (mod_rh_conferenceDisplay.RHConferenceToXML)


# Routes for conferenceModification.py
# Inactive: /conferenceModification.py (mod_rh_conferenceModif.RHConferenceModification)
# Inactive: /conferenceModification.py/addContribType (mod_rh_conferenceModif.RHConfAddContribType)

legacy.add_url_rule('/conferenceModification.py/close',
                    'conferenceModification-close',
                    rh_as_view(mod_rh_conferenceModif.RHConferenceClose),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/closeModifKey',
                    'conferenceModification-closeModifKey',
                    rh_as_view(mod_rh_conferenceModif.RHConferenceCloseModifKey),
                    methods=('GET', 'POST'))
# Inactive: /conferenceModification.py/data (mod_rh_conferenceModif.RHConfDataModif)
# Inactive: /conferenceModification.py/dataPerform (mod_rh_conferenceModif.RHConfPerformDataModif)
# Inactive: /conferenceModification.py/editContribType (mod_rh_conferenceModif.RHConfEditContribType)
# Inactive: /conferenceModification.py/managementAccess (mod_rh_conferenceModif.RHConferenceModifManagementAccess)

legacy.add_url_rule('/conferenceModification.py/materialsAdd',
                    'conferenceModification-materialsAdd',
                    rh_as_view(mod_rh_conferenceModif.RHMaterialsAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/materialsShow',
                    'conferenceModification-materialsShow',
                    rh_as_view(mod_rh_conferenceModif.RHMaterialsShow),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/modifKey',
                    'conferenceModification-modifKey',
                    rh_as_view(mod_rh_conferenceModif.RHConferenceModifKey),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/modificationClosed',
                    'conferenceModification-modificationClosed',
                    rh_as_view(mod_rh_conferenceModif.RHConferenceModificationClosed),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/open',
                    'conferenceModification-open',
                    rh_as_view(mod_rh_conferenceModif.RHConferenceOpen),
                    methods=('GET', 'POST'))
# Inactive: /conferenceModification.py/removeContribType (mod_rh_conferenceModif.RHConfRemoveContribType)

legacy.add_url_rule('/conferenceModification.py/roomBookingBookingForm',
                    'conferenceModification-roomBookingBookingForm',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifRoomBookingBookingForm),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/roomBookingChooseEvent',
                    'conferenceModification-roomBookingChooseEvent',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifRoomBookingChooseEvent),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/roomBookingCloneBooking',
                    'conferenceModification-roomBookingCloneBooking',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifRoomBookingCloneBooking),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/roomBookingDetails',
                    'conferenceModification-roomBookingDetails',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifRoomBookingDetails),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/roomBookingList',
                    'conferenceModification-roomBookingList',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifRoomBookingList),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/roomBookingRoomDetails',
                    'conferenceModification-roomBookingRoomDetails',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifRoomBookingRoomDetails),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/roomBookingRoomList',
                    'conferenceModification-roomBookingRoomList',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifRoomBookingRoomList),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/roomBookingSaveBooking',
                    'conferenceModification-roomBookingSaveBooking',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifRoomBookingSaveBooking),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/roomBookingSearch4Rooms',
                    'conferenceModification-roomBookingSearch4Rooms',
                    rh_as_view(mod_rh_conferenceModif.RHConfModifRoomBookingSearch4Rooms),
                    methods=('GET', 'POST'))
# Inactive: /conferenceModification.py/screenDates (mod_rh_conferenceModif.RHConfScreenDatesEdit)

legacy.add_url_rule('/conferenceModification.py/sectionsSettings',
                    'conferenceModification-sectionsSettings',
                    rh_as_view(mod_rh_conferenceModif.RHConfSectionsSettings),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/conferenceModification.py/sessionSlots',
                    'conferenceModification-sessionSlots',
                    rh_as_view(mod_rh_conferenceModif.RHConfSessionSlots),
                    methods=('GET', 'POST'))


# Routes for conferenceOtherViews.py
# Inactive: /conferenceOtherViews.py (mod_rh_conferenceDisplay.RHConferenceOtherViews)


# Routes for conferenceProgram.py
# Inactive: /conferenceProgram.py (mod_rh_conferenceDisplay.RHConferenceProgram)
# Inactive: /conferenceProgram.py/pdf (mod_rh_conferenceDisplay.RHConferenceProgramPDF)


# Routes for conferenceTimeTable.py
# Inactive: /conferenceTimeTable.py (mod_rh_conferenceDisplay.RHConferenceTimeTable)
# Inactive: /conferenceTimeTable.py/customizePdf (mod_rh_conferenceDisplay.RHTimeTableCustomizePDF)
# Inactive: /conferenceTimeTable.py/pdf (mod_rh_conferenceDisplay.RHTimeTablePDF)


# Routes for contact.py
# Inactive: /contact.py (mod_rh_contact.RHContact)


# Routes for contribAuthorDisplay.py
# Inactive: /contribAuthorDisplay.py (mod_rh_authorDisplay.RHAuthorDisplay)


# Routes for contributionAC.py
legacy.add_url_rule('/contributionAC.py',
                    'contributionAC',
                    rh_as_view(mod_rh_contribMod.RHContributionAC),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionAC.py/setVisibility',
                    'contributionAC-setVisibility',
                    rh_as_view(mod_rh_contribMod.RHContributionSetVisibility),
                    methods=('GET', 'POST'))


# Routes for contributionDisplay.py
# Inactive: /contributionDisplay.py (mod_rh_contribDisplay.RHContributionDisplay)
# Inactive: /contributionDisplay.py/ical (mod_rh_contribDisplay.RHContributionToiCal)
# Inactive: /contributionDisplay.py/marcxml (mod_rh_contribDisplay.RHContributionToMarcXML)
# Inactive: /contributionDisplay.py/pdf (mod_rh_contribDisplay.RHContributionToPDF)
# Inactive: /contributionDisplay.py/xml (mod_rh_contribDisplay.RHContributionToXML)


# Routes for contributionEditingJudgement.py
legacy.add_url_rule('/contributionEditingJudgement.py',
                    'contributionEditingJudgement',
                    rh_as_view(mod_rh_contribReviewingModif.RHContributionEditingJudgement),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionEditingJudgement.py/judgeEditing',
                    'contributionEditingJudgement-judgeEditing',
                    rh_as_view(mod_rh_contribReviewingModif.RHJudgeEditing),
                    methods=('GET', 'POST'))


# Routes for contributionGiveAdvice.py
legacy.add_url_rule('/contributionGiveAdvice.py',
                    'contributionGiveAdvice',
                    rh_as_view(mod_rh_contribReviewingModif.RHContributionGiveAdvice),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionGiveAdvice.py/giveAdvice',
                    'contributionGiveAdvice-giveAdvice',
                    rh_as_view(mod_rh_contribReviewingModif.RHGiveAdvice),
                    methods=('GET', 'POST'))


# Routes for contributionListDisplay.py
# Inactive: /contributionListDisplay.py (mod_rh_conferenceDisplay.RHContributionList)
# Inactive: /contributionListDisplay.py/contributionsToPDF (mod_rh_conferenceDisplay.RHContributionListToPDF)


# Routes for contributionModifSubCont.py
legacy.add_url_rule('/contributionModifSubCont.py',
                    'contributionModifSubCont',
                    rh_as_view(mod_rh_contribMod.RHContributionSC),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModifSubCont.py/Down',
                    'contributionModifSubCont-Down',
                    rh_as_view(mod_rh_contribMod.RHContributionDownSC),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModifSubCont.py/actionSubContribs',
                    'contributionModifSubCont-actionSubContribs',
                    rh_as_view(mod_rh_contribMod.RHSubContribActions),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModifSubCont.py/add',
                    'contributionModifSubCont-add',
                    rh_as_view(mod_rh_contribMod.RHContributionAddSC),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModifSubCont.py/create',
                    'contributionModifSubCont-create',
                    rh_as_view(mod_rh_contribMod.RHContributionCreateSC),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModifSubCont.py/setVisibility',
                    'contributionModifSubCont-setVisibility',
                    rh_as_view(mod_rh_contribMod.RHContributionSetVisibility),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModifSubCont.py/up',
                    'contributionModifSubCont-up',
                    rh_as_view(mod_rh_contribMod.RHContributionUpSC),
                    methods=('GET', 'POST'))


# Routes for contributionModification.py
legacy.add_url_rule('/contributionModification.py',
                    'contributionModification',
                    rh_as_view(mod_rh_contribMod.RHContributionModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/addMaterial',
                    'contributionModification-addMaterial',
                    rh_as_view(mod_rh_contribMod.RHContributionAddMaterial),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/browseMaterial',
                    'contributionModification-browseMaterial',
                    rh_as_view(mod_rh_contribMod.RHContribModifMaterialBrowse),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/data',
                    'contributionModification-data',
                    rh_as_view(mod_rh_contribMod.RHContributionData),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/materials',
                    'contributionModification-materials',
                    rh_as_view(mod_rh_contribMod.RHMaterials),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/materialsAdd',
                    'contributionModification-materialsAdd',
                    rh_as_view(mod_rh_contribMod.RHMaterialsAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/modifData',
                    'contributionModification-modifData',
                    rh_as_view(mod_rh_contribMod.RHContributionModifData),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/pdf',
                    'contributionModification-pdf',
                    rh_as_view(mod_rh_contribMod.RHContributionToPDF),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/performAddMaterial',
                    'contributionModification-performAddMaterial',
                    rh_as_view(mod_rh_contribMod.RHContributionPerformAddMaterial),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/performMove',
                    'contributionModification-performMove',
                    rh_as_view(mod_rh_contribMod.RHContributionPerformMove),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/removeMaterials',
                    'contributionModification-removeMaterials',
                    rh_as_view(mod_rh_contribMod.RHContributionRemoveMaterials),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/setSession',
                    'contributionModification-setSession',
                    rh_as_view(mod_rh_contribMod.RHSetSession),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/setTrack',
                    'contributionModification-setTrack',
                    rh_as_view(mod_rh_contribMod.RHSetTrack),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/withdraw',
                    'contributionModification-withdraw',
                    rh_as_view(mod_rh_contribMod.RHWithdraw),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionModification.py/xml',
                    'contributionModification-xml',
                    rh_as_view(mod_rh_contribMod.RHContributionToXML),
                    methods=('GET', 'POST'))


# Routes for contributionReviewing.py
legacy.add_url_rule('/contributionReviewing.py',
                    'contributionReviewing',
                    rh_as_view(mod_rh_contribReviewingModif.RHContributionReviewing),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/assignEditing',
                    'contributionReviewing-assignEditing',
                    rh_as_view(mod_rh_contribReviewingModif.RHAssignEditing),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/assignReferee',
                    'contributionReviewing-assignReferee',
                    rh_as_view(mod_rh_contribReviewingModif.RHAssignReferee),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/assignReviewing',
                    'contributionReviewing-assignReviewing',
                    rh_as_view(mod_rh_contribReviewingModif.RHAssignReviewing),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/contributionReviewingJudgements',
                    'contributionReviewing-contributionReviewingJudgements',
                    rh_as_view(mod_rh_contribReviewingModif.RHContributionReviewingJudgements),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/contributionReviewingMaterials',
                    'contributionReviewing-contributionReviewingMaterials',
                    rh_as_view(mod_rh_contribReviewingModif.RHContribModifReviewingMaterials),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/editorDueDate',
                    'contributionReviewing-editorDueDate',
                    rh_as_view(mod_rh_contribReviewingModif.RHEditorDueDate),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/finalJudge',
                    'contributionReviewing-finalJudge',
                    rh_as_view(mod_rh_contribReviewingModif.RHFinalJudge),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/refereeDueDate',
                    'contributionReviewing-refereeDueDate',
                    rh_as_view(mod_rh_contribReviewingModif.RHRefereeDueDate),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/removeAssignEditing',
                    'contributionReviewing-removeAssignEditing',
                    rh_as_view(mod_rh_contribReviewingModif.RHRemoveAssignEditing),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/removeAssignReferee',
                    'contributionReviewing-removeAssignReferee',
                    rh_as_view(mod_rh_contribReviewingModif.RHRemoveAssignReferee),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/removeAssignReviewing',
                    'contributionReviewing-removeAssignReviewing',
                    rh_as_view(mod_rh_contribReviewingModif.RHRemoveAssignReviewing),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/reviewerDueDate',
                    'contributionReviewing-reviewerDueDate',
                    rh_as_view(mod_rh_contribReviewingModif.RHReviewerDueDate),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionReviewing.py/reviewingHistory',
                    'contributionReviewing-reviewingHistory',
                    rh_as_view(mod_rh_contribReviewingModif.RHReviewingHistory),
                    methods=('GET', 'POST'))


# Routes for contributionTools.py
legacy.add_url_rule('/contributionTools.py',
                    'contributionTools',
                    rh_as_view(mod_rh_contribMod.RHContributionTools),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/contributionTools.py/delete',
                    'contributionTools-delete',
                    rh_as_view(mod_rh_contribMod.RHContributionDeletion),
                    methods=('GET', 'POST'))


# Routes for domainCreation.py
# Inactive: /domainCreation.py (mod_rh_domains.RHDomainCreation)
# Inactive: /domainCreation.py/create (mod_rh_domains.RHDomainPerformCreation)


# Routes for domainDataModification.py
# Inactive: /domainDataModification.py (mod_rh_domains.RHDomainModification)
# Inactive: /domainDataModification.py/modify (mod_rh_domains.RHDomainPerformModification)


# Routes for domainDetails.py
# Inactive: /domainDetails.py (mod_rh_domains.RHDomainDetails)


# Routes for domainList.py
# Inactive: /domainList.py (mod_rh_domains.RHDomains)


# Routes for errors.py
# Inactive: /errors.py (mod_rh_errors.RHErrorReporting)


# Routes for generalInfoModification.py
# Inactive: /generalInfoModification.py (mod_rh_admins.RHGeneralInfoModification)
# Inactive: /generalInfoModification.py/update (mod_rh_admins.RHGeneralInfoPerformModification)


# Routes for getConvertedFile.py
# Inactive: /getConvertedFile.py (mod_rh_materialDisplay.RHMaterialAddConvertedFile)


# Routes for getFile.py
# Inactive: /getFile.py/access (mod_rh_fileAccess.RHFileAccess)
# Inactive: /getFile.py/accessKey (mod_rh_fileAccess.RHFileAccessStoreAccessKey)
# Inactive: /getFile.py/flash (mod_rh_fileAccess.RHVideoFlashAccess)
# Inactive: /getFile.py/wmv (mod_rh_fileAccess.RHVideoWmvAccess)


# Routes for groupDetails.py
# Inactive: /groupDetails.py (mod_rh_groups.RHGroupDetails)


# Routes for groupList.py
# Inactive: /groupList.py (mod_rh_groups.RHGroups)


# Routes for groupModification.py
# Inactive: /groupModification.py (mod_rh_groups.RHGroupModification)
# Inactive: /groupModification.py/update (mod_rh_groups.RHGroupPerformModification)


# Routes for groupRegistration.py
# Inactive: /groupRegistration.py (mod_rh_groups.RHGroupCreation)
# Inactive: /groupRegistration.py/update (mod_rh_groups.RHGroupPerformCreation)


# Routes for help.py
# Inactive: /help.py (mod_rh_helpDisplay.RHHelp)


# Routes for identityCreation.py
# Inactive: /identityCreation.py (mod_rh_users.RHUserIdentityCreation)
# Inactive: /identityCreation.py/changePassword (mod_rh_users.RHUserIdentityChangePassword)
# Inactive: /identityCreation.py/create (mod_rh_users.RHUserIdentityCreation)
# Inactive: /identityCreation.py/remove (mod_rh_users.RHUserRemoveIdentity)


# Routes for index.py
# Inactive: /index.py (mod_rh_welcome.RHWelcome)


# Routes for internalPage.py
# Inactive: /internalPage.py (mod_rh_conferenceDisplay.RHInternalPageDisplay)


# Routes for logOut.py
# Inactive: /logOut.py (mod_rh_login.RHSignOut)


# Routes for logoutSSOHook.py
# Inactive: /logoutSSOHook.py (mod_rh_login.RHLogoutSSOHook)


# Routes for materialDisplay.py
# Inactive: /materialDisplay.py (mod_rh_materialDisplay.RHMaterialDisplay)
# Inactive: /materialDisplay.py/accessKey (mod_rh_materialDisplay.RHMaterialDisplayStoreAccessKey)


# Routes for myconference.py
# Inactive: /myconference.py (mod_rh_conferenceDisplay.RHMyStuff)
# Inactive: /myconference.py/myContributions (mod_rh_conferenceDisplay.RHConfMyStuffMyContributions)
# Inactive: /myconference.py/mySessions (mod_rh_conferenceDisplay.RHConfMyStuffMySessions)
# Inactive: /myconference.py/myTracks (mod_rh_conferenceDisplay.RHConfMyStuffMyTracks)


# Routes for news.py
# Inactive: /news.py (mod_rh_newsDisplay.RHNews)


# Routes for oauth.py
# Inactive: /oauth.py/access_token (mod_rh_oauth.RHOAuthAccessTokenURL)
# Inactive: /oauth.py/authorize (mod_rh_oauth.RHOAuthAuthorization)
# Inactive: /oauth.py/authorize_consumer (mod_rh_oauth.RHOAuthAuthorizeConsumer)
# Inactive: /oauth.py/request_token (mod_rh_oauth.RHOAuthRequestToken)
# Inactive: /oauth.py/thirdPartyAuth (mod_rh_oauth.RHOAuthThirdPartyAuth)
# Inactive: /oauth.py/userThirdPartyAuth (mod_rh_oauth.RHOAuthUserThirdPartyAuth)


# Routes for paperReviewingDisplay.py
# Inactive: /paperReviewingDisplay.py (mod_rh_paperReviewingDisplay.RHPaperReviewingDisplay)
# Inactive: /paperReviewingDisplay.py/downloadTemplate (mod_rh_paperReviewingDisplay.RHDownloadPRTemplate)
# Inactive: /paperReviewingDisplay.py/uploadPaper (mod_rh_paperReviewingDisplay.RHUploadPaper)


# Routes for payment.py
# Inactive: /payment.py (mod_rh_payment.RHPaymentModule)


# Routes for posterTemplates.py
# Inactive: /posterTemplates.py (mod_rh_templates.RHPosterTemplates)
# Inactive: /posterTemplates.py/posterDesign (mod_rh_templates.RHConfPosterDesign)
# Inactive: /posterTemplates.py/posterPrinting (mod_rh_templates.RHPosterTemplates)


# Routes for resetSessionTZ.py
# Inactive: /resetSessionTZ.py (mod_rh_resetTimezone.RHResetTZ)


# Routes for roomBooking.py
# Inactive: /roomBooking.py (mod_rh_roomBooking.RHRoomBookingWelcome)
# Inactive: /roomBooking.py/acceptBooking (mod_rh_roomBooking.RHRoomBookingAcceptBooking)
# Inactive: /roomBooking.py/admin (mod_rh_roomBooking.RHRoomBookingAdmin)
# Inactive: /roomBooking.py/adminLocation (mod_rh_roomBooking.RHRoomBookingAdminLocation)
# Inactive: /roomBooking.py/blockingDetails (mod_rh_roomBooking.RHRoomBookingBlockingDetails)
# Inactive: /roomBooking.py/blockingForm (mod_rh_roomBooking.RHRoomBookingBlockingForm)
# Inactive: /roomBooking.py/blockingList (mod_rh_roomBooking.RHRoomBookingBlockingList)
# Inactive: /roomBooking.py/blockingsForMyRooms (mod_rh_roomBooking.RHRoomBookingBlockingsForMyRooms)
# Inactive: /roomBooking.py/bookRoom (mod_rh_roomBooking.RHRoomBookingBookRoom)
# Inactive: /roomBooking.py/bookingDetails (mod_rh_roomBooking.RHRoomBookingBookingDetails)
# Inactive: /roomBooking.py/bookingForm (mod_rh_roomBooking.RHRoomBookingBookingForm)
# Inactive: /roomBooking.py/bookingList (mod_rh_roomBooking.RHRoomBookingBookingList)
# Inactive: /roomBooking.py/cancelBooking (mod_rh_roomBooking.RHRoomBookingCancelBooking)
# Inactive: /roomBooking.py/cancelBookingOccurrence (mod_rh_roomBooking.RHRoomBookingCancelBookingOccurrence)
# Inactive: /roomBooking.py/cloneBooking (mod_rh_roomBooking.RHRoomBookingCloneBooking)
# Inactive: /roomBooking.py/deleteBlocking (mod_rh_roomBooking.RHRoomBookingDelete)
# Inactive: /roomBooking.py/deleteBooking (mod_rh_roomBooking.RHRoomBookingDeleteBooking)
# Inactive: /roomBooking.py/deleteCustomAttribute (mod_rh_roomBooking.RHRoomBookingDeleteCustomAttribute)
# Inactive: /roomBooking.py/deleteEquipment (mod_rh_roomBooking.RHRoomBookingDeleteEquipment)
# Inactive: /roomBooking.py/deleteLocation (mod_rh_roomBooking.RHRoomBookingDeleteLocation)
# Inactive: /roomBooking.py/deleteRoom (mod_rh_roomBooking.RHRoomBookingDeleteRoom)
# Inactive: /roomBooking.py/mapOfRooms (mod_rh_roomBooking.RHRoomBookingMapOfRooms)
# Inactive: /roomBooking.py/mapOfRoomsWidget (mod_rh_roomBooking.RHRoomBookingMapOfRoomsWidget)
# Inactive: /roomBooking.py/rejectAllConflicting (mod_rh_roomBooking.RHRoomBookingRejectALlConflicting)
# Inactive: /roomBooking.py/rejectBooking (mod_rh_roomBooking.RHRoomBookingRejectBooking)
# Inactive: /roomBooking.py/rejectBookingOccurrence (mod_rh_roomBooking.RHRoomBookingRejectBookingOccurrence)
# Inactive: /roomBooking.py/roomDetails (mod_rh_roomBooking.RHRoomBookingRoomDetails)
# Inactive: /roomBooking.py/roomForm (mod_rh_roomBooking.RHRoomBookingRoomForm)
# Inactive: /roomBooking.py/roomList (mod_rh_roomBooking.RHRoomBookingRoomList)
# Inactive: /roomBooking.py/roomStats (mod_rh_roomBooking.RHRoomBookingRoomStats)
# Inactive: /roomBooking.py/saveBooking (mod_rh_roomBooking.RHRoomBookingSaveBooking)
# Inactive: /roomBooking.py/saveCustomAttributes (mod_rh_roomBooking.RHRoomBookingSaveCustomAttribute)
# Inactive: /roomBooking.py/saveEquipment (mod_rh_roomBooking.RHRoomBookingSaveEquipment)
# Inactive: /roomBooking.py/saveLocation (mod_rh_roomBooking.RHRoomBookingSaveLocation)
# Inactive: /roomBooking.py/saveRoom (mod_rh_roomBooking.RHRoomBookingSaveRoom)
# Inactive: /roomBooking.py/search4Bookings (mod_rh_roomBooking.RHRoomBookingSearch4Bookings)
# Inactive: /roomBooking.py/search4Rooms (mod_rh_roomBooking.RHRoomBookingSearch4Rooms)
# Inactive: /roomBooking.py/setDefaultLocation (mod_rh_roomBooking.RHRoomBookingSetDefaultLocation)
# Inactive: /roomBooking.py/statement (mod_rh_roomBooking.RHRoomBookingStatement)


# Routes for roomBookingPluginAdmin.py
# Inactive: /roomBookingPluginAdmin.py (mod_rh_roomBookingPluginAdmin.RHRoomBookingPluginAdmin)
# Inactive: /roomBookingPluginAdmin.py/switchRoomBookingModuleActive (mod_rh_roomBookingPluginAdmin.RHSwitchRoomBookingModuleActive)
# Inactive: /roomBookingPluginAdmin.py/zodbSave (mod_rh_roomBookingPluginAdmin.RHZODBSave)


# Routes for roomMapper.py
# Inactive: /roomMapper.py (mod_rh_roomMappers.RHRoomMappers)
# Inactive: /roomMapper.py/creation (mod_rh_roomMappers.RHRoomMapperCreation)
# Inactive: /roomMapper.py/details (mod_rh_roomMappers.RHRoomMapperDetails)
# Inactive: /roomMapper.py/modify (mod_rh_roomMappers.RHRoomMapperModification)
# Inactive: /roomMapper.py/performCreation (mod_rh_roomMappers.RHRoomMapperPerformCreation)
# Inactive: /roomMapper.py/performModify (mod_rh_roomMappers.RHRoomMapperPerformModification)


# Routes for sessionDisplay.py
# Inactive: /sessionDisplay.py (mod_rh_sessionDisplay.RHSessionDisplay)
# Inactive: /sessionDisplay.py/ical (mod_rh_sessionDisplay.RHSessionToiCal)


# Routes for sessionModifAC.py
legacy.add_url_rule('/sessionModifAC.py',
                    'sessionModifAC',
                    rh_as_view(mod_rh_sessionModif.RHSessionModifAC),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModifAC.py/setVisibility',
                    'sessionModifAC-setVisibility',
                    rh_as_view(mod_rh_sessionModif.RHSessionSetVisibility),
                    methods=('GET', 'POST'))


# Routes for sessionModifComm.py
legacy.add_url_rule('/sessionModifComm.py',
                    'sessionModifComm',
                    rh_as_view(mod_rh_sessionModif.RHSessionModifComm),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModifComm.py/edit',
                    'sessionModifComm-edit',
                    rh_as_view(mod_rh_sessionModif.RHSessionModifCommEdit),
                    methods=('GET', 'POST'))


# Routes for sessionModifSchedule.py
legacy.add_url_rule('/sessionModifSchedule.py',
                    'sessionModifSchedule',
                    rh_as_view(mod_rh_sessionModif.RHSessionModifSchedule),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModifSchedule.py/fitSlot',
                    'sessionModifSchedule-fitSlot',
                    rh_as_view(mod_rh_sessionModif.RHFitSlot),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModifSchedule.py/slotCalc',
                    'sessionModifSchedule-slotCalc',
                    rh_as_view(mod_rh_sessionModif.RHSlotCalc),
                    methods=('GET', 'POST'))


# Routes for sessionModifTools.py
legacy.add_url_rule('/sessionModifTools.py',
                    'sessionModifTools',
                    rh_as_view(mod_rh_sessionModif.RHSessionModifTools),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModifTools.py/delete',
                    'sessionModifTools-delete',
                    rh_as_view(mod_rh_sessionModif.RHSessionDeletion),
                    methods=('GET', 'POST'))


# Routes for sessionModification.py
legacy.add_url_rule('/sessionModification.py',
                    'sessionModification',
                    rh_as_view(mod_rh_sessionModif.RHSessionModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/addContribs',
                    'sessionModification-addContribs',
                    rh_as_view(mod_rh_sessionModif.RHAddContribs),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/close',
                    'sessionModification-close',
                    rh_as_view(mod_rh_sessionModif.RHSessionClose),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/contribAction',
                    'sessionModification-contribAction',
                    rh_as_view(mod_rh_sessionModif.RHContribsActions),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/contribList',
                    'sessionModification-contribList',
                    rh_as_view(mod_rh_sessionModif.RHContribList),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/contribQuickAccess',
                    'sessionModification-contribQuickAccess',
                    rh_as_view(mod_rh_sessionModif.RHContribQuickAccess),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/contribsToPDF',
                    'sessionModification-contribsToPDF',
                    rh_as_view(mod_rh_sessionModif.RHContribsToPDF),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/editContrib',
                    'sessionModification-editContrib',
                    rh_as_view(mod_rh_sessionModif.RHContribListEditContrib),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/materials',
                    'sessionModification-materials',
                    rh_as_view(mod_rh_sessionModif.RHMaterials),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/materialsAdd',
                    'sessionModification-materialsAdd',
                    rh_as_view(mod_rh_sessionModif.RHMaterialsAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/modify',
                    'sessionModification-modify',
                    rh_as_view(mod_rh_sessionModif.RHSessionDataModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/open',
                    'sessionModification-open',
                    rh_as_view(mod_rh_sessionModif.RHSessionOpen),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/sessionModification.py/participantList',
                    'sessionModification-participantList',
                    rh_as_view(mod_rh_sessionModif.RHContribsParticipantList),
                    methods=('GET', 'POST'))


# Routes for signIn.py
# Inactive: /signIn.py (mod_rh_login.RHSignIn)
# Inactive: /signIn.py/active (mod_rh_login.RHActive)
# Inactive: /signIn.py/disabledAccount (mod_rh_login.RHDisabledAccount)
# Inactive: /signIn.py/sendActivation (mod_rh_login.RHSendActivation)
# Inactive: /signIn.py/sendLogin (mod_rh_login.RHSendLogin)
# Inactive: /signIn.py/unactivatedAccount (mod_rh_login.RHUnactivatedAccount)


# Routes for subContributionDisplay.py
legacy.add_url_rule('/subContributionDisplay.py',
                    'subContributionDisplay',
                    rh_as_view(mod_rh_subContribDisplay.RHSubContributionDisplay),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/subContributionDisplay.py/marcxml',
                    'subContributionDisplay-marcxml',
                    rh_as_view(mod_rh_subContribDisplay.RHSubContributionToMarcXML),
                    methods=('GET', 'POST'))


# Routes for subContributionModification.py
legacy.add_url_rule('/subContributionModification.py',
                    'subContributionModification',
                    rh_as_view(mod_rh_subContribMod.RHSubContributionModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/subContributionModification.py/data',
                    'subContributionModification-data',
                    rh_as_view(mod_rh_subContribMod.RHSubContributionData),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/subContributionModification.py/materials',
                    'subContributionModification-materials',
                    rh_as_view(mod_rh_subContribMod.RHMaterials),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/subContributionModification.py/materialsAdd',
                    'subContributionModification-materialsAdd',
                    rh_as_view(mod_rh_subContribMod.RHMaterialsAdd),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/subContributionModification.py/modifData',
                    'subContributionModification-modifData',
                    rh_as_view(mod_rh_subContribMod.RHSubContributionModifData),
                    methods=('GET', 'POST'))


# Routes for subContributionTools.py
legacy.add_url_rule('/subContributionTools.py',
                    'subContributionTools',
                    rh_as_view(mod_rh_subContribMod.RHSubContributionTools),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/subContributionTools.py/delete',
                    'subContributionTools-delete',
                    rh_as_view(mod_rh_subContribMod.RHSubContributionDeletion),
                    methods=('GET', 'POST'))


# Routes for taskManager.py
# Inactive: /taskManager.py (mod_rh_taskManager.RHTaskManager)


# Routes for trackAbstractModif.py
legacy.add_url_rule('/trackAbstractModif.py',
                    'trackAbstractModif',
                    rh_as_view(mod_rh_trackModif.RHTrackAbstract),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/abstractAction',
                    'trackAbstractModif-abstractAction',
                    rh_as_view(mod_rh_trackModif.RHAbstractsActions),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/abstractToPDF',
                    'trackAbstractModif-abstractToPDF',
                    rh_as_view(mod_rh_trackModif.RHAbstractToPDF),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/accept',
                    'trackAbstractModif-accept',
                    rh_as_view(mod_rh_trackModif.RHTrackAbstractAccept),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/commentEdit',
                    'trackAbstractModif-commentEdit',
                    rh_as_view(mod_rh_trackModif.RHAbstractIntCommentEdit),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/commentNew',
                    'trackAbstractModif-commentNew',
                    rh_as_view(mod_rh_trackModif.RHAbstractIntCommentNew),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/commentRem',
                    'trackAbstractModif-commentRem',
                    rh_as_view(mod_rh_trackModif.RHAbstractIntCommentRem),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/comments',
                    'trackAbstractModif-comments',
                    rh_as_view(mod_rh_trackModif.RHAbstractIntComments),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/directAccess',
                    'trackAbstractModif-directAccess',
                    rh_as_view(mod_rh_trackModif.RHTrackAbstractDirectAccess),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/markAsDup',
                    'trackAbstractModif-markAsDup',
                    rh_as_view(mod_rh_trackModif.RHModAbstractMarkAsDup),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/proposeForOtherTracks',
                    'trackAbstractModif-proposeForOtherTracks',
                    rh_as_view(mod_rh_trackModif.RHTrackAbstractPropForOtherTracks),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/proposeToBeAcc',
                    'trackAbstractModif-proposeToBeAcc',
                    rh_as_view(mod_rh_trackModif.RHTrackAbstractPropToAccept),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/proposeToBeRej',
                    'trackAbstractModif-proposeToBeRej',
                    rh_as_view(mod_rh_trackModif.RHTrackAbstractPropToReject),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/reject',
                    'trackAbstractModif-reject',
                    rh_as_view(mod_rh_trackModif.RHTrackAbstractReject),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackAbstractModif.py/unMarkAsDup',
                    'trackAbstractModif-unMarkAsDup',
                    rh_as_view(mod_rh_trackModif.RHModAbstractUnMarkAsDup),
                    methods=('GET', 'POST'))


# Routes for trackModContribList.py
legacy.add_url_rule('/trackModContribList.py',
                    'trackModContribList',
                    rh_as_view(mod_rh_trackModif.RHContribList),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackModContribList.py/contribAction',
                    'trackModContribList-contribAction',
                    rh_as_view(mod_rh_trackModif.RHContribsActions),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackModContribList.py/contribQuickAccess',
                    'trackModContribList-contribQuickAccess',
                    rh_as_view(mod_rh_trackModif.RHContribQuickAccess),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackModContribList.py/contribsToPDF',
                    'trackModContribList-contribsToPDF',
                    rh_as_view(mod_rh_trackModif.RHContribsToPDF),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackModContribList.py/participantList',
                    'trackModContribList-participantList',
                    rh_as_view(mod_rh_trackModif.RHContribsParticipantList),
                    methods=('GET', 'POST'))


# Routes for trackModifAbstracts.py
legacy.add_url_rule('/trackModifAbstracts.py',
                    'trackModifAbstracts',
                    rh_as_view(mod_rh_trackModif.RHTrackAbstractList),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackModifAbstracts.py/abstractsToPDF',
                    'trackModifAbstracts-abstractsToPDF',
                    rh_as_view(mod_rh_trackModif.RHAbstractsToPDF),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackModifAbstracts.py/participantList',
                    'trackModifAbstracts-participantList',
                    rh_as_view(mod_rh_trackModif.RHAbstractsParticipantList),
                    methods=('GET', 'POST'))


# Routes for trackModifCoordination.py
legacy.add_url_rule('/trackModifCoordination.py',
                    'trackModifCoordination',
                    rh_as_view(mod_rh_trackModif.RHTrackCoordination),
                    methods=('GET', 'POST'))


# Routes for trackModification.py
legacy.add_url_rule('/trackModification.py',
                    'trackModification',
                    rh_as_view(mod_rh_trackModif.RHTrackModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackModification.py/modify',
                    'trackModification-modify',
                    rh_as_view(mod_rh_trackModif.RHTrackDataModification),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/trackModification.py/performModify',
                    'trackModification-performModify',
                    rh_as_view(mod_rh_trackModif.RHTrackPerformDataModification),
                    methods=('GET', 'POST'))


# Routes for updateNews.py
# Inactive: /updateNews.py (mod_rh_admins.RHUpdateNews)


# Routes for userAPI.py
# Inactive: /userAPI.py (mod_rh_api.RHUserAPI)
# Inactive: /userAPI.py/block (mod_rh_api.RHUserAPIBlock)
# Inactive: /userAPI.py/create (mod_rh_api.RHUserAPICreate)
# Inactive: /userAPI.py/delete (mod_rh_api.RHUserAPIDelete)


# Routes for userAbstracts.py
# Inactive: /userAbstracts.py (mod_rh_CFADisplay.RHUserAbstracts)
# Inactive: /userAbstracts.py/pdf (mod_rh_CFADisplay.RHUserAbstractsPDF)


# Routes for userBaskets.py
# Inactive: /userBaskets.py (mod_rh_users.RHUserBaskets)


# Routes for userDashboard.py
# Inactive: /userDashboard.py (mod_rh_users.RHUserDashboard)


# Routes for userDetails.py
# Inactive: /userDetails.py (mod_rh_users.RHUserDetails)


# Routes for userList.py
# Inactive: /userList.py (mod_rh_users.RHUsers)


# Routes for userManagement.py
# Inactive: /userManagement.py (mod_rh_users.RHUserManagement)
# Inactive: /userManagement.py/switchAuthorisedAccountCreation (mod_rh_users.RHUserManagementSwitchAuthorisedAccountCreation)
# Inactive: /userManagement.py/switchModerateAccountCreation (mod_rh_users.RHUserManagementSwitchModerateAccountCreation)
# Inactive: /userManagement.py/switchNotifyAccountCreation (mod_rh_users.RHUserManagementSwitchNotifyAccountCreation)


# Routes for userMerge.py
# Inactive: /userMerge.py (mod_rh_admins.RHUserMerge)


# Routes for userPreferences.py
# Inactive: /userPreferences.py (mod_rh_users.RHUserPreferences)


# Routes for userRegistration.py
# Inactive: /userRegistration.py (mod_rh_users.RHUserCreation)
# Inactive: /userRegistration.py/UserExist (mod_rh_users.RHUserExistWithIdentity)
# Inactive: /userRegistration.py/active (mod_rh_users.RHUserActive)
# Inactive: /userRegistration.py/created (mod_rh_users.RHUserCreated)
# Inactive: /userRegistration.py/disable (mod_rh_users.RHUserDisable)


# Routes for userSelection.py
legacy.add_url_rule('/userSelection.py/createExternalUsers',
                    'userSelection-createExternalUsers',
                    rh_as_view(mod_rh_users.RHCreateExternalUsers),
                    methods=('GET', 'POST'))


# Routes for wcalendar.py
# Inactive: /wcalendar.py (mod_rh_calendar.RHCalendar)
# Inactive: /wcalendar.py/select (mod_rh_calendar.RHCalendarSelectCategories)


# Routes for xmlGateway.py
legacy.add_url_rule('/xmlGateway.py',
                    'xmlGateway',
                    rh_as_view(mod_rh_xmlGateway.RHLoginStatus),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/getCategoryInfo',
                    'xmlGateway-getCategoryInfo',
                    rh_as_view(mod_rh_xmlGateway.RHCategInfo),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/getStatsIndico',
                    'xmlGateway-getStatsIndico',
                    rh_as_view(mod_rh_xmlGateway.RHStatsIndico),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/getStatsRoomBooking',
                    'xmlGateway-getStatsRoomBooking',
                    rh_as_view(mod_rh_xmlGateway.RHStatsRoomBooking),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/loginStatus',
                    'xmlGateway-loginStatus',
                    rh_as_view(mod_rh_xmlGateway.RHLoginStatus),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/signIn',
                    'xmlGateway-signIn',
                    rh_as_view(mod_rh_xmlGateway.RHSignIn),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/signOut',
                    'xmlGateway-signOut',
                    rh_as_view(mod_rh_xmlGateway.RHSignOut),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/webcastForthcomingEvents',
                    'xmlGateway-webcastForthcomingEvents',
                    rh_as_view(mod_rh_xmlGateway.RHWebcastForthcomingEvents),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/webcastOnAir',
                    'xmlGateway-webcastOnAir',
                    rh_as_view(mod_rh_xmlGateway.RHWebcastOnAir),
                    methods=('GET', 'POST'))
