import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.pages.reviewing import WPConfListContribToJudge
from MaKaC.errors import MaKaCError

class RHContribListToJudge(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifListContribToJudge
    
    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            confReview = self._conf.getConfReview()
            user = self.getAW().getUser()
            if not (confReview.isReferee(user) or confReview.isEditor(user) or confReview.isReviewer(user)):
                RHConferenceModifBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))
        
    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        p = WPConfListContribToJudge(self, self._target)
        return p.display()