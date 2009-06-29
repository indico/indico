from MaKaC.webinterface.rh import reviewingAssignContributions

def index( req, **params ):
    return reviewingAssignContributions.RHReviewingAssignContributionsList( req ).process( params )