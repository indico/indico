# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from indico.modules.events.contributions.controllers.management import RHManageContributionBase
from indico.util.i18n import _
from indico.web.flask.util import url_for

import MaKaC.user as user
import MaKaC.webinterface.pages.contributionReviewing as contributionReviewing
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.errors import FormValuesError, MaKaCError
from MaKaC.paperReviewing import ConferencePaperReview as CPR
from MaKaC.webinterface.rh.contribMod import (RCContributionEditor,
                                              RCContributionReferee,
                                              RCContributionReviewer,
                                              RCContributionPaperReviewingStaff)
from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager


class RHManageContributionReviewingBase(RHManageContributionBase):
    def _checkParams(self, params):
        RHManageContributionBase._checkParams(self, params)
        self._rm = self._conf.getReviewManager(self.contrib)


class RHContribModifBaseReviewingStaffRights(RHManageContributionReviewingBase):
    """ Base class for any RH where a member of the Paper Reviewing staff
        (a PRM, or a Referee / Editor / Reviewer of the target contribution)
        has the rights to perform the request
    """

    def _checkProtection(self):
        if not RCContributionPaperReviewingStaff.hasRights(self):
            RHManageContributionReviewingBase._checkProtection(self)


class RHAssignEditorOrReviewerBase(RHManageContributionReviewingBase):

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            if not (RCPaperReviewManager.hasRights(self) or RCContributionReferee.hasRights(self)):
                RHManageContributionReviewingBase._checkProtection(self)
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))


class RHContributionReviewing(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHContributionModifReviewing

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            RHAssignEditorOrReviewerBase._checkProtection(self)
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _process(self):
        p = contributionReviewing.WPContributionReviewing(self, self.contrib)
        return p.display()


class RHContributionReviewingJudgements(RHManageContributionReviewingBase):
    _uh = urlHandlers.UHContributionReviewingJudgements

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            if self._target.getConfPaperReview().getChoice() == CPR.NO_REVIEWING:
                raise MaKaCError(_("Type of reviewing has not been chosen yet"))
            elif not (RCPaperReviewManager.hasRights(self) or RCContributionReferee.hasRights(self)):
                RHManageContributionReviewingBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _process(self):
        p = contributionReviewing.WPContributionReviewingJudgements(self, self.contrib)
        return p.display()


class RHAssignRefereeBase(RHManageContributionReviewingBase):

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            if not RCPaperReviewManager.hasRights(self):
                RHManageContributionReviewingBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

class RHAssignReferee(RHAssignRefereeBase):
    _uh = urlHandlers.UHAssignReviewing

    def _checkParams( self, params ):
        RHManageContributionReviewingBase._checkParams( self, params )
        self._referee = int(params.get("refereeAssignSelection"))
        if self._referee == None:
            raise FormValuesError("No referee selected")

    def _process( self ):
        self._rm.setReferee(user.AvatarHolder().getById(self._referee))
        self._redirect(url_for('event_mgmt.contributionReviewing', self.contrib))

class RHRemoveAssignReferee(RHAssignRefereeBase):
    _uh = urlHandlers.UHRemoveAssignReferee

    def _process(self):
        self._rm.removeReferee()
        self._redirect(url_for('event_mgmt.contributionReviewing', self.contrib))


class RHAssignEditing(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHAssignEditing

    def _checkParams( self, params ):
        RHManageContributionReviewingBase._checkParams( self, params )
        self._editor = int(params.get("editorAssignSelection"))
        if self._editor == None:
            raise FormValuesError("No editor selected")

    def _process( self ):
        choice = self._target.getConference().getConfPaperReview().getChoice()
        if choice == 3 or choice == 4:
            self._rm.setEditor(user.AvatarHolder().getById(self._editor))
        else:
            raise MaKaCError("Reviewing mode does not allow editing")
        self._redirect(url_for('event_mgmt.contributionReviewing', self.contrib))


class RHRemoveAssignEditing(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHRemoveAssignEditing

    def _process( self ):
        self._rm.removeEditor()
        self._redirect(url_for('event_mgmt.contributionReviewing', self.contrib))


#Assign Reviewer classes
class RHAssignReviewing(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHAssignReviewing

    def _checkParams( self, params ):
        RHManageContributionReviewingBase._checkParams( self, params )
        self._reviewer = int(params.get("reviewerAssignSelection"))
        if self._reviewer == None:
            raise FormValuesError("No reviewer selected")

    def _process( self ):
        choice = self._target.getConference().getConfPaperReview().getChoice()
        if choice == 2 or choice == 4:
            self._rm.addReviewer(user.AvatarHolder().getById(self._reviewer))
            self._redirect(url_for('event_mgmt.contributionReviewing', self.contrib))
        else:
            raise MaKaCError("Reviewing mode does not allow content reviewing")

class RHRemoveAssignReviewing(RHAssignEditorOrReviewerBase):
    _uh = urlHandlers.UHRemoveAssignReviewing

    def _checkParams( self, params ):
        RHManageContributionReviewingBase._checkParams( self, params )
        self._reviewer = int(params.get("reviewerRemoveAssignSelection"))
        if self._reviewer == None:
            raise FormValuesError("No reviewer selected")

    def _process(self):
        self._rm.removeReviewer(user.AvatarHolder().getById(self._reviewer))
        self._redirect(url_for('event_mgmt.contributionReviewing', self.contrib))


#Judgement classes for editor
class RHEditorBase(RHManageContributionReviewingBase):

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
        RHManageContributionReviewingBase._checkParams(self, params)
        paper_review = self._conf.getReviewManager(self.contrib)
        if paper_review.getLastReview().getRefereeJudgement().isSubmitted() and \
           not paper_review.getChoice() == CPR.LAYOUT_REVIEWING:
            raise MaKaCError("The editor assessment has been submitted")

class RHContributionEditingJudgement(RHEditorBase):
    _uh = urlHandlers.UHContributionEditingJudgement

    def _process(self):
        p = contributionReviewing.WPJudgeEditing(self, self.contrib)
        return p.display()


#Judgement classes for reviewer
class RHReviewerBase(RHManageContributionReviewingBase):

    def _checkProtection(self):
        paper_review = self._conf.getConfPaperReview()
        if self._target.getConference().hasEnabledSection("paperReviewing"):
            if not paper_review.getChoice() in (CPR.CONTENT_REVIEWING, CPR.CONTENT_AND_LAYOUT_REVIEWING):
                raise MaKaCError(_("Content Reviewing is not active for this conference"))
            elif not (RCContributionReviewer.hasRights(self)):
                raise MaKaCError("Only the reviewer of this contribution can access this page / perform this request")
                #RHContribModifBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _checkParams(self, params):
        RHManageContributionReviewingBase._checkParams(self, params)
        paper_review = self._conf.getReviewManager(self.contrib)
        if paper_review.getLastReview().getRefereeJudgement().isSubmitted():
            raise MaKaCError("The content assessment has been submitted")


class RHContributionGiveAdvice(RHReviewerBase):
    _uh = urlHandlers.UHContributionGiveAdvice

    def _checkParams(self, params):
        RHReviewerBase._checkParams(self, params)
        self._editAdvice = params.get("edit", False)

    def _process(self):
        p = contributionReviewing.WPGiveAdvice(self, self.contrib)
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
        p = contributionReviewing.WPContributionReviewingHistory(self, self.contrib)
        return p.display()
