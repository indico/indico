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

from MaKaC.webinterface.rh import login




def index(req, **params):
    return login.RHSignIn( req ).process( params )
    #p = pages.WPSignIn( req )
    #params["postURL"] = "signIn.py/signIn"
    #return p.display( params )

#TODO: Never used, should be soon deleted. Also "login.RHAuthenticate" doesn't exist!
#def signIn(req, **params):
#    return login.RHAuthenticate( req ).process( params )
#    #p = pages.WPSignIn( req )
#    #res = p.authenticate( params )
#    #return "done: %s"%res

def active(req, **params):
    return login.RHActive( req ).process( params )


def sendLogin(req, **params):
    return login.RHSendLogin( req ).process( params )


def disabledAccount(req, **params):
    return login.RHDisabledAccount( req ).process( params )


def unactivatedAccount(req, **params):
    return login.RHUnactivatedAccount( req ).process( params )


def sendActivation(req, **params):
    return login.RHSendActivation( req ).process( params )

