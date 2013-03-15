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

from MaKaC.common.general import *

from MaKaC.webinterface.rh import contribReviewingModif

if DEVELOPMENT:
    contribReviewingModif = reload( contribReviewingModif )


def index( req, **params ):
    return contribReviewingModif.RHContributionReviewing( req ).process( params )

def contributionReviewingMaterials( req, **params ):
    return contribReviewingModif.RHContribModifReviewingMaterials ( req ). process ( params )

def contributionReviewingJudgements( req, **params ):
    return contribReviewingModif.RHContributionReviewingJudgements ( req ). process ( params )

def assignEditing( req, **params ):
    return contribReviewingModif.RHAssignEditing( req ).process( params )

def removeAssignEditing( req, **params ):
    return contribReviewingModif.RHRemoveAssignEditing( req ).process( params )

def assignReviewing( req, **params ):
    return contribReviewingModif.RHAssignReviewing( req ).process( params )

def removeAssignReviewing( req, **params ):
    return contribReviewingModif.RHRemoveAssignReviewing( req ).process( params )

def assignReferee( req, **params ):
    return contribReviewingModif.RHAssignReferee( req ).process(params)

def removeAssignReferee(req, **params):
    return contribReviewingModif.RHRemoveAssignReferee( req ).process(params)

def finalJudge( req, **params ):
    return contribReviewingModif.RHFinalJudge( req ).process( params )

def reviewingHistory( req, **params ):
    return contribReviewingModif.RHReviewingHistory( req ).process( params )

def refereeDueDate( req, **params ):
    return contribReviewingModif.RHRefereeDueDate( req ).process( params )

def editorDueDate( req, **params ):
    return contribReviewingModif.RHEditorDueDate( req ).process( params )

def reviewerDueDate( req, **params ):
    return contribReviewingModif.RHReviewerDueDate( req ).process( params )