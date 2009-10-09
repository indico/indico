from MaKaC.webinterface.rh import reviewingListContribToJudge

def index( req, **params ):
    return reviewingListContribToJudge.RHContribListToJudge( req ).process( params )

def asReviewer( req, **params ):
    return reviewingListContribToJudge.RHContribListToJudgeAsReviewer(req).process(params)

def asEditor( req, **params ):
    return reviewingListContribToJudge.RHContribListToJudgeAsEditor(req).process(params)