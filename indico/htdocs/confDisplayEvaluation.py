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

from MaKaC.webinterface.rh import evaluationDisplay

def index(req, **params):
    """General information display."""
    return evaluationDisplay.RHEvaluationMainInformation( req ).process( params )

def display (req, **params):
    """Evaluation display."""
    return evaluationDisplay.RHEvaluationDisplay( req ).process( params )

def modif (req, **params):
    """Evaluation modification."""
    return evaluationDisplay.RHEvaluationModif( req ).process( params )

def signIn (req, **params):
    """Evaluation sign in."""
    return evaluationDisplay.RHEvaluationSignIn( req ).process( params )

def submit (req, **params):
    """Submit the evaluation."""
    return evaluationDisplay.RHEvaluationSubmit( req ).process( params )

def submitted (req, **params):
    """Show message : Evaluation submitted."""
    return evaluationDisplay.RHEvaluationSubmitted( req ).process( params )