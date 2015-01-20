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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.contributionReviewing as contributionReviewing
import MaKaC.user as user
from MaKaC.errors import FormValuesError
from MaKaC.errors import MaKaCError
from MaKaC.webinterface.rh.contribMod import RHContribModifBase, RHContribModifBaseReviewingStaffRights
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
            if self._target.getConference().getConfPaperReview().getChoice() == CPR.NO_REVIEWING:
                raise MaKaCError(_("Type of reviewing has not been chosen yet"))
            elif not (RCPaperReviewManager.hasRights(self) or RCContributionReferee.hasRights(self)):
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


#Judgement classes for editor
class RHEditorBase(RHContribModifBase):

    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            if not self._target.getConference().getConfPaperReview().getChoice() in [CPR.LAYOUT_REVIEWING, CPR.CONTENT_AND_LAYOUT_REVIEWING]:
                raise MaKaCError(_("Layout Reviewing is not active for this conference"))
            elif not (RCContributionEditor.hasRights(self)):
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


#Judgement classes for reviewer
class RHReviewerBase(RHContribModifBase):

    def _checkProtection(self):
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            if not self._target.getConference().getConfPaperReview().getChoice() in [CPR.CONTENT_REVIEWING, CPR.CONTENT_AND_LAYOUT_REVIEWING]:
                raise MaKaCError(_("Content Reviewing is not active for this conference"))
            elif not (RCContributionReviewer.hasRights(self)):
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
