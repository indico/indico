from MaKaC.common.general import *

from MaKaC.webinterface.rh import contribReviewingModif

if DEVELOPEMENT:
    contribReviewingModif = reload( contribReviewingModif )


def index( req, **params ):
    return contribReviewingModif.RHContributionGiveAdvice( req ).process( params )

def giveAdvice( req, **params ):
    return contribReviewingModif.RHGiveAdvice( req ).process( params )