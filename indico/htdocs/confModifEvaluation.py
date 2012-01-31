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

from MaKaC.webinterface.rh import evaluationModif

def index( req, **params ):
    """The index web page of an evaluation is by default the setup page."""
    return setup(req, **params)

def setup( req, **params ):
    """Setup web page of an evaluation."""
    return evaluationModif.RHEvaluationSetup( req ).process( params )

def changeStatus( req, **params ):
    """changes status of an evaluation (ENABLED/DISABLED)."""
    return evaluationModif.RHEvaluationSetupChangeStatus( req ).process( params )

def specialAction( req, **params ):
    """processes a special action."""
    return evaluationModif.RHEvaluationSetupSpecialAction( req ).process( params )

def dataModif(req, **params):
    """called when you want to change general parameters of your evaluation."""
    return evaluationModif.RHEvaluationSetupDataModif( req ).process( params )

def performDataModif(req, **params):
    """performs changes to general parameters of the evaluation."""
    return evaluationModif.RHEvaluationSetupPerformDataModif( req ).process( params )

def edit( req, **params ):
    """Edition of Evaluation questions."""
    return evaluationModif.RHEvaluationEdit( req ).process( params )

def editPerformChanges( req, **params ):
    """performs changes for Evaluation questions."""
    return evaluationModif.RHEvaluationEditPerformChanges( req ).process( params )

def preview( req, **params ):
    """Preview web page of an evaluation."""
    return evaluationModif.RHEvaluationPreview( req ).process( params )

def results( req, **params ):
    """Results web page of an evaluation."""
    return evaluationModif.RHEvaluationResults( req ).process( params )

def resultsOptions( req, **params ):
    """Do asked actions for the results."""
    return evaluationModif.RHEvaluationResultsOptions( req ).process( params )

def resultsSubmittersActions( req, **params ):
    """Do asked actions for the submitters."""
    return evaluationModif.RHEvaluationResultsSubmittersActions( req ).process( params )