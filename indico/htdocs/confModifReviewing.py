# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
from MaKaC.webinterface.rh import reviewingModif

if DEVELOPMENT:
    reviewingModif = reload( reviewingModif )

def access( req, **params ):
    return reviewingModif.RHConfModifReviewingAccess( req ).process( params )

def paperSetup( req, **params ):
    return reviewingModif.RHConfModifReviewingPaperSetup( req ).process( params )

def chooseReviewing( req, **params ):
    return reviewingModif.RHChooseReviewing( req ).process( params )

def selectReviewing(req, **params):
    return reviewingModif.RHSelectReviewing(req).process(params)

def setState(req, **params):
    return reviewingModif.RHSetState(req).process(params)

def addState(req, **params):
    return reviewingModif.RHAddState(req).process(params)

def removeState(req, **params):
    return reviewingModif.RHRemoveState(req).process(params)

def selectState(req, **params):
    return reviewingModif.RHSelectState(req).process(params)

def addQuestion(req, **params):
    return reviewingModif.RHAddQuestion(req).process(params)

def selectQuestion(req, **params):
    return reviewingModif.RHSelectQuestion(req).process(params)

def removeQuestion(req, **params):
    return reviewingModif.RHRemoveQuestion(req).process(params)

def setQuestion(req, **params):
    return reviewingModif.RHSetQuestion(req).process(params)

def setTemplate(req, **params):
    return reviewingModif.RHSetTemplate(req).process(params)

def selectCriteria(req, **params):
    return reviewingModif.RHSelectCriteria(req).process(params)

def setCriteria(req, **params):
    return reviewingModif.RHSetCriteria(req).process(params)

def addCriteria(req, **params):
    return reviewingModif.RHAddCriteria(req).process(params)

def removeCriteria(req, **params):
    return reviewingModif.RHRemoveCriteria(req).process(params)

def downloadTemplate(req, **params):
    return reviewingModif.RHDownloadTemplate(req).process(params)

def deleteTemplate(req, **params):
    return reviewingModif.RHDeleteTemplate(req).process(params)
