# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.contributionReviewing as contributionReviewing
import MaKaC.user as user
from MaKaC.errors import FormValuesError
from MaKaC.errors import MaKaCError
from MaKaC.webinterface.rh.contribMod import RHContribModifBase, RHContribModifBaseReviewingStaffRights
from MaKaC.webinterface.rh.conferenceBase import RHSubmitMaterialBase
from MaKaC.webinterface.rh.contribDisplay import RHContributionMaterialSubmissionRightsBase
from MaKaC.webinterface.rh.contribMod import RCContributionReferee
from MaKaC.webinterface.rh.contribMod import RCContributionEditor
from MaKaC.webinterface.rh.contribMod import RCContributionReviewer
from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager
from MaKaC.webinterface.pages.conferences import WPConferenceModificationClosed
from MaKaC.i18n import _
from MaKaC.paperReviewing import ConferencePaperReview as CPR

#Assign Editor classes
class RHAssignEditorOrReviewerBase(RHContribModifBase):

    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            if not (RCPaperReviewManager.hasRights(self) or RCContributionReferee.hasRights(self)):
                RHContribModifBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

class RHContributionReviewing(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHContributionModifReviewing

    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            RHAssignEditorOrReviewerBase._checkProtection(self)
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _process(self):
        p = contributionReviewing.WPContributionReviewing(self, self._target)
        return p.display()

class RHContributionReviewingJudgements(RHContribModifBase):
    _uh = urlHandlers.UHContributionReviewingJudgements

    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            if not (RCPaperReviewManager.hasRights(self) or RCContributionReferee.hasRights(self)):
                RHContribModifBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _process(self):
        p = contributionReviewing.WPContributionReviewingJudgements(self, self._target)
        return p.display()

class RHContribModifReviewingMaterials(RHContribModifBaseReviewingStaffRights):
    _uh = urlHandlers.UHContribModifReviewingMaterials

    def _checkProtection(self):
        """ This disables people that are not conference managers or track coordinators to
            delete files from a contribution.
        """
        RHContribModifBaseReviewingStaffRights._checkProtection(self)
        for key in self._paramsForCheckProtection.keys():
            if key.find("delete")!=-1:
                RHContribModifBaseReviewingStaffRights._checkProtection(self)

    def _checkParams(self, params):
        RHContribModifBaseReviewingStaffRights._checkParams(self, params)
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]
        self._paramsForCheckProtection = params

    def _process(self):
        if self._target.getOwner().isClosed():
            p = WPConferenceModificationClosed( self, self._target )
            return p.display()

        p = contributionReviewing.WPContributionModifReviewingMaterials( self, self._target )
        return p.display(**self._getRequestParams())

#Assign Referee classes
class RHAssignRefereeBase(RHContribModifBase):

    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            if not RCPaperReviewManager.hasRights(self):
                RHContribModifBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

class RHAssignReferee(RHAssignRefereeBase):
    _uh = urlHandlers.UHAssignReviewing

    def _checkParams( self, params ):
        RHContribModifBase._checkParams( self, params )
        self._referee = int(params.get("refereeAssignSelection"))
        if self._referee == None:
            raise FormValuesError("No referee selected")

    def _process( self ):
        ph = user.PrincipalHolder()
        self._target.getReviewManager().setReferee( ph.getById(self._referee))
        self._redirect( urlHandlers.UHContributionModifReviewing.getURL( self._target ) )

class RHRemoveAssignReferee(RHAssignRefereeBase):
    _uh = urlHandlers.UHRemoveAssignReferee

    def _process( self ):
        self._target.getReviewManager().removeReferee()
        self._redirect( urlHandlers.UHContributionModifReviewing.getURL( self._target ) )

