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

from MaKaC.common.general import *
from MaKaC.webinterface.rh import conferenceModif
from MaKaC.webinterface import pages

if DEVELOPMENT:
    pages = reload(pages)


def index(req, **params):
    p = pages.WPContributionCreation( req )
    params["postURL"] = "contributionCreation.py/create"
    return p.display( params )

def create(req, **params):
    p = pages.WPContributionCreation( req )
    p.createContribution( params )
    return "done"

def presenterSearch( req, **params ):
    return conferenceModif.RHNewContributionPresenterSearch( req ).process( params )
    
def presenterNew( req, **params ):
    return conferenceModif.RHNewContributionPresenterNew( req ).process( params )
    
def personAdd( req, **params ):
    return conferenceModif.RHNewContributionPersonAdd( req ).process( params )
    
def authorSearch( req, **params ):
    return conferenceModif.RHNewContributionAuthorSearch( req ).process( params )
    
def authorNew( req, **params ):
    return conferenceModif.RHNewContributionAuthorNew( req ).process( params )
    
def authorAdd( req, **params ):
    return conferenceModif.RHNewContributionAuthorAdd( req ).process( params )
    
def coauthorSearch( req, **params ):
    return conferenceModif.RHNewContributionCoauthorSearch( req ).process( params )
    
def coauthorNew( req, **params ):
    return conferenceModif.RHNewContributionCoauthorNew( req ).process( params )
    
def coauthorAdd( req, **params ):
    return conferenceModif.RHNewContributionCoauthorAdd( req ).process( params )
    