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

import MaKaC.webinterface.rh.conferenceModif as mod_rh_conferenceModif
import MaKaC.webinterface.rh.contribReviewingModif as mod_rh_contribReviewingModif
import MaKaC.webinterface.rh.reviewingAssignContributions as mod_rh_reviewingAssignContributions
import MaKaC.webinterface.rh.reviewingControlModif as mod_rh_reviewingControlModif
import MaKaC.webinterface.rh.reviewingListContribToJudge as mod_rh_reviewingListContribToJudge
import MaKaC.webinterface.rh.reviewingModif as mod_rh_reviewingModif
import MaKaC.webinterface.rh.reviewingUserCompetencesModif as mod_rh_reviewingUserCompetencesModif
import MaKaC.webinterface.rh.sessionModif as mod_rh_sessionModif
import MaKaC.webinterface.rh.users as mod_rh_users
import MaKaC.webinterface.rh.xmlGateway as mod_rh_xmlGateway


legacy = IndicoBlueprint('legacy', __name__)


# Routes for EMail.py
# Inactive: /EMail.py (mod_rh_conferenceDisplay.RHConferenceEmail)
# Inactive: /EMail.py/send (mod_rh_conferenceDisplay.RHConferenceSendEmail)
# Inactive: /EMail.py/sendcontribparticipants (mod_rh_conferenceModif.RHContribParticipantsSendEmail)
# Inactive: /EMail.py/sendconvener (mod_rh_conferenceModif.RHConvenerSendEmail)
# Inactive: /EMail.py/sendreg (mod_rh_registrantsModif.RHRegistrantSendEmail)


# Routes for JSContent.py
# Inactive: /JSContent.py/getVars (mod_rh_JSContent.RHGetVarsJs)


# Routes for about.py
# Inactive: /about.py (mod_rh_about.RHAbout)


# Routes for abstractDisplay.py
# Inactive: /abstractDisplay.py (mod_rh_CFADisplay.RHAbstractDisplay)
# Inactive: /abstractDisplay.py/getAttachedFile (mod_rh_CFADisplay.RHGetAttachedFile)
# Inactive: /abstractDisplay.py/pdf (mod_rh_CFADisplay.RHAbstractDisplayPDF)


# Routes for abstractManagment.py
# Inactive: /abstractManagment.py (mod_rh_abstractModif.RHAbstractManagment)
# Inactive: /abstractManagment.py/abstractToPDF (mod_rh_abstractModif.RHAbstractToPDF)
# Inactive: /abstractManagment.py/accept (mod_rh_abstractModif.RHAbstractManagmentAccept)
# Inactive: /abstractManagment.py/acceptMultiple (mod_rh_conferenceModif.RHAbstractManagmentAcceptMultiple)
# Inactive: /abstractManagment.py/backToSubmitted (mod_rh_abstractModif.RHBackToSubmitted)
# Inactive: /abstractManagment.py/changeTrack (mod_rh_abstractModif.RHAbstractManagmentChangeTrack)
# Inactive: /abstractManagment.py/comments (mod_rh_abstractModif.RHIntComments)
# Inactive: /abstractManagment.py/directAccess (mod_rh_abstractModif.RHAbstractDirectAccess)
# Inactive: /abstractManagment.py/editComment (mod_rh_abstractModif.RHIntCommentEdit)
# Inactive: /abstractManagment.py/editData (mod_rh_abstractModif.RHEditData)
# Inactive: /abstractManagment.py/markAsDup (mod_rh_abstractModif.RHMarkAsDup)
# Inactive: /abstractManagment.py/mergeInto (mod_rh_abstractModif.RHMergeInto)
# Inactive: /abstractManagment.py/newComment (mod_rh_abstractModif.RHNewIntComment)
# Inactive: /abstractManagment.py/notifLog (mod_rh_abstractModif.RHNotifLog)
# Inactive: /abstractManagment.py/orderByRating (mod_rh_abstractModif.RHAbstractTrackOrderByRating)
# Inactive: /abstractManagment.py/propToAcc (mod_rh_abstractModif.RHPropToAcc)
# Inactive: /abstractManagment.py/propToRej (mod_rh_abstractModif.RHPropToRej)
# Inactive: /abstractManagment.py/reject (mod_rh_abstractModif.RHAbstractManagmentReject)
# Inactive: /abstractManagment.py/rejectMultiple (mod_rh_conferenceModif.RHAbstractManagmentRejectMultiple)
# Inactive: /abstractManagment.py/remComment (mod_rh_abstractModif.RHIntCommentRem)
# Inactive: /abstractManagment.py/trackProposal (mod_rh_abstractModif.RHAbstractTrackManagment)
# Inactive: /abstractManagment.py/unMarkAsDup (mod_rh_abstractModif.RHUnMarkAsDup)
# Inactive: /abstractManagment.py/unmerge (mod_rh_abstractModif.RHUnMerge)
# Inactive: /abstractManagment.py/withdraw (mod_rh_abstractModif.RHWithdraw)
# Inactive: /abstractManagment.py/xml (mod_rh_abstractModif.RHAbstractToXML)


# Routes for abstractModify.py
# Inactive: /abstractModify.py (mod_rh_CFADisplay.RHAbstractModify)


