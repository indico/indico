from MaKaC.common.general import DEVELOPMENT
from MaKaC.webinterface.rh import reviewingUserCompetencesModif

if DEVELOPMENT:
    reviewingUserCompetencesModif = reload( reviewingUserCompetencesModif )

def index( req, **params ):
    return reviewingUserCompetencesModif.RHConfModifUserCompetences( req ).process( params )

def Abstracts ( req, **params ):
    return reviewingUserCompetencesModif.RHConfModifUserCompetencesAbstracts( req ).process( params )

def modifyCompetences( req, **params ):
    return reviewingUserCompetencesModif.RHConfModifModifyUserCompetences( req ).process( params )