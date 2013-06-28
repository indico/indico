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

from MaKaC.webinterface.rh import abstractModif, abstractReviewing, conferenceModif
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.management import event_mgmt


# Setup
event_mgmt.add_url_rule('/call-for-abstracts/setup/', 'confModifCFA', rh_as_view(conferenceModif.RHConfModifCFA))
event_mgmt.add_url_rule('/call-for-abstracts/setup/toggle', 'confModifCFA-changeStatus',
                        rh_as_view(conferenceModif.RHConfModifCFAStatus), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/setup/modify', 'confModifCFA-modifyData',
                        rh_as_view(conferenceModif.RHCFADataModification), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/setup/modify/save', 'confModifCFA-performModifyData',
                        rh_as_view(conferenceModif.RHCFAPerformDataModification), methods=('POST',))

# Setup: fields
event_mgmt.add_url_rule('/call-for-abstracts/setup/fields/<fieldId>/', 'confModifCFA-editAbstractField',
                        rh_as_view(conferenceModif.RHConfEditAbstractField), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/setup/fields/<fieldId>/toggle', 'confModifCFA-abstractFields',
                        rh_as_view(conferenceModif.RHConfAbstractFields))
event_mgmt.add_url_rule('/call-for-abstracts/setup/fields/<fieldId>/down', 'confModifCFA-absFieldDown',
                        rh_as_view(conferenceModif.RHConfMoveAbsFieldDown))
event_mgmt.add_url_rule('/call-for-abstracts/setup/fields/<fieldId>/up', 'confModifCFA-absFieldUp',
                        rh_as_view(conferenceModif.RHConfMoveAbsFieldUp), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/setup/fields/add', 'confModifCFA-addAbstractField',
                        rh_as_view(conferenceModif.RHConfAddAbstractField), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/setup/fields/save', 'confModifCFA-performAddAbstractField',
                        rh_as_view(conferenceModif.RHConfPerformAddAbstractField), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/setup/fields/remove', 'confModifCFA-removeAbstractField',
                        rh_as_view(conferenceModif.RHConfRemoveAbstractField), methods=('POST',))

# Setup: misc options
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/attach-files', 'confModifCFA-switchAttachFiles',
                        rh_as_view(conferenceModif.RHConfModifCFASwitchAttachFiles))
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/multiple-tracks', 'confModifCFA-switchMultipleTracks',
                        rh_as_view(conferenceModif.RHConfModifCFASwitchMultipleTracks))
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/mandatory-speaker',
                        'confModifCFA-switchSelectSpeakerMandatory',
                        rh_as_view(conferenceModif.RHConfModifCFASwitchSelectSpeakerMandatory))
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/show-attachments', 'confModifCFA-switchShowAttachedFiles',
                        rh_as_view(conferenceModif.RHConfModifCFASwitchShowAttachedFilesContribList))
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/select-speaker', 'confModifCFA-switchShowSelectSpeaker',
                        rh_as_view(conferenceModif.RHConfModifCFASwitchShowSelectAsSpeaker))
event_mgmt.add_url_rule('/call-for-abstracts/setup/options/mandatory-tracks', 'confModifCFA-makeTracksMandatory',
                        rh_as_view(conferenceModif.RHConfModifCFAMakeTracksMandatory))

# Preview
event_mgmt.add_url_rule('/call-for-abstracts/preview', 'confModifCFA-preview',
                        rh_as_view(conferenceModif.RHConfModifCFAPreview), methods=('GET', 'POST'))

# List of abstracts
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/', 'abstractsManagment',
                        rh_as_view(conferenceModif.RHAbstractList), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/direct-access', 'abstractManagment-directAccess',
                        rh_as_view(abstractModif.RHAbstractDirectAccess), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/new', 'abstractsManagment-newAbstract',
                        rh_as_view(conferenceModif.RHNewAbstract), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/perform-action', 'abstractsManagment-abstractsActions',
                        rh_as_view(conferenceModif.RHAbstractsActions), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/merge', 'abstractsManagment-mergeAbstracts',
                        rh_as_view(conferenceModif.RHAbstractsMerge), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/participants', 'abstractsManagment-participantList',
                        rh_as_view(conferenceModif.RHAbstractsParticipantList), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/accept', 'abstractManagment-acceptMultiple',
                        rh_as_view(conferenceModif.RHAbstractManagmentAcceptMultiple), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/reject', 'abstractManagment-rejectMultiple',
                        rh_as_view(conferenceModif.RHAbstractManagmentRejectMultiple), methods=('POST',))