# Routes for abstractReviewing.py
# Inactive: /abstractReviewing.py/notifTpl (mod_rh_abstractReviewing.RHNotifTpl)
# Inactive: /abstractReviewing.py/notifTplCondNew (mod_rh_abstractReviewing.RHNotifTplConditionNew)
# Inactive: /abstractReviewing.py/notifTplCondRem (mod_rh_abstractReviewing.RHNotifTplConditionRem)
# Inactive: /abstractReviewing.py/notifTplDisplay (mod_rh_abstractReviewing.RHCFANotifTplDisplay)
# Inactive: /abstractReviewing.py/notifTplDown (mod_rh_abstractReviewing.RHCFANotifTplDown)
# Inactive: /abstractReviewing.py/notifTplEdit (mod_rh_abstractReviewing.RHCFANotifTplEdit)
# Inactive: /abstractReviewing.py/notifTplNew (mod_rh_abstractReviewing.RHCFANotifTplNew)
# Inactive: /abstractReviewing.py/notifTplPreview (mod_rh_abstractReviewing.RHCFANotifTplPreview)
# Inactive: /abstractReviewing.py/notifTplRem (mod_rh_abstractReviewing.RHCFANotifTplRem)
# Inactive: /abstractReviewing.py/notifTplUp (mod_rh_abstractReviewing.RHCFANotifTplUp)
# Inactive: /abstractReviewing.py/reviewingSetup (mod_rh_abstractReviewing.RHAbstractReviewingSetup)
# Inactive: /abstractReviewing.py/reviewingTeam (mod_rh_abstractReviewing.RHAbstractReviewingTeam)


# Routes for abstractSubmission.py
# Inactive: /abstractSubmission.py (mod_rh_CFADisplay.RHAbstractSubmission)
# Inactive: /abstractSubmission.py/confirmation (mod_rh_CFADisplay.RHAbstractSubmissionConfirmation)


# Routes for abstractTools.py
# Inactive: /abstractTools.py (mod_rh_abstractModif.RHTools)
# Inactive: /abstractTools.py/delete (mod_rh_abstractModif.RHAbstractDelete)


# Routes for abstractWithdraw.py
# Inactive: /abstractWithdraw.py (mod_rh_CFADisplay.RHAbstractWithdraw)
# Inactive: /abstractWithdraw.py/recover (mod_rh_CFADisplay.RHAbstractRecovery)


# Routes for abstractsManagment.py
# Inactive: /abstractsManagment.py (mod_rh_conferenceModif.RHAbstractList)
# Inactive: /abstractsManagment.py/abstractsActions (mod_rh_conferenceModif.RHAbstractsActions)
# Inactive: /abstractsManagment.py/mergeAbstracts (mod_rh_conferenceModif.RHAbstractsMerge)
# Inactive: /abstractsManagment.py/newAbstract (mod_rh_conferenceModif.RHNewAbstract)
# Inactive: /abstractsManagment.py/participantList (mod_rh_conferenceModif.RHAbstractsParticipantList)


# Routes for adminAnnouncement.py
# Inactive: /adminAnnouncement.py (mod_rh_announcement.RHAnnouncementModif)
# Inactive: /adminAnnouncement.py/save (mod_rh_announcement.RHAnnouncementModifSave)


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
# Inactive: /confModBOA.py (mod_rh_conferenceModif.RHAbstractBook)
# Inactive: /confModBOA.py/toogleShowIds (mod_rh_conferenceModif.RHAbstractBookToogleShowIds)


# Routes for confModifAC.py
# Inactive: /confModifAC.py (mod_rh_conferenceModif.RHConfModifAC)
# Inactive: /confModifAC.py/grantModificationToAllConveners (mod_rh_conferenceModif.RHConfGrantModificationToAllConveners)
# Inactive: /confModifAC.py/grantSubmissionToAllSpeakers (mod_rh_conferenceModif.RHConfGrantSubmissionToAllSpeakers)
# Inactive: /confModifAC.py/modifySessionCoordRights (mod_rh_conferenceModif.RHModifSessionCoordRights)
# Inactive: /confModifAC.py/removeAllSubmissionRights (mod_rh_conferenceModif.RHConfRemoveAllSubmissionRights)
# Inactive: /confModifAC.py/setVisibility (mod_rh_conferenceModif.RHConfSetVisibility)


# Routes for confModifCFA.py
# Inactive: /confModifCFA.py (mod_rh_conferenceModif.RHConfModifCFA)
# Inactive: /confModifCFA.py/absFieldDown (mod_rh_conferenceModif.RHConfMoveAbsFieldDown)
# Inactive: /confModifCFA.py/absFieldUp (mod_rh_conferenceModif.RHConfMoveAbsFieldUp)
# Inactive: /confModifCFA.py/abstractFields (mod_rh_conferenceModif.RHConfAbstractFields)
# Inactive: /confModifCFA.py/addAbstractField (mod_rh_conferenceModif.RHConfAddAbstractField)
# Inactive: /confModifCFA.py/changeStatus (mod_rh_conferenceModif.RHConfModifCFAStatus)
# Inactive: /confModifCFA.py/editAbstractField (mod_rh_conferenceModif.RHConfEditAbstractField)
# Inactive: /confModifCFA.py/makeTracksMandatory (mod_rh_conferenceModif.RHConfModifCFAMakeTracksMandatory)
# Inactive: /confModifCFA.py/modifyData (mod_rh_conferenceModif.RHCFADataModification)
# Inactive: /confModifCFA.py/performAddAbstractField (mod_rh_conferenceModif.RHConfPerformAddAbstractField)
# Inactive: /confModifCFA.py/performModifyData (mod_rh_conferenceModif.RHCFAPerformDataModification)
# Inactive: /confModifCFA.py/preview (mod_rh_conferenceModif.RHConfModifCFAPreview)
# Inactive: /confModifCFA.py/removeAbstractField (mod_rh_conferenceModif.RHConfRemoveAbstractField)
# Inactive: /confModifCFA.py/switchAttachFiles (mod_rh_conferenceModif.RHConfModifCFASwitchAttachFiles)
# Inactive: /confModifCFA.py/switchMultipleTracks (mod_rh_conferenceModif.RHConfModifCFASwitchMultipleTracks)
# Inactive: /confModifCFA.py/switchSelectSpeakerMandatory (mod_rh_conferenceModif.RHConfModifCFASwitchSelectSpeakerMandatory)
# Inactive: /confModifCFA.py/switchShowAttachedFiles (mod_rh_conferenceModif.RHConfModifCFASwitchShowAttachedFilesContribList)
# Inactive: /confModifCFA.py/switchShowSelectSpeaker (mod_rh_conferenceModif.RHConfModifCFASwitchShowSelectAsSpeaker)


