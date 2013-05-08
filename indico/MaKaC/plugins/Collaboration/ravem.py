# -*- coding: utf-8 -*-
##
## $id$
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

from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.logger import Logger
from requests.auth import HTTPDigestAuth
import requests

class RavemClient(object):
    """ Singleton for the client for RAVEM API
    """
    _instance = None

    def __init__(self, username, password, url):
        self._username = username
        self._password = password
        self._url = url

    def performOperation(self, operation):
        data = requests.get(self._url + operation, auth=HTTPDigestAuth(self._username, self._password), verify=False)
        return data

    @classmethod
    def getInstance(cls, ravemAPIUrl = None, username = None, password = None):

        if cls._instance is None or (ravemAPIUrl is not None or username is not None or password is not None):

            if ravemAPIUrl is None:
                ravemAPIUrl = CollaborationTools.getCollaborationOptionValue('ravemAPIURL')
            if username is None:
                username = CollaborationTools.getCollaborationOptionValue('ravemUsername')
            if password is None:
                password = CollaborationTools.getCollaborationOptionValue('ravemPassword')

            try:
                cls._instance = RavemClient(username, password, ravemAPIUrl)
            except Exception:
                Logger.get("Ravem").exception("Problem building RavemClient")
                raise
        return cls._instance

class RavemApi(object):
    """ This class performs low-level operations by getting the corresponding
        client and calling a service.
    """


    @classmethod
    def isRoomConnected(cls, roomIp):
        try:
            ravemClient = RavemClient.getInstance()
            return ravemClient.performOperation("/getstatus?where=vc_endpoint_ip&value=%s"%roomIp)
        except Exception, e:
            Logger.get('Ravem').exception("""Ravem API's isRoomConnected operation not successfull: %s""" % e.message)
            raise

    @classmethod
    def disconnectRoom(cls, roomIp, serviceType):
        try:
            ravemClient = RavemClient.getInstance()
            return ravemClient.performOperation("/videoconference/disconnect?type=%s&where=vc_endpoint_ip&value=%s"%(serviceType, roomIp))
        except Exception, e:
            Logger.get('Ravem').exception("""Ravem API's disconnectRoom operation not successfull: %s""" % e.message)
            raise
