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

from MaKaC.plugins.Collaboration.Vidyo.common import getVidyoOptionValue
from MaKaC.common.logger import Logger
import suds
from requests.auth import HTTPDigestAuth
import requests


class ClientBase(object):
    """ Base class for AdminClient and UserClient
        Provides a method to obtain the correct transport for authentication.
    """

    @classmethod
    def getTransport(cls, url, username, password):
        """ Note: we always use http.HttpAuthenticated, which implements basic authentication.
            https.HttpAuthenticated implements advanced authentication.
            Even if the 2 classes have "http" and "https" in the package names, they are just 2 ways
            of authenticating independant of http and https.
            Vidyo probably only supports basic authentication, be it through http or https.
        """
#        if url.startswith('https'):
#            return suds.transport.https.HttpAuthenticated(username=username, password=password, timeout = 30.0)
#        else:
        return suds.transport.http.HttpAuthenticated(username=username, password=password, timeout = 30.0)



class AdminClient(ClientBase):
    """ Singleton for the client for Vidyo's admin API.
        We need to build a suds.client.Client with a transport argument (and not directly with username and password
        arguments) because Vidyo only supports preemptive http authentication for performance reasons.
        Suds supports this by first constructing an HttpAuthenticated transport and then passing it to the Client.
    """
    _instance = None

    @classmethod
    def getInstance(cls, adminAPIUrl = None, username = None, password = None):

        if cls._instance is None or (adminAPIUrl is not None or username is not None or password is not None):

            if adminAPIUrl is None:
                adminAPIUrl = getVidyoOptionValue('adminAPIURL')
            if username is None:
                username = getVidyoOptionValue('indicoUsername')
            if password is None:
                password = getVidyoOptionValue('indicoPassword')

            try:
                cls._instance = suds.client.Client(adminAPIUrl,
                                                   transport = ClientBase.getTransport(adminAPIUrl, username , password))
            except Exception:
                Logger.get("Vidyo").exception("Problem building AdminClient")
                raise

        return cls._instance



class UserClient(ClientBase):
    """ Singleton for the client for Vidyo's user API
    """
    _instance = None

    @classmethod
    def getInstance(cls, userAPIUrl = None, username = None, password = None):

        if cls._instance is None or (userAPIUrl is not None or username is not None or password is not None):

            if userAPIUrl is None:
                userAPIUrl = getVidyoOptionValue('userAPIURL')
            if username is None:
                username = getVidyoOptionValue('indicoUsername')
            if password is None:
                password = getVidyoOptionValue('indicoPassword')

            try:
                cls._instance = suds.client.Client(userAPIUrl,
                                                   transport = ClientBase.getTransport(userAPIUrl, username , password))
            except Exception:
                Logger.get("Vidyo").exception("Problem building UserClient")
                raise

        return cls._instance

class RavemClient(object):
    """ Singleton for the client for RAVEM API
    """
    _instance = None

    def __init__(self, client, url):
        self._client = client
        self._url = url

    def performOperation(self, operation):
        try:
            return self._client.get(self._url + operation)
        except Exception:
            Logger.get("Vidyo").exception("Problem making request to RavemClient")
            raise

    @classmethod
    def getInstance(cls, ravemAPIUrl = None, username = None, password = None):

        if cls._instance is None or (ravemAPIUrl is not None or username is not None or password is not None):

            if ravemAPIUrl is None:
                ravemAPIUrl = getVidyoOptionValue('ravemAPIURL')
            if username is None:
                username = getVidyoOptionValue('ravemUsername')
            if password is None:
                password = getVidyoOptionValue('ravemPassword')

            try:
                client = requests.session(auth=HTTPDigestAuth(username, password), verify=False)
                cls._instance = RavemClient(client, ravemAPIUrl)
            except Exception:
                Logger.get("Vidyo").exception("Problem building RavemClient")
                raise
        return cls._instance