# Routes for confModifContribList.py
# Inactive: /confModifContribList.py (mod_rh_conferenceModif.RHContributionList)
# Inactive: /confModifContribList.py/contribQuickAccess (mod_rh_conferenceModif.RHContribQuickAccess)
# Inactive: /confModifContribList.py/contribsActions (mod_rh_conferenceModif.RHContribsActions)
# Inactive: /confModifContribList.py/contribsToPDFMenu (mod_rh_conferenceModif.RHContribsToPDFMenu)
# Inactive: /confModifContribList.py/matPkg (mod_rh_conferenceModif.RHMaterialPackage)
# Inactive: /confModifContribList.py/moveToSession (mod_rh_conferenceModif.RHMoveContribsToSession)
# Inactive: /confModifContribList.py/participantList (mod_rh_conferenceModif.RHContribsParticipantList)
# Inactive: /confModifContribList.py/proceedings (mod_rh_conferenceModif.RHProceedings)


# Routes for confModifDisplay.py
# Inactive: /confModifDisplay.py (mod_rh_conferenceModif.RHConfModifDisplayCustomization)
# Inactive: /confModifDisplay.py/addLink (mod_rh_conferenceModif.RHConfModifDisplayAddLink)
# Inactive: /confModifDisplay.py/addPage (mod_rh_conferenceModif.RHConfModifDisplayAddPage)
# Inactive: /confModifDisplay.py/addSpacer (mod_rh_conferenceModif.RHConfModifDisplayAddSpacer)
# Inactive: /confModifDisplay.py/confHeader (mod_rh_conferenceModif.RHConfModifDisplayConfHeader)
# Inactive: /confModifDisplay.py/custom (mod_rh_conferenceModif.RHConfModifDisplayCustomization)
# Inactive: /confModifDisplay.py/downLink (mod_rh_conferenceModif.RHConfModifDisplayDownLink)
# Inactive: /confModifDisplay.py/formatTitleBgColor (mod_rh_conferenceModif.RHConfModifFormatTitleBgColor)
# Inactive: /confModifDisplay.py/formatTitleTextColor (mod_rh_conferenceModif.RHConfModifFormatTitleTextColor)
# Inactive: /confModifDisplay.py/menu (mod_rh_conferenceModif.RHConfModifDisplayMenu)
# Inactive: /confModifDisplay.py/modifyData (mod_rh_conferenceModif.RHConfModifDisplayModifyData)
# Inactive: /confModifDisplay.py/modifySystemData (mod_rh_conferenceModif.RHConfModifDisplayModifySystemData)
# Inactive: /confModifDisplay.py/previewCSS (mod_rh_conferenceModif.RHConfModifPreviewCSS)
# Inactive: /confModifDisplay.py/removeCSS (mod_rh_conferenceModif.RHConfRemoveCSS)
# Inactive: /confModifDisplay.py/removeLink (mod_rh_conferenceModif.RHConfModifDisplayRemoveLink)
# Inactive: /confModifDisplay.py/removeLogo (mod_rh_conferenceModif.RHConfRemoveLogo)
# Inactive: /confModifDisplay.py/resources (mod_rh_conferenceModif.RHConfModifDisplayResources)
# Inactive: /confModifDisplay.py/saveCSS (mod_rh_conferenceModif.RHConfSaveCSS)
# Inactive: /confModifDisplay.py/saveLogo (mod_rh_conferenceModif.RHConfSaveLogo)
# Inactive: /confModifDisplay.py/savePic (mod_rh_conferenceModif.RHConfSavePic)
# Inactive: /confModifDisplay.py/tickerTapeAction (mod_rh_conferenceModif.RHConfModifTickerTapeAction)
# Inactive: /confModifDisplay.py/toggleHomePage (mod_rh_conferenceModif.RHConfModifDisplayToggleHomePage)
# Inactive: /confModifDisplay.py/toggleLinkStatus (mod_rh_conferenceModif.RHConfModifDisplayToggleLinkStatus)
# Inactive: /confModifDisplay.py/toggleNavigationBar (mod_rh_conferenceModif.RHConfModifToggleNavigationBar)
# Inactive: /confModifDisplay.py/toggleSearch (mod_rh_conferenceModif.RHConfModifToggleSearch)
# Inactive: /confModifDisplay.py/upLink (mod_rh_conferenceModif.RHConfModifDisplayUpLink)
# Inactive: /confModifDisplay.py/useCSS (mod_rh_conferenceModif.RHConfUseCSS)


