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

"""
URL handlers for Collaboration plugins
"""

from MaKaC.webinterface.urlHandlers import SecureURLHandler, OptionallySecureURLHandler

class UHCollaborationElectronicAgreement(OptionallySecureURLHandler):
    """
    URL handler for Electronic Agreement Manager
    """
    _relativeURL = "Collaboration/elecAgree"

class UHCollaborationElectronicAgreementGetFile(OptionallySecureURLHandler):
    """
    URL handler for Electronic Agreement Manager to get Paper
    """
    _relativeURL = "Collaboration/getPaperAgree"
    def getURL(cls, conf, spkId, **params):
        url = cls._getURL()
        url.addParam("confId", conf.getId())
        url.addParam("spkId", spkId)
        return url
    getURL = classmethod( getURL )

class UHCollaborationElectronicAgreementForm(SecureURLHandler):
    """
    URL handler for Electronic Agreement Form
    """
    _relativeURL = "Collaboration/elecAgreeForm"

    def getURL(cls, confId, key, **params):
        url = cls._getURL()
        url.addParam("authKey", key)
        url.addParam("confId", confId)
        return url
    getURL = classmethod( getURL )

