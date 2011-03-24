from MaKaC.webinterface.rh import reviewingAssignContributions

def index( req, **params ):
    return reviewingAssignContributions.RHReviewingAssignContributionsList( req ).process( params )

def downloadAcceptedPapers(req, **params):
    return reviewingAssignContributions.RHDownloadAcceptedPapers(req).process(params)
