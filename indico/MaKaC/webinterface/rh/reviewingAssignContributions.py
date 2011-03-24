import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.pages.reviewing import WPConfReviewingAssignContributions
from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager, RCReferee
from MaKaC.errors import MaKaCError
from MaKaC.common.contribPacker import ZIPFileHandler, ReviewingPacker
from MaKaC.common import Config

class RHReviewingAssignContributionsList(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifListContribToJudge

    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self) and not RCReferee.hasRights(self):
            RHConferenceModifBase._checkProtection(self)

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        p = WPConfReviewingAssignContributions(self, self._target)
        return p.display()


class RHDownloadAcceptedPapers(RHConferenceModifBase):

    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self):
            RHConferenceModifBase._checkProtection(self)

    def _process( self ):
        p = ReviewingPacker(self._conf)
        path = p.pack(ZIPFileHandler())
        filename = "accepted-papers.zip"
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "ZIP" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        self._req.sendfile(path)

