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

from MaKaC.webinterface.rh import abstractModif, abstractReviewing, conferenceModif
from indico.web.flask.blueprints.event.management import event_mgmt


# Setup
event_mgmt.add_url_rule('/call-for-abstracts/setup/', 'confModifCFA', conferenceModif.RHConfModifCFA)
event_mgmt.add_url_rule('/call-for-abstracts/setup/toggle', 'confModifCFA-changeStatus',
                        conferenceModif.RHConfModifCFAStatus, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/setup/modify', 'confModifCFA-modifyData',
                        conferenceModif.RHCFADataModification, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/setup/modify/save', 'confModifCFA-performModifyData',
                        conferenceModif.RHCFAPerformDataModification, methods=('POST',))

# Setup: fields
event_mgmt.add_url_rule('/call-for-abstracts/setup/fields/<fieldId>/toggle', 'confModifCFA-abstractFields',
                        conferenceModif.RHConfAbstractFields)
event_mgmt.add_url_rule('/call-for-abstracts/setup/fields/<fieldId>/down', 'confModifCFA-absFieldDown',
                        conferenceModif.RHConfMoveAbsFieldDown)
event_mgmt.add_url_rule('/call-for-abstracts/setup/fields/<fieldId>/up', 'confModifCFA-absFieldUp',
                        conferenceModif.RHConfMoveAbsFieldUp, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/setup/fields/remove', 'confModifCFA-removeAbstractField',
                        conferenceModif.RHConfRemoveAbstractField, methods=('POST',))

# Setup: misc options
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/attach-files', 'confModifCFA-switchAttachFiles',
                        conferenceModif.RHConfModifCFASwitchAttachFiles)
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/multiple-tracks', 'confModifCFA-switchMultipleTracks',
                        conferenceModif.RHConfModifCFASwitchMultipleTracks)
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/mandatory-speaker',
                        'confModifCFA-switchSelectSpeakerMandatory',
                        conferenceModif.RHConfModifCFASwitchSelectSpeakerMandatory)
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/show-attachments', 'confModifCFA-switchShowAttachedFiles',
                        conferenceModif.RHConfModifCFASwitchShowAttachedFilesContribList)
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/select-speaker', 'confModifCFA-switchShowSelectSpeaker',
                        conferenceModif.RHConfModifCFASwitchShowSelectAsSpeaker)
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/mandatory-tracks', 'confModifCFA-makeTracksMandatory',
                        conferenceModif.RHConfModifCFAMakeTracksMandatory)

# Preview
event_mgmt.add_url_rule('/call-for-abstracts/preview', 'confModifCFA-preview', conferenceModif.RHConfModifCFAPreview,
                        methods=('GET', 'POST'))

# List of abstracts
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/', 'abstractsManagment', conferenceModif.RHAbstractList,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/direct-access', 'abstractManagment-directAccess',
                        abstractModif.RHAbstractDirectAccess, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/new', 'abstractsManagment-newAbstract',
                        conferenceModif.RHNewAbstract, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/perform-action', 'abstractsManagment-abstractsActions',
                        conferenceModif.RHAbstractsActions, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/merge', 'abstractsManagment-mergeAbstracts',
                        conferenceModif.RHAbstractsMerge, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/participants', 'abstractsManagment-participantList',
                        conferenceModif.RHAbstractsParticipantList, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/accept', 'abstractManagment-acceptMultiple',
                        conferenceModif.RHAbstractManagmentAcceptMultiple, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/reject', 'abstractManagment-rejectMultiple',
                        conferenceModif.RHAbstractManagmentRejectMultiple, methods=('POST',))

