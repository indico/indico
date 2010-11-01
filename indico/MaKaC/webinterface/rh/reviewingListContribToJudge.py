import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.pages.reviewing import WPConfListContribToJudge
from MaKaC.webinterface.pages.reviewing import WPConfListContribToJudgeAsReviewer
from MaKaC.webinterface.pages.reviewing import WPConfListContribToJudgeAsEditor
from MaKaC.errors import MaKaCError

class RHContribListToJudge(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifListContribToJudge

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            confReview = self._conf.getConfReview()
            user = self.getAW().getUser()
            if not (confReview.isReferee(user)):
                raise MaKaCError(_("Only the referees can access this page"))
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        p = WPConfListContribToJudge(self, self._target)
        return p.display()


class RHContribListToJudgeAsReviewer(RHContribListToJudge):
    _uh = urlHandlers.UHConfModifListContribToJudgeAsReviewer

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            confReview = self._conf.getConfReview()
            user = self.getAW().getUser()
            if not (confReview.isReviewer(user)):
                raise MaKaCError(_("Only the content reviewers can access this page"))
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _process( self ):
        p = WPConfListContribToJudgeAsReviewer(self, self._target)
        return p.display()

class RHContribListToJudgeAsEditor(RHContribListToJudge):
    _uh = urlHandlers.UHConfModifListContribToJudgeAsEditor

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            confReview = self._conf.getConfReview()
            user = self.getAW().getUser()
            if not (confReview.isEditor(user)):
                raise MaKaCError(_("Only the layout reviewers can access this page"))
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))

    def _process( self ):
        p = WPConfListContribToJudgeAsEditor(self, self._target)
        return p.display()