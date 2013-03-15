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

import MaKaC.webinterface.rh.registrationFormDisplay as registrationFormDisplay

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

def conditions (req, **params):
    return registrationFormDisplay.RHRegistrationFormConditions( req ).process( params )