# Abstract: main
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/', 'abstractManagment',
                        abstractModif.RHAbstractManagment, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/abstract.pdf', 'abstractManagment-abstractToPDF',
                        abstractModif.RHAbstractToPDF)
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/abstract.xml', 'abstractManagment-xml',
                        abstractModif.RHAbstractToXML)
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/modify', 'abstractManagment-editData',
                        abstractModif.RHEditData, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/change-track', 'abstractManagment-changeTrack',
                        abstractModif.RHAbstractManagmentChangeTrack, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/reset-status', 'abstractManagment-backToSubmitted',
                        abstractModif.RHBackToSubmitted)
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/accept', 'abstractManagment-accept',
                        abstractModif.RHAbstractManagmentAccept, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/reject', 'abstractManagment-reject',
                        abstractModif.RHAbstractManagmentReject, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/dupe', 'abstractManagment-markAsDup',
                        abstractModif.RHMarkAsDup, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/dupe/undo', 'abstractManagment-unMarkAsDup',
                        abstractModif.RHUnMarkAsDup, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/merge', 'abstractManagment-mergeInto',
                        abstractModif.RHMergeInto, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/merge/undo', 'abstractManagment-unmerge',
                        abstractModif.RHUnMerge, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/propose/accept', 'abstractManagment-propToAcc',
                        abstractModif.RHPropToAcc, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/propose/reject', 'abstractManagment-propToRej',
                        abstractModif.RHPropToRej, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/withdraw', 'abstractManagment-withdraw',
                        abstractModif.RHWithdraw, methods=('POST',))

# Abstract: Track judgments
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/tracks/judgements',
                        'abstractManagment-trackProposal', abstractModif.RHAbstractTrackManagment,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/tracks/ratings', 'abstractManagment-orderByRating',
                        abstractModif.RHAbstractTrackOrderByRating)

# Abstract: Internal comments
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/comments/', 'abstractManagment-comments',
                        abstractModif.RHIntComments)
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/comments/add', 'abstractManagment-newComment',
                        abstractModif.RHNewIntComment, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/comments/<intCommentId>/edit',
                        'abstractManagment-editComment', abstractModif.RHIntCommentEdit, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/comments/<intCommentId>/delete',
                        'abstractManagment-remComment', abstractModif.RHIntCommentRem, methods=('POST',))

# Abstract: Notification log
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/notifications', 'abstractManagment-notifLog',
                        abstractModif.RHNotifLog)

# Abstract: Tools
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/tools/', 'abstractTools', abstractModif.RHTools)
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/tools/delete', 'abstractTools-delete',
                        abstractModif.RHAbstractDelete, methods=('GET', 'POST'))

# Book of abstracts
event_mgmt.add_url_rule('/call-for-abstracts/book/', 'confModBOA', conferenceModif.RHAbstractBook,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/book/options/show-ids', 'confModBOA-toogleShowIds',
                        conferenceModif.RHAbstractBookToogleShowIds)

# Reviewing: setup
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/setup', 'abstractReviewing-reviewingSetup',
                        abstractReviewing.RHAbstractReviewingSetup)

# Reviewing: team
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/team', 'abstractReviewing-reviewingTeam',
                        abstractReviewing.RHAbstractReviewingTeam)


# Reviewing: notification templates
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/', 'abstractReviewing-notifTpl',
                        abstractReviewing.RHNotifTpl)
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/add', 'abstractReviewing-notifTplNew',
                        abstractReviewing.RHCFANotifTplNew, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/remove', 'abstractReviewing-notifTplRem',
                        abstractReviewing.RHCFANotifTplRem, methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/',
                        'abstractReviewing-notifTplDisplay', abstractReviewing.RHCFANotifTplDisplay)
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/down',
                        'abstractReviewing-notifTplDown', abstractReviewing.RHCFANotifTplDown)
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/up', 'abstractReviewing-notifTplUp',
                        abstractReviewing.RHCFANotifTplUp)
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/modify',
                        'abstractReviewing-notifTplEdit', abstractReviewing.RHCFANotifTplEdit, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/preview',
                        'abstractReviewing-notifTplPreview', abstractReviewing.RHCFANotifTplPreview)
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/condition/add',
                        'abstractReviewing-notifTplCondNew', abstractReviewing.RHNotifTplConditionNew,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/condition/remove',
                        'abstractReviewing-notifTplCondRem', abstractReviewing.RHNotifTplConditionRem,
                        methods=('GET', 'POST'))
