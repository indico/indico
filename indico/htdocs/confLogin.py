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

from MaKaC.common.general import *

from MaKaC.webinterface.rh import conferenceDisplay


def index(req, **params):
    return conferenceDisplay.RHConfSignIn( req ).process( params )

def signIn(req, **params):
    return conferenceDisplay.RHConfAuthenticate( req ).process( params )

#def signOut(req, **params):
#    return conferenceDisplay.RHConfSignOut( req ).process( params )

def active(req, **params):
    return conferenceDisplay.RHConfActivate( req ).process( params )

def sendLogin(req, **params):
    return conferenceDisplay.RHConfSendLogin( req ).process( params )

def disabledAccount(req, **params):
    return conferenceDisplay.RHConfDisabledAccount( req ).process( params )

def unactivatedAccount(req, **params):
    return conferenceDisplay.RHConfUnactivatedAccount( req ).process( params )

def sendActivation(req, **params):
    return conferenceDisplay.RHConfSendActivation( req ).process( params )

