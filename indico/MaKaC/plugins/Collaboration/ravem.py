# -*- coding: utf-8 -*-
##
## $id$
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

from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.logger import Logger
from requests.auth import HTTPDigestAuth
import requests
from urllib import urlencode


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
    def getInstance(cls, ravem_api_url=None, username=None, password=None):

        if cls._instance is None or (ravem_api_url is not None or username is not None or password is not None):

            if ravem_api_url is None:
                ravem_api_url = CollaborationTools.getCollaborationOptionValue('ravemAPIURL')
            if username is None:
                username = CollaborationTools.getCollaborationOptionValue('ravemUsername')
            if password is None:
                password = CollaborationTools.getCollaborationOptionValue('ravemPassword')

            try:
                cls._instance = RavemClient(username, password, ravem_api_url)
            except Exception:
                Logger.get("Ravem").exception("Problem building RavemClient")
                raise
        return cls._instance


class RavemApi(object):
    """ This class performs low-level operations by getting the corresponding
        client and calling a service.
    """

    @classmethod
    def _api_operation(cls, service, *args, **kwargs):
        try:
            url = "/%s?%s" % (service, urlencode(kwargs))
            ravemClient = RavemClient.getInstance()
            return ravemClient.performOperation(url)
        except Exception, e:
            Logger.get('Ravem').exception("""Ravem API's '%s' operation not successfull: %s""" % (service, e.message))
            raise

    @classmethod
    def isLegacyEndpointConnected(cls, room_ip):
        return cls._api_operation("getstatus", where="vc_endpoint_legacy_ip", value=room_ip)

    @classmethod
    def isVidyoPanoramaConnected(cls, vidyo_panorama_id):
        return cls._api_operation("getstatus", where="vc_endpoint_vidyo_username", value=vidyo_panorama_id)

    @classmethod
    def disconnectLegacyEndpoint(cls, room_ip, service_type, room_name):
        return cls._api_operation("videoconference/disconnect", type=service_type, where="vc_endpoint_legacy_ip",
                                  value=room_ip, vidyo_room_name=room_name)

    @classmethod
    def disconnectVidyoPanorama(cls, vidyo_panorama_id, service_type, room_name):
        return cls._api_operation("videoconference/disconnect", type=service_type, where="vc_endpoint_vidyo_username",
                                  value=vidyo_panorama_id, vidyo_room_name=room_name)