# Routes for confModifEpayment.py
# Inactive: /confModifEpayment.py (mod_rh_ePaymentModif.RHEPaymentModif)
# Inactive: /confModifEpayment.py/changeStatus (mod_rh_ePaymentModif.RHEPaymentModifChangeStatus)
# Inactive: /confModifEpayment.py/dataModif (mod_rh_ePaymentModif.RHEPaymentModifDataModification)
# Inactive: /confModifEpayment.py/enableSection (mod_rh_ePaymentModif.RHEPaymentModifEnableSection)
# Inactive: /confModifEpayment.py/modifModule (mod_rh_ePaymentModif.RHModifModule)
# Inactive: /confModifEpayment.py/performDataModif (mod_rh_ePaymentModif.RHEPaymentModifPerformDataModification)


# Routes for confModifEvaluation.py
# Inactive: /confModifEvaluation.py (mod_rh_evaluationModif.RHEvaluationSetup)
# Inactive: /confModifEvaluation.py/changeStatus (mod_rh_evaluationModif.RHEvaluationSetupChangeStatus)
# Inactive: /confModifEvaluation.py/dataModif (mod_rh_evaluationModif.RHEvaluationSetupDataModif)
# Inactive: /confModifEvaluation.py/edit (mod_rh_evaluationModif.RHEvaluationEdit)
# Inactive: /confModifEvaluation.py/editPerformChanges (mod_rh_evaluationModif.RHEvaluationEditPerformChanges)
# Inactive: /confModifEvaluation.py/performDataModif (mod_rh_evaluationModif.RHEvaluationSetupPerformDataModif)
# Inactive: /confModifEvaluation.py/preview (mod_rh_evaluationModif.RHEvaluationPreview)
# Inactive: /confModifEvaluation.py/results (mod_rh_evaluationModif.RHEvaluationResults)
# Inactive: /confModifEvaluation.py/resultsOptions (mod_rh_evaluationModif.RHEvaluationResultsOptions)
# Inactive: /confModifEvaluation.py/resultsSubmittersActions (mod_rh_evaluationModif.RHEvaluationResultsSubmittersActions)
# Inactive: /confModifEvaluation.py/setup (mod_rh_evaluationModif.RHEvaluationSetup)
# Inactive: /confModifEvaluation.py/specialAction (mod_rh_evaluationModif.RHEvaluationSetupSpecialAction)


# Routes for confModifListings.py
# Inactive: /confModifListings.py/allSpeakers (mod_rh_conferenceModif.RHConfAllSpeakers)
# Inactive: /confModifListings.py/allSpeakersAction (mod_rh_conferenceModif.RHConfAllSpeakersAction)


# Routes for confModifLog.py
# Inactive: /confModifLog.py (mod_rh_conferenceModif.RHConfModifLog)


# Routes for confModifParticipants.py
# Inactive: /confModifParticipants.py (mod_rh_conferenceModif.RHConfModifParticipants)
# Inactive: /confModifParticipants.py/action (mod_rh_conferenceModif.RHConfModifParticipantsAction)
# Inactive: /confModifParticipants.py/declinedParticipants (mod_rh_conferenceModif.RHConfModifParticipantsDeclined)
# Inactive: /confModifParticipants.py/invitation (mod_rh_conferenceDisplay.RHConfParticipantsInvitation)
# Inactive: /confModifParticipants.py/pendingParticipants (mod_rh_conferenceModif.RHConfModifParticipantsPending)
# Inactive: /confModifParticipants.py/refusal (mod_rh_conferenceDisplay.RHConfParticipantsRefusal)
# Inactive: /confModifParticipants.py/setup (mod_rh_conferenceModif.RHConfModifParticipantsSetup)
# Inactive: /confModifParticipants.py/statistics (mod_rh_conferenceModif.RHConfModifParticipantsStatistics)


# Routes for confModifPendingQueues.py
# Inactive: /confModifPendingQueues.py (mod_rh_conferenceModif.RHConfModifPendingQueues)
# Inactive: /confModifPendingQueues.py/actionConfSubmitters (mod_rh_conferenceModif.RHConfModifPendingQueuesActionConfSubm)
# Inactive: /confModifPendingQueues.py/actionCoordinators (mod_rh_conferenceModif.RHConfModifPendingQueuesActionCoord)
# Inactive: /confModifPendingQueues.py/actionManagers (mod_rh_conferenceModif.RHConfModifPendingQueuesActionMgr)
# Inactive: /confModifPendingQueues.py/actionSubmitters (mod_rh_conferenceModif.RHConfModifPendingQueuesActionSubm)


# Routes for confModifProgram.py
# Inactive: /confModifProgram.py (mod_rh_conferenceModif.RHConfModifProgram)
# Inactive: /confModifProgram.py/addTrack (mod_rh_conferenceModif.RHConfAddTrack)
# Inactive: /confModifProgram.py/deleteTracks (mod_rh_conferenceModif.RHConfDelTracks)
# Inactive: /confModifProgram.py/moveTrackDown (mod_rh_conferenceModif.RHProgramTrackDown)
# Inactive: /confModifProgram.py/moveTrackUp (mod_rh_conferenceModif.RHProgramTrackUp)
# Inactive: /confModifProgram.py/performAddTrack (mod_rh_conferenceModif.RHConfPerformAddTrack)


