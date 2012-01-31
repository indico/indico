# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

from MaKaC.common.general import DEVELOPMENT
from MaKaC.webinterface.rh import reviewingControlModif

if DEVELOPMENT:
    reviewingControlModif = reload( reviewingControlModif )

def index( req, **params ):
    return reviewingControlModif.RHConfModifReviewingControl( req ).process( params )

def selectPaperReviewManager(req, **params):
    return reviewingControlModif.RHConfSelectPaperReviewManager(req).process(params)

def addPaperReviewManager(req, **params):
    return reviewingControlModif.RHConfAddPaperReviewManager(req).process(params)

def removePaperReviewManager(req, **params):
    return reviewingControlModif.RHConfRemovePaperReviewManager(req).process(params)


def selectEditor(req, **params):
    return reviewingControlModif.RHConfSelectEditor(req).process(params)

def addEditor(req, **params):
    return reviewingControlModif.RHConfAddEditor(req).process(params)

def removeEditor(req, **params):
    return reviewingControlModif.RHConfRemoveEditor(req).process(params)

def selectReviewer(req, **params):
    return reviewingControlModif.RHConfSelectReviewer(req).process(params)

def addReviewer(req, **params):
    return reviewingControlModif.RHConfAddReviewer(req).process(params)

def removeReviewer(req, **params):
    return reviewingControlModif.RHConfRemoveReviewer(req).process(params)

def selectReferee(req, **params):
    return reviewingControlModif.RHConfSelectReferee(req).process(params)

def addReferee(req, **params):
    return reviewingControlModif.RHConfAddReferee(req).process(params)

def removeReferee(req, **params):
    return reviewingControlModif.RHConfRemoveReferee(req).process(params)