# Abstract: main
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/', 'abstractManagment',
                        rh_as_view(abstractModif.RHAbstractManagment))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/abstract.pdf', 'abstractManagment-abstractToPDF',
                        rh_as_view(abstractModif.RHAbstractToPDF))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/abstract.xml', 'abstractManagment-xml',
                        rh_as_view(abstractModif.RHAbstractToXML))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/modify', 'abstractManagment-editData',
                        rh_as_view(abstractModif.RHEditData), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/change-track', 'abstractManagment-changeTrack',
                        rh_as_view(abstractModif.RHAbstractManagmentChangeTrack), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/reset-status', 'abstractManagment-backToSubmitted',
                        rh_as_view(abstractModif.RHBackToSubmitted))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/accept', 'abstractManagment-accept',
                        rh_as_view(abstractModif.RHAbstractManagmentAccept), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/reject', 'abstractManagment-reject',
                        rh_as_view(abstractModif.RHAbstractManagmentReject), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/dupe', 'abstractManagment-markAsDup',
                        rh_as_view(abstractModif.RHMarkAsDup), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/dupe/undo', 'abstractManagment-unMarkAsDup',
                        rh_as_view(abstractModif.RHUnMarkAsDup), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/merge', 'abstractManagment-mergeInto',
                        rh_as_view(abstractModif.RHMergeInto), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/merge/undo', 'abstractManagment-unmerge',
                        rh_as_view(abstractModif.RHUnMerge), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/propose/accept', 'abstractManagment-propToAcc',
                        rh_as_view(abstractModif.RHPropToAcc), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/propose/reject', 'abstractManagment-propToRej',
                        rh_as_view(abstractModif.RHPropToRej), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/withdraw', 'abstractManagment-withdraw',
                        rh_as_view(abstractModif.RHWithdraw), methods=('POST',))

# Abstract: Track judgments
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/tracks/judgements',
                        'abstractManagment-trackProposal', rh_as_view(abstractModif.RHAbstractTrackManagment))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/tracks/ratings', 'abstractManagment-orderByRating',
                        rh_as_view(abstractModif.RHAbstractTrackOrderByRating))

# Abstract: Internal comments
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/comments/', 'abstractManagment-comments',
                        rh_as_view(abstractModif.RHIntComments))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/comments/add', 'abstractManagment-newComment',
                        rh_as_view(abstractModif.RHNewIntComment), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/comments/<intCommentId>/edit',
                        'abstractManagment-editComment', rh_as_view(abstractModif.RHIntCommentEdit), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/comments/<intCommentId>/delete',
                        'abstractManagment-remComment', rh_as_view(abstractModif.RHIntCommentRem), methods=('POST',))

# Abstract: Notification log
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/notifications', 'abstractManagment-notifLog',
                        rh_as_view(abstractModif.RHNotifLog))

# Abstract: Tools
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/tools/', 'abstractTools',
                        rh_as_view(abstractModif.RHTools))
event_mgmt.add_url_rule('/call-for-abstracts/abstracts/<abstractId>/tools/delete', 'abstractTools-delete',
                        rh_as_view(abstractModif.RHAbstractDelete), methods=('GET', 'POST'))

# Book of abstracts
event_mgmt.add_url_rule('/call-for-abstracts/book/', 'confModBOA', rh_as_view(conferenceModif.RHAbstractBook),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/book/options/show-ids', 'confModBOA-toogleShowIds',
                        rh_as_view(conferenceModif.RHAbstractBookToogleShowIds))

# Reviewing: setup
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/setup', 'abstractReviewing-reviewingSetup',
                        rh_as_view(abstractReviewing.RHAbstractReviewingSetup))

# Reviewing: team
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/team', 'abstractReviewing-reviewingTeam',
                        rh_as_view(abstractReviewing.RHAbstractReviewingTeam))


# Reviewing: notification templates
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/', 'abstractReviewing-notifTpl',
                        rh_as_view(abstractReviewing.RHNotifTpl))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/add', 'abstractReviewing-notifTplNew',
                        rh_as_view(abstractReviewing.RHCFANotifTplNew), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/remove', 'abstractReviewing-notifTplRem',
                        rh_as_view(abstractReviewing.RHCFANotifTplRem), methods=('POST',))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/',
                        'abstractReviewing-notifTplDisplay', rh_as_view(abstractReviewing.RHCFANotifTplDisplay))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/down',
                        'abstractReviewing-notifTplDown', rh_as_view(abstractReviewing.RHCFANotifTplDown))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/up', 'abstractReviewing-notifTplUp',
                        rh_as_view(abstractReviewing.RHCFANotifTplUp))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/modify',
                        'abstractReviewing-notifTplEdit', rh_as_view(abstractReviewing.RHCFANotifTplEdit),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/preview',
                        'abstractReviewing-notifTplPreview', rh_as_view(abstractReviewing.RHCFANotifTplPreview))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/condition/add',
                        'abstractReviewing-notifTplCondNew', rh_as_view(abstractReviewing.RHNotifTplConditionNew),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/call-for-abstracts/reviewing/notifications/<notifTplId>/condition/remove',
                        'abstractReviewing-notifTplCondRem', rh_as_view(abstractReviewing.RHNotifTplConditionRem),
                        methods=('GET', 'POST'))