# Routes for confModifRegistrants.py
# Inactive: /confModifRegistrants.py (mod_rh_registrantsModif.RHRegistrantListModif)
# Inactive: /confModifRegistrants.py/action (mod_rh_registrantsModif.RHRegistrantListModifAction)
# Inactive: /confModifRegistrants.py/getAttachedFile (mod_rh_registrantsModif.RHGetAttachedFile)
# Inactive: /confModifRegistrants.py/modification (mod_rh_registrantsModif.RHRegistrantModification)
# Inactive: /confModifRegistrants.py/modifyAccommodation (mod_rh_registrantsModif.RHRegistrantAccommodationModify)
# Inactive: /confModifRegistrants.py/modifyMiscInfo (mod_rh_registrantsModif.RHRegistrantMiscInfoModify)
# Inactive: /confModifRegistrants.py/modifyReasonParticipation (mod_rh_registrantsModif.RHRegistrantReasonParticipationModify)
# Inactive: /confModifRegistrants.py/modifySessions (mod_rh_registrantsModif.RHRegistrantSessionModify)
# Inactive: /confModifRegistrants.py/modifySocialEvents (mod_rh_registrantsModif.RHRegistrantSocialEventsModify)
# Inactive: /confModifRegistrants.py/modifyStatuses (mod_rh_registrantsModif.RHRegistrantStatusesModify)
# Inactive: /confModifRegistrants.py/modifyTransaction (mod_rh_registrantsModif.RHRegistrantTransactionModify)
# Inactive: /confModifRegistrants.py/newRegistrant (mod_rh_registrantsModif.RHRegistrantNewForm)
# Inactive: /confModifRegistrants.py/peformModifyTransaction (mod_rh_registrantsModif.RHRegistrantTransactionPerformModify)
# Inactive: /confModifRegistrants.py/performModifyAccommodation (mod_rh_registrantsModif.RHRegistrantAccommodationPerformModify)
# Inactive: /confModifRegistrants.py/performModifyMiscInfo (mod_rh_registrantsModif.RHRegistrantMiscInfoPerformModify)
# Inactive: /confModifRegistrants.py/performModifyReasonParticipation (mod_rh_registrantsModif.RHRegistrantReasonParticipationPerformModify)
# Inactive: /confModifRegistrants.py/performModifySessions (mod_rh_registrantsModif.RHRegistrantSessionPerformModify)
# Inactive: /confModifRegistrants.py/performModifySocialEvents (mod_rh_registrantsModif.RHRegistrantSocialEventsPerformModify)
# Inactive: /confModifRegistrants.py/performModifyStatuses (mod_rh_registrantsModif.RHRegistrantStatusesPerformModify)
# Inactive: /confModifRegistrants.py/remove (mod_rh_registrantsModif.RHRegistrantListRemove)


