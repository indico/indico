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

import MaKaC.webinterface.rh.categoryMod as categoryMod


def index(req, **params):
    return categoryMod.RHCategoryModification( req ).process( params )

def actionSubCategs( req, **params ):
    return categoryMod.RHCategoryActionSubCategs( req ).process( params )

def clearCache( req, **params ):
    return categoryMod.RHCategoryClearCache( req ).process( params )

def clearConferenceCaches( req, **params ):
    return categoryMod.RHCategoryClearConferenceCaches( req ).process( params )

def actionConferences( req, **params ):
    return categoryMod.RHCategoryActionConferences( req ).process( params )
