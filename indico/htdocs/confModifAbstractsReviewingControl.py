
from MaKaC.webinterface.rh import reviewingControlModif

def index( req, **params ):
    return reviewingControlModif.RHConfModifReviewingAbstractsControl( req ).process( params )

def selectAbstractManager(req, **params):
    return reviewingControlModif.RHConfSelectAbstractManager(req).process(params)

def addAbstractManager(req, **params):
    return reviewingControlModif.RHConfAddAbstractManager(req).process(params)

def removeAbstractManager(req, **params):
    return reviewingControlModif.RHConfRemoveAbstractManager(req).process(params)

def selectAbstractReviewer(req, **params):
    return reviewingControlModif.RHConfSelectAbstractReviewer(req).process(params)

def addAbstractReviewer(req, **params):
    return reviewingControlModif.RHConfAddAbstractReviewer(req).process(params)

def removeAbstractReviewer(req, **params):
    return reviewingControlModif.RHConfRemoveAbstractReviewer(req).process(params)