# Routes for confModifRegistrationForm.py
# Inactive: /confModifRegistrationForm.py (mod_rh_registrationFormModif.RHRegistrationFormModif)
# Inactive: /confModifRegistrationForm.py/actionSection (mod_rh_registrationFormModif.RHRegistrationFormActionSection)
# Inactive: /confModifRegistrationForm.py/actionStatuses (mod_rh_registrationFormModif.RHRegistrationFormActionStatuses)
# Inactive: /confModifRegistrationForm.py/addAccommodationType (mod_rh_registrationFormModif.RHRegistrationFormModifAccommodationTypeAdd)
# Inactive: /confModifRegistrationForm.py/addGeneralField (mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionFieldAdd)
# Inactive: /confModifRegistrationForm.py/addSession (mod_rh_registrationFormModif.RHRegistrationFormModifSessionsAdd)
# Inactive: /confModifRegistrationForm.py/addSocialEvent (mod_rh_registrationFormModif.RHRegistrationFormModifSocialEventAdd)
# Inactive: /confModifRegistrationForm.py/changeStatus (mod_rh_registrationFormModif.RHRegistrationFormModifChangeStatus)
# Inactive: /confModifRegistrationForm.py/dataModif (mod_rh_registrationFormModif.RHRegistrationFormModifDataModification)
# Inactive: /confModifRegistrationForm.py/enablePersonalField (mod_rh_registrationFormModif.RHRegistrationFormModifEnablePersonalField)
# Inactive: /confModifRegistrationForm.py/enableSection (mod_rh_registrationFormModif.RHRegistrationFormModifEnableSection)
# Inactive: /confModifRegistrationForm.py/modifAccommodation (mod_rh_registrationFormModif.RHRegistrationFormModifAccommodation)
# Inactive: /confModifRegistrationForm.py/modifAccommodationData (mod_rh_registrationFormModif.RHRegistrationFormModifAccommodationDataModif)
# Inactive: /confModifRegistrationForm.py/modifFurtherInformation (mod_rh_registrationFormModif.RHRegistrationFormModifFurtherInformation)
# Inactive: /confModifRegistrationForm.py/modifFurtherInformationData (mod_rh_registrationFormModif.RHRegistrationFormModifFurtherInformationDataModif)
# Inactive: /confModifRegistrationForm.py/modifGeneralField (mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionFieldModif)
# Inactive: /confModifRegistrationForm.py/modifGeneralSection (mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSection)
# Inactive: /confModifRegistrationForm.py/modifGeneralSectionData (mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionDataModif)
# Inactive: /confModifRegistrationForm.py/modifReasonParticipation (mod_rh_registrationFormModif.RHRegistrationFormModifReasonParticipation)
# Inactive: /confModifRegistrationForm.py/modifReasonParticipationData (mod_rh_registrationFormModif.RHRegistrationFormModifReasonParticipationDataModif)
# Inactive: /confModifRegistrationForm.py/modifSessions (mod_rh_registrationFormModif.RHRegistrationFormModifSessions)
# Inactive: /confModifRegistrationForm.py/modifSessionsData (mod_rh_registrationFormModif.RHRegistrationFormModifSessionsDataModif)
# Inactive: /confModifRegistrationForm.py/modifSocialEvent (mod_rh_registrationFormModif.RHRegistrationFormModifSocialEvent)
# Inactive: /confModifRegistrationForm.py/modifSocialEventData (mod_rh_registrationFormModif.RHRegistrationFormModifSocialEventDataModif)
# Inactive: /confModifRegistrationForm.py/modifStatus (mod_rh_registrationFormModif.RHRegistrationFormStatusModif)
# Inactive: /confModifRegistrationForm.py/modifyAccommodationType (mod_rh_registrationFormModif.RHRegistrationFormAccommodationTypeModify)
# Inactive: /confModifRegistrationForm.py/modifySessionItem (mod_rh_registrationFormModif.RHRegistrationFormSessionItemModify)
# Inactive: /confModifRegistrationForm.py/modifySocialEventItem (mod_rh_registrationFormModif.RHRegistrationFormSocialEventItemModify)
# Inactive: /confModifRegistrationForm.py/performAddAccommodationType (mod_rh_registrationFormModif.RHRegistrationFormModifAccommodationTypePerformAdd)
# Inactive: /confModifRegistrationForm.py/performAddGeneralField (mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionFieldPerformAdd)
# Inactive: /confModifRegistrationForm.py/performAddSession (mod_rh_registrationFormModif.RHRegistrationFormModifSessionsPerformAdd)
# Inactive: /confModifRegistrationForm.py/performAddSocialEvent (mod_rh_registrationFormModif.RHRegistrationFormModifSocialEventPerformAdd)
# Inactive: /confModifRegistrationForm.py/performDataModif (mod_rh_registrationFormModif.RHRegistrationFormModifPerformDataModification)
# Inactive: /confModifRegistrationForm.py/performModifAccommodationData (mod_rh_registrationFormModif.RHRegistrationFormModifAccommodationPerformDataModif)
# Inactive: /confModifRegistrationForm.py/performModifFurtherInformationData (mod_rh_registrationFormModif.RHRegistrationFormModifFurtherInformationPerformDataModif)
# Inactive: /confModifRegistrationForm.py/performModifGeneralField (mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionFieldPerformModif)
# Inactive: /confModifRegistrationForm.py/performModifGeneralSectionData (mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionPerformDataModif)
# Inactive: /confModifRegistrationForm.py/performModifReasonParticipationData (mod_rh_registrationFormModif.RHRegistrationFormModifReasonParticipationPerformDataModif)
# Inactive: /confModifRegistrationForm.py/performModifSessionsData (mod_rh_registrationFormModif.RHRegistrationFormModifSessionsPerformDataModif)
# Inactive: /confModifRegistrationForm.py/performModifSocialEventData (mod_rh_registrationFormModif.RHRegistrationFormModifSocialEventPerformDataModif)
# Inactive: /confModifRegistrationForm.py/performModifStatus (mod_rh_registrationFormModif.RHRegistrationFormModifStatusPerformModif)
# Inactive: /confModifRegistrationForm.py/performModifyAccommodationType (mod_rh_registrationFormModif.RHRegistrationFormAccommodationTypePerformModify)
# Inactive: /confModifRegistrationForm.py/performModifySessionItem (mod_rh_registrationFormModif.RHRegistrationFormSessionItemPerformModify)
# Inactive: /confModifRegistrationForm.py/performModifySocialEventItem (mod_rh_registrationFormModif.RHRegistrationFormSocialEventItemPerformModify)
# Inactive: /confModifRegistrationForm.py/removeAccommodationType (mod_rh_registrationFormModif.RHRegistrationFormModifAccommodationTypeRemove)
# Inactive: /confModifRegistrationForm.py/removeGeneralField (mod_rh_registrationFormModif.RHRegistrationFormModifGeneralSectionFieldProcess)
# Inactive: /confModifRegistrationForm.py/removeSession (mod_rh_registrationFormModif.RHRegistrationFormModifSessionsRemove)
# Inactive: /confModifRegistrationForm.py/removeSocialEvent (mod_rh_registrationFormModif.RHRegistrationFormModifSocialEventRemove)


# Routes for confModifRegistrationPreview.py
# Inactive: /confModifRegistrationPreview.py (mod_rh_registrationFormModif.RHRegistrationPreview)


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
# Inactive: /confModifSchedule.py (mod_rh_conferenceModif.RHConfModifSchedule)
# Inactive: /confModifSchedule.py/edit (mod_rh_conferenceModif.RHScheduleDataEdit)
# Inactive: /confModifSchedule.py/reschedule (mod_rh_conferenceModif.RHReschedule)


