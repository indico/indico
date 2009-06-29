from MaKaC.webinterface.rh import reviewingListContribToJudge

def index( req, **params ):
    return reviewingListContribToJudge.RHContribListToJudge( req ).process( params )