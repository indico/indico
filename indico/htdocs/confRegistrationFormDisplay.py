# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import MaKaC.webinterface.rh.registrationFormDisplay as registrationFormDisplay
import MaKaC.webinterface.rh.CFADisplay as CFADisplay

def index(req, **params):
    return registrationFormDisplay.RHRegistrationForm( req ).process( params )

def display (req, **params):
    return registrationFormDisplay.RHRegistrationFormDisplay( req ).process( params )

def creation (req, **params):
    return registrationFormDisplay.RHRegistrationFormCreation( req ).process( params )

def creationDone (req, **params):
    return registrationFormDisplay.RHRegistrationFormCreationDone( req ).process( params )
    
def confirmBooking (req, **params):
    return registrationFormDisplay.RHRegistrationFormconfirmBooking( req ).process( params )

def confirmBookingDone (req, **params):
    return registrationFormDisplay.RHRegistrationFormconfirmBookingDone( req ).process( params )
    
def signIn (req, **params):
    return registrationFormDisplay.RHRegistrationFormSignIn( req ).process( params )

def modify (req, **params):
    return registrationFormDisplay.RHRegistrationFormModify( req ).process( params )

def performModify (req, **params):
    return registrationFormDisplay.RHRegistrationFormPerformModify( req ).process( params )

def abstractSubmission(req, **params):
    return CFADisplay.RHAbstractSubmissionRegistratant(req).process(params)

def conditions (req, **params):
    return registrationFormDisplay.RHRegistrationFormConditions( req ).process( params )