# Routes for confModifTools.py
# Inactive: /confModifTools.py (mod_rh_conferenceModif.RHConfModifTools)
# Inactive: /confModifTools.py/addAlarm (mod_rh_conferenceModif.RHConfAddAlarm)
# Inactive: /confModifTools.py/allSessionsConveners (mod_rh_conferenceModif.RHConfAllSessionsConveners)
# Inactive: /confModifTools.py/allSessionsConvenersAction (mod_rh_conferenceModif.RHConfAllSessionsConvenersAction)
# Inactive: /confModifTools.py/badgeDesign (mod_rh_conferenceModif.RHConfBadgeDesign)
# Inactive: /confModifTools.py/badgeGetBackground (mod_rh_conferenceModif.RHConfBadgeGetBackground)
# Inactive: /confModifTools.py/badgePrinting (mod_rh_conferenceModif.RHConfBadgePrinting)
# Inactive: /confModifTools.py/badgePrintingPDF (mod_rh_conferenceModif.RHConfBadgePrintingPDF)
# Inactive: /confModifTools.py/badgeSaveBackground (mod_rh_conferenceModif.RHConfBadgeSaveTempBackground)
# Inactive: /confModifTools.py/clone (mod_rh_conferenceModif.RHConfClone)
# Inactive: /confModifTools.py/delete (mod_rh_conferenceModif.RHConfDeletion)
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
# Inactive: /confModifTools.py/matPkg (mod_rh_conferenceModif.RHFullMaterialPackage)
# Inactive: /confModifTools.py/modifyAlarm (mod_rh_conferenceModif.RHConfModifyAlarm)
# Inactive: /confModifTools.py/performCloning (mod_rh_conferenceModif.RHConfPerformCloning)
# Inactive: /confModifTools.py/performMatPkg (mod_rh_conferenceModif.RHFullMaterialPackagePerform)
# Inactive: /confModifTools.py/posterDesign (mod_rh_conferenceModif.RHConfPosterDesign)
# Inactive: /confModifTools.py/posterGetBackground (mod_rh_conferenceModif.RHConfPosterGetBackground)
# Inactive: /confModifTools.py/posterPrinting (mod_rh_conferenceModif.RHConfPosterPrinting)
# Inactive: /confModifTools.py/posterPrintingPDF (mod_rh_conferenceModif.RHConfPosterPrintingPDF)
# Inactive: /confModifTools.py/posterSaveBackground (mod_rh_conferenceModif.RHConfPosterSaveTempBackground)
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
# Inactive: /conferenceModification.py/close (mod_rh_conferenceModif.RHConferenceClose)
# Inactive: /conferenceModification.py/closeModifKey (mod_rh_conferenceModif.RHConferenceCloseModifKey)
# Inactive: /conferenceModification.py/data (mod_rh_conferenceModif.RHConfDataModif)
# Inactive: /conferenceModification.py/dataPerform (mod_rh_conferenceModif.RHConfPerformDataModif)
# Inactive: /conferenceModification.py/editContribType (mod_rh_conferenceModif.RHConfEditContribType)
# Inactive: /conferenceModification.py/managementAccess (mod_rh_conferenceModif.RHConferenceModifManagementAccess)
# Inactive: /conferenceModification.py/materialsAdd (mod_rh_conferenceModif.RHMaterialsAdd)
# Inactive: /conferenceModification.py/materialsShow (mod_rh_conferenceModif.RHMaterialsShow)
# Inactive: /conferenceModification.py/modifKey (mod_rh_conferenceModif.RHConferenceModifKey)
# Inactive: /conferenceModification.py/open (mod_rh_conferenceModif.RHConferenceOpen)
# Inactive: /conferenceModification.py/removeContribType (mod_rh_conferenceModif.RHConfRemoveContribType)
# Inactive: /conferenceModification.py/roomBookingBookingForm (mod_rh_conferenceModif.RHConfModifRoomBookingBookingForm)
# Inactive: /conferenceModification.py/roomBookingChooseEvent (mod_rh_conferenceModif.RHConfModifRoomBookingChooseEvent)
# Inactive: /conferenceModification.py/roomBookingCloneBooking (mod_rh_conferenceModif.RHConfModifRoomBookingCloneBooking)
# Inactive: /conferenceModification.py/roomBookingDetails (mod_rh_conferenceModif.RHConfModifRoomBookingDetails)
# Inactive: /conferenceModification.py/roomBookingList (mod_rh_conferenceModif.RHConfModifRoomBookingList)
# Inactive: /conferenceModification.py/roomBookingRoomDetails (mod_rh_conferenceModif.RHConfModifRoomBookingRoomDetails)
# Inactive: /conferenceModification.py/roomBookingRoomList (mod_rh_conferenceModif.RHConfModifRoomBookingRoomList)
# Inactive: /conferenceModification.py/roomBookingSaveBooking (mod_rh_conferenceModif.RHConfModifRoomBookingSaveBooking)
# Inactive: /conferenceModification.py/roomBookingSearch4Rooms (mod_rh_conferenceModif.RHConfModifRoomBookingSearch4Rooms)
# Inactive: /conferenceModification.py/screenDates (mod_rh_conferenceModif.RHConfScreenDatesEdit)


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
# Inactive: /contributionAC.py (mod_rh_contribMod.RHContributionAC)
# Inactive: /contributionAC.py/setVisibility (mod_rh_contribMod.RHContributionSetVisibility)


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
# Inactive: /contributionModifSubCont.py (mod_rh_contribMod.RHContributionSC)
# Inactive: /contributionModifSubCont.py/actionSubContribs (mod_rh_contribMod.RHSubContribActions)
# Inactive: /contributionModifSubCont.py/add (mod_rh_contribMod.RHContributionAddSC)
# Inactive: /contributionModifSubCont.py/create (mod_rh_contribMod.RHContributionCreateSC)


