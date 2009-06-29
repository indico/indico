from MaKaC.common.general import DEVELOPEMENT
from MaKaC.webinterface.rh import reviewingUserCompetencesModif

if DEVELOPEMENT:
    reviewingUserCompetencesModif = reload( reviewingUserCompetencesModif )

def index( req, **params ):
    return reviewingUserCompetencesModif.RHConfModifUserCompetences( req ).process( params )

def modifyCompetences( req, **params ):
    return reviewingUserCompetencesModif.RHConfModifModifyUserCompetences( req ).process( params )