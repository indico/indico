from MaKaC.common.general import *

from MaKaC.webinterface.rh import contribReviewingModif

if DEVELOPMENT:
    contribReviewingModif = reload( contribReviewingModif )


def index( req, **params ):
    return contribReviewingModif.RHContributionEditingJudgement( req ).process( params )

def judgeEditing( req, **params ):
    return contribReviewingModif.RHJudgeEditing( req ).process( params )