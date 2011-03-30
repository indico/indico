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