# Routes for contributionModification.py
# Inactive: /contributionModification.py (mod_rh_contribMod.RHContributionModification)
# Inactive: /contributionModification.py/browseMaterial (mod_rh_contribMod.RHContribModifMaterialBrowse)
# Inactive: /contributionModification.py/data (mod_rh_contribMod.RHContributionData)
# Inactive: /contributionModification.py/materials (mod_rh_contribMod.RHMaterials)
# Inactive: /contributionModification.py/materialsAdd (mod_rh_contribMod.RHMaterialsAdd)
# Inactive: /contributionModification.py/modifData (mod_rh_contribMod.RHContributionModifData)
# Inactive: /contributionModification.py/pdf (mod_rh_contribMod.RHContributionToPDF)
# Inactive: /contributionModification.py/setSession (mod_rh_contribMod.RHSetSession)
# Inactive: /contributionModification.py/setTrack (mod_rh_contribMod.RHSetTrack)
# Inactive: /contributionModification.py/withdraw (mod_rh_contribMod.RHWithdraw)
# Inactive: /contributionModification.py/xml (mod_rh_contribMod.RHContributionToXML)


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
# Inactive: /contributionTools.py (mod_rh_contribMod.RHContributionTools)
# Inactive: /contributionTools.py/delete (mod_rh_contribMod.RHContributionDeletion)


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
# Inactive: /subContributionDisplay.py (mod_rh_subContribDisplay.RHSubContributionDisplay)
# Inactive: /subContributionDisplay.py/marcxml (mod_rh_subContribDisplay.RHSubContributionToMarcXML)


# Routes for subContributionModification.py
# Inactive: /subContributionModification.py (mod_rh_subContribMod.RHSubContributionModification)
# Inactive: /subContributionModification.py/data (mod_rh_subContribMod.RHSubContributionData)
# Inactive: /subContributionModification.py/materials (mod_rh_subContribMod.RHMaterials)
# Inactive: /subContributionModification.py/materialsAdd (mod_rh_subContribMod.RHMaterialsAdd)
# Inactive: /subContributionModification.py/modifData (mod_rh_subContribMod.RHSubContributionModifData)


# Routes for subContributionTools.py
# Inactive: /subContributionTools.py (mod_rh_subContribMod.RHSubContributionTools)
# Inactive: /subContributionTools.py/delete (mod_rh_subContribMod.RHSubContributionDeletion)


# Routes for taskManager.py
# Inactive: /taskManager.py (mod_rh_taskManager.RHTaskManager)


# Routes for trackAbstractModif.py
# Inactive: /trackAbstractModif.py (mod_rh_trackModif.RHTrackAbstract)
# Inactive: /trackAbstractModif.py/abstractAction (mod_rh_trackModif.RHAbstractsActions)
# Inactive: /trackAbstractModif.py/abstractToPDF (mod_rh_trackModif.RHAbstractToPDF)
# Inactive: /trackAbstractModif.py/accept (mod_rh_trackModif.RHTrackAbstractAccept)
# Inactive: /trackAbstractModif.py/commentEdit (mod_rh_trackModif.RHAbstractIntCommentEdit)
# Inactive: /trackAbstractModif.py/commentNew (mod_rh_trackModif.RHAbstractIntCommentNew)
# Inactive: /trackAbstractModif.py/commentRem (mod_rh_trackModif.RHAbstractIntCommentRem)
# Inactive: /trackAbstractModif.py/comments (mod_rh_trackModif.RHAbstractIntComments)
# Inactive: /trackAbstractModif.py/directAccess (mod_rh_trackModif.RHTrackAbstractDirectAccess)
# Inactive: /trackAbstractModif.py/markAsDup (mod_rh_trackModif.RHModAbstractMarkAsDup)
# Inactive: /trackAbstractModif.py/proposeForOtherTracks (mod_rh_trackModif.RHTrackAbstractPropForOtherTracks)
# Inactive: /trackAbstractModif.py/proposeToBeAcc (mod_rh_trackModif.RHTrackAbstractPropToAccept)
# Inactive: /trackAbstractModif.py/proposeToBeRej (mod_rh_trackModif.RHTrackAbstractPropToReject)
# Inactive: /trackAbstractModif.py/reject (mod_rh_trackModif.RHTrackAbstractReject)
# Inactive: /trackAbstractModif.py/unMarkAsDup (mod_rh_trackModif.RHModAbstractUnMarkAsDup)


# Routes for trackModContribList.py
# Inactive: /trackModContribList.py (mod_rh_trackModif.RHContribList)
# Inactive: /trackModContribList.py/contribAction (mod_rh_trackModif.RHContribsActions)
# Inactive: /trackModContribList.py/contribQuickAccess (mod_rh_trackModif.RHContribQuickAccess)
# Inactive: /trackModContribList.py/contribsToPDF (mod_rh_trackModif.RHContribsToPDF)
# Inactive: /trackModContribList.py/participantList (mod_rh_trackModif.RHContribsParticipantList)


# Routes for trackModifAbstracts.py
# Inactive: /trackModifAbstracts.py (mod_rh_trackModif.RHTrackAbstractList)


# Routes for trackModifCoordination.py
# Inactive: /trackModifCoordination.py (mod_rh_trackModif.RHTrackCoordination)


# Routes for trackModification.py
# Inactive: /trackModification.py (mod_rh_trackModif.RHTrackModification)
# Inactive: /trackModification.py/modify (mod_rh_trackModif.RHTrackDataModification)
# Inactive: /trackModification.py/performModify (mod_rh_trackModif.RHTrackPerformDataModification)


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
