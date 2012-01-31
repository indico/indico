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

import MaKaC.webinterface.rh.templates as templates
from MaKaC.webinterface.rh import admins

def index(req, **params):
    return admins.RHAdminLayoutGeneral(req).process(params)

def saveTemplateSet(req, **params):
    return admins.RHAdminLayoutSaveTemplateSet(req).process(params)

def saveSocial(req, **params):
    return admins.RHAdminLayoutSaveSocial(req).process(params)

def setDefaultPDFOptions(req, **params):
    return templates.RHSetDefaultPDFOptions(req).process(params)

def styles(req, **params):
    return admins.RHStyles(req).process(params)

def addStyle(req, **params):
    return admins.RHAddStyle(req).process(params)

def deleteStyle(req, **params):
    return admins.RHDeleteStyle(req).process(params)
