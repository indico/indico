# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

"""
URL handlers for Collaboration plugins
"""

import os
from werkzeug.exceptions import NotFound

from indico.web.handlers import RHHtdocs

from MaKaC.webinterface.urlHandlers import SecureURLHandler, URLHandler, OptionallySecureURLHandler
from MaKaC.plugins import Collaboration
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools


class RHCollaborationHtdocs(RHHtdocs):
    """
    Static file handler for Collaboration plugin
    """

    @classmethod
    def calculatePath(cls, filepath, local_path=None, plugin=None):
        if plugin:
            module = CollaborationTools.getModule(plugin)
            if module:
                local_path = module.__path__[0]
            elif os.path.exists(os.path.join(Collaboration.__path__[0], 'htdocs', plugin)):
                return super(RHCollaborationHtdocs, cls).calculatePath(filepath, local_path=os.path.join(
                    Collaboration.__path__[0], 'htdocs', plugin))
            else:
                raise NotFound
        else:
            local_path = Collaboration.__path__[0]

        return super(RHCollaborationHtdocs, cls).calculatePath(filepath, os.path.join(local_path, 'htdocs'))


class UHAdminCollaboration(URLHandler):
    """URL handler for Admin Collaboration"""
    _endpoint = 'collaboration.adminCollaboration'


class UHConfModifCollaboration(OptionallySecureURLHandler):
    """URL handler for Admin Collaboration"""
    _endpoint = 'collaboration.confModifCollaboration'


class UHConfModifCollaborationManagers(URLHandler):
    """URL handler for Admin Collaboration"""
    _endpoint = 'collaboration.confModifCollaboration-managers'


class UHCollaborationDisplay(URLHandler):
    _endpoint = 'collaboration.collaborationDisplay'


class UHCollaborationElectronicAgreement(URLHandler):
    """URL handler for Electronic Agreement Manager"""
    _endpoint = 'collaboration.elecAgree'


class UHCollaborationUploadElectronicAgreement(URLHandler):
    """URL handler for Electronic Agreement to upload the Agreement"""
    _endpoint = 'collaboration.uploadElecAgree'


class UHCollaborationElectronicAgreementGetFile(URLHandler):
    """URL handler for Electronic Agreement Manager to get Paper"""
    _endpoint = 'collaboration.getPaperAgree'

    @classmethod
    def getURL(cls, conf, spkId, **params):
        url = cls._getURL()
        url.addParam('confId', conf.getId())
        url.addParam('spkId', spkId)
        return url


class UHCollaborationElectronicAgreementForm(SecureURLHandler):
    """URL handler for Electronic Agreement Form"""
    _endpoint = 'collaboration.elecAgreeForm'

    @classmethod
    def getURL(cls, confId, key, **params):
        return super(UHCollaborationElectronicAgreementForm, cls).getURL(authKey=key, confId=confId)
