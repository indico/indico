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

import MaKaC.webinterface.rh.abstractReviewing as abstractReviewing

# Reviewing
def reviewingSetup(req, **params):
    return abstractReviewing.RHAbstractReviewingSetup(req).process(params)

def reviewingTeam(req, **params):
    return abstractReviewing.RHAbstractReviewingTeam(req).process(params)

# Notification templates
def notifTpl( req, **params ):
    return abstractReviewing.RHNotifTpl( req ).process( params )

def notifTplNew(req,**params):
    return abstractReviewing.RHCFANotifTplNew(req).process(params)

def notifTplRem(req,**params):
    return abstractReviewing.RHCFANotifTplRem(req).process(params)

def notifTplEdit(req,**params):
    return abstractReviewing.RHCFANotifTplEdit(req).process(params)

def notifTplDisplay(req,**params):
    return abstractReviewing.RHCFANotifTplDisplay(req).process(params)

def notifTplPreview(req,**params):
    return abstractReviewing.RHCFANotifTplPreview(req).process(params)

def notifTplCondNew(req,**params):
    return abstractReviewing.RHNotifTplConditionNew(req).process(params)

def notifTplCondRem(req,**params):
    return abstractReviewing.RHNotifTplConditionRem(req).process(params)

def notifTplUp(req,**params):
    return abstractReviewing.RHCFANotifTplUp(req).process(params)

def notifTplDown(req,**params):
    return abstractReviewing.RHCFANotifTplDown(req).process(params)


