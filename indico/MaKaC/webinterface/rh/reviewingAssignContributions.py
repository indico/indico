import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.pages.reviewing import WPConfReviewingAssignContributions
from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager, RCReferee
from MaKaC.errors import MaKaCError

class RHReviewingAssignContributionsList(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifListContribToJudge
    
    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            if not RCPaperReviewManager.hasRights(self) and not RCReferee.hasRights(self):
                RHConferenceModifBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))
        
    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        p = WPConfReviewingAssignContributions(self, self._target)
        return p.display()