class RHRefereeDueDate(RHAssignRefereeBase):
    _uh = urlHandlers.UHRemoveAssignReferee

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        try:
            self._day = int(params.get('sDay', 0))
            self._month = int(params.get('sMonth', 0))
            self._year = int(params.get('sYear', 0))
            if self._day == 0 or self._month == 0 or self._year == 0:
                raise MaKaCError("Please set the date correctly")
        except Exception:
            raise MaKaCError("Please set the date correctly")


    def _process( self ):
        self._target.getReviewManager().getLastReview().setRefereeDueDate(self._day, self._month, self._year)
        self._redirect( urlHandlers.UHContributionModifReviewing.getURL( self._target ) )



class RHAssignEditing(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHAssignEditing

    def _checkParams( self, params ):
        RHContribModifBase._checkParams( self, params )
        self._editor = int(params.get("editorAssignSelection"))
        if self._editor == None:
            raise FormValuesError("No editor selected")

    def _process( self ):
        choice = self._target.getConference().getConfPaperReview().getChoice()
        if choice == 3 or choice == 4:
            ph = user.PrincipalHolder()
            self._target.getReviewManager().setEditor(ph.getById(self._editor))
        else:
            raise MaKaCError("Reviewing mode does not allow editing")
        self._redirect( urlHandlers.UHContributionModifReviewing.getURL( self._target) )


class RHRemoveAssignEditing(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHRemoveAssignEditing

    def _process( self ):
        self._target.getReviewManager().removeEditor()
        self._redirect( urlHandlers.UHContributionModifReviewing.getURL( self._target ) )

class RHEditorDueDate(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHRemoveAssignReferee

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        try:
            self._day = int(params.get('sDay', 0))
            self._month = int(params.get('sMonth', 0))
            self._year = int(params.get('sYear', 0))
            if self._day == 0 or self._month == 0 or self._year == 0:
                raise MaKaCError("Please set the date correctly")
        except Exception:
            raise MaKaCError("Please set the date correctly")

    def _process( self ):
        self._target.getReviewManager().getLastReview().setEditorDueDate(self._day, self._month, self._year)
        self._redirect( urlHandlers.UHContributionModifReviewing.getURL( self._target ) )

#Assign Reviewer classes
class RHAssignReviewing(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHAssignReviewing

    def _checkParams( self, params ):
        RHContribModifBase._checkParams( self, params )
        self._reviewer = int(params.get("reviewerAssignSelection"))
        if self._reviewer == None:
            raise FormValuesError("No reviewer selected")

    def _process( self ):
        choice = self._target.getConference().getConfPaperReview().getChoice()
        if choice == 2 or choice == 4:
            ph = user.PrincipalHolder()
            self._target.getReviewManager().addReviewer( ph.getById(self._reviewer))
            self._redirect( urlHandlers.UHContributionModifReviewing.getURL( self._target ) )
        else:
            raise MaKaCError("Reviewing mode does not allow content reviewing")

class RHRemoveAssignReviewing(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHRemoveAssignReviewing

    def _checkParams( self, params ):
        RHContribModifBase._checkParams( self, params )
        self._reviewer = int(params.get("reviewerRemoveAssignSelection"))
        if self._reviewer == None:
            raise FormValuesError("No reviewer selected")

    def _process( self ):
        ph = user.PrincipalHolder()
        self._target.getReviewManager().removeReviewer(ph.getById(self._reviewer))
        self._redirect( urlHandlers.UHContributionModifReviewing.getURL( self._target ) )

class RHReviewerDueDate(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHRemoveAssignReferee

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        try:
            self._day = int(params.get('sDay', 0))
            self._month = int(params.get('sMonth', 0))
            self._year = int(params.get('sYear', 0))
            if self._day == 0 or self._month == 0 or self._year == 0:
                raise MaKaCError("Please set the date correctly")
        except Exception:
            raise MaKaCError("Please set the date correctly")

    def _process( self ):
        self._target.getReviewManager().getLastReview().setReviewerDueDate(self._day, self._month, self._year)
        self._redirect( urlHandlers.UHContributionModifReviewing.getURL( self._target ) )



#Judgement classes for referee
class RHFinalJudge(RHContribModifBase):
    _uh = urlHandlers.UHFinalJudge

    def _checkProtection(self):
        if not RCContributionReferee.hasRights(self):
            RHContribModifBase._checkProtection(self);

    def _checkParams( self, params ):
        RHContribModifBase._checkParams( self, params )
        if not (self._target.getReviewManager().getLastReview().isAuthorSubmitted()):
            raise MaKaCError("You must wait until the author has submitted the materials")

        self._questions = params.get("questions")
        self._judgement = params.get("judgement")
        self._comments = params.get("comments")

    def _process( self ):
        if self._judgement == None:
            raise MaKaCError("Select a judgement for this contribution")
        else:
            lastReview = self._target.getReviewManager().getLastReview()
            lastReview.getRefereeJudgement().setAuthor(self._getUser())
            #TODO: this does not work any more now that questions are not Yes/No questions but multiple-answer questions
            #lastReview.getRefereeJudgement().setQuestions(self._questions)
            lastReview.getRefereeJudgement().setComments(self._comments)
            lastReview.getRefereeJudgement().setJudgement(self._judgement)
            #lastReview.setFinalJudgement(self._judgement)
            lastReview.getRefereeJudgement().sendNotificationEmail()
            self._redirect( urlHandlers.UHContributionModifReviewing.getURL( self._target ) )

#Judgement classes for editor
class RHEditorBase(RHContribModifBase):

    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            if not (RCContributionEditor.hasRights(self)):
                raise MaKaCError("Only the editor of this contribution can access this page / perform this request")
                #RHContribModifBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))



    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        if self._target.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() and \
           not self._target.getConference().getConfPaperReview().getChoice() == CPR.LAYOUT_REVIEWING:
            raise MaKaCError("The editor assessment has been submitted")

class RHContributionEditingJudgement(RHEditorBase):
    _uh = urlHandlers.UHContributionEditingJudgement

    def _process(self):
        p = contributionReviewing.WPJudgeEditing(self, self._target)
        return p.display()


class RHJudgeEditing(RHEditorBase):
    _uh = urlHandlers.UHJudgeEditing

    def _checkParams( self, params ):
        RHEditorBase._checkParams( self, params )
        if not (self._target.getReviewManager().getLastReview().isAuthorSubmitted()):
            raise MaKaCError("You must wait until the author has submitted the materials")
        if self._target.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() and \
            not self._target.getConference().getConfPaperReview().getChoice() == CPR.LAYOUT_REVIEWING:
            raise MaKaCError("This contribution has already been assessed by the referee.")
        self._editingJudgement = params.get("editingJudgement")
        self._comments = params.get("comments")
        self._criteria = params.get("criteria")
        self._editor = self.getAW().getUser()

    def _process( self ):

        if self._editingJudgement == None:
            raise MaKaCError("Select an assessment for this contribution")
        else:
            lastReview = self._target.getReviewManager().getLastReview()
            lastReview.getEditorJudgement().setAuthor(self._editor)
            #TODO: this does not work any more now that questions are not Yes/No questions but multiple-answer questions
            #lastReview.getEditorJudgement().setLayoutCriteria(self._criteria)
            lastReview.getEditorJudgement().setJudgement(self._editingJudgement)
            lastReview.getEditorJudgement().setComments(self._comments)
            lastReview.getEditorJudgement().sendNotificationEmail()
            #if self._target.getParent().getConfPaperReview().getChoice() == 3:
            #    self._target.getReviewManager().getLastReview().setFinalJudgement(self._editingJudgement)

            #if self._editingJudgement == "Accept" or self._editingJudgement == "Reject":
            if self._editingJudgement == "1" or self._editingJudgement == "3":
                self._redirect( urlHandlers.UHContributionEditingJudgement.getURL( self._target ))
            else:
                self._redirect( urlHandlers.UHContributionModifReviewing.getURL( self._target ))

#Judgement classes for reviewer
class RHReviewerBase(RHContribModifBase):

    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            if not (RCContributionReviewer.hasRights(self)):
                raise MaKaCError("Only the reviewer of this contribution can access this page / perform this request")
                #RHContribModifBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))



    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        if self._target.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted():
            raise MaKaCError("The content assessment has been submitted")

class RHContributionGiveAdvice(RHReviewerBase):
    _uh = urlHandlers.UHContributionGiveAdvice

    def _checkParams(self, params):
        RHReviewerBase._checkParams(self, params)
        self._editAdvice = params.get("edit", False)

    def _process(self):
        p = contributionReviewing.WPGiveAdvice(self, self._target)
        return p.display()


class RHGiveAdvice(RHReviewerBase):
    _uh = urlHandlers.UHGiveAdvice

    def _checkParams( self, params ):
        RHReviewerBase._checkParams( self, params )
        if not (self._target.getReviewManager().getLastReview().isAuthorSubmitted()):
            raise MaKaCError("You must wait until the author has submitted the materials")
        if self._target.getReviewManager().getLastReview().isSubmitted():
            raise MaKaCError("This contribution has already been assessed by the referee.")
        self._reviewer = self.getAW().getUser()
        self._questions = params.get("questions")
        self._adviceJudgement = params.get("adviceJudgement")
        self._comments = params.get("comments")
        self._questions = params.get("questions")

    def _process( self ):
        if self._adviceJudgement == None:
            raise MaKaCError("Select an assessment for this contribution")
        else:
            lastReview = self._target.getReviewManager().getLastReview()
            lastReview.addReviewerJudgement(self._reviewer)
            reviewerJudgement = lastReview.getReviewerJudgement(self._reviewer)
            #TODO: this does not work any more now that questions are not Yes/No questions but multiple-answer questions
            #reviewerJudgement.setQuestions(self._questions)
            reviewerJudgement.setComments(self._comments)
            reviewerJudgement.setJudgement(self._adviceJudgement)
            reviewerJudgement.sendNotificationEmail()

            self._redirect( urlHandlers.UHContributionGiveAdvice.getURL( self._target ))

#Classes for the author
class RHReviewingAuthorBase(RHContributionMaterialSubmissionRightsBase):

    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            RHContributionMaterialSubmissionRightsBase._checkProtection(self)
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

class RHSubmitForReviewing(RHReviewingAuthorBase):
    _uh = urlHandlers.UHContributionDisplay

    def _process (self):
        self._target.getReviewManager().getLastReview().setAuthorSubmitted(True)
        self._redirect(urlHandlers.UHContributionDisplay.getURL(self._target))

class RHRemoveSubmittedMarkForReviewing(RHReviewingAuthorBase):
    _uh = urlHandlers.UHContributionDisplay

    def _checkParams(self, params):
        RHContributionMaterialSubmissionRightsBase._checkParams(self, params)
        if self._target.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() or \
        (self._target.getReviewManager().getLastReview().getEditorJudgement().isSubmitted() and self._target.getConference().getConfPaperReview().getChoice() == CPR.LAYOUT_REVIEWING):
            raise MaKaCError("This contribution has already been judged. You cannot un-submit the materials")

    def _process (self):
        self._target.getReviewManager().getLastReview().setAuthorSubmitted(False)
        self._redirect(urlHandlers.UHContributionDisplay.getURL(self._target))

#class to show reviewing history
class RHReviewingHistory(RHContribModifBaseReviewingStaffRights):
    _uh = urlHandlers.UHContributionModifReviewing

    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            RHContribModifBaseReviewingStaffRights._checkProtection(self)
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _process(self):
        p = contributionReviewing.WPContributionReviewingHistory(self, self._target)
        return p.display()