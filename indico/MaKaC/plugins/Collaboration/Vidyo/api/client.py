# -*- coding: utf-8 -*-
##
## $Id: options.py,v 1.2 2009/04/25 13:56:05 dmartinc Exp $
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

from MaKaC.plugins.Collaboration.Vidyo.common import getVidyoOptionValue
from MaKaC.common.logger import Logger
import suds


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
                adminAPIUrl = getVidyoOptionValue('baseAPILocation') + getVidyoOptionValue('adminAPISuffix')
            if username is None:
                username = getVidyoOptionValue('indicoUsername')
            if password is None:
                password = getVidyoOptionValue('indicoPassword')

            try:
                cls._instance = suds.client.Client(adminAPIUrl,
                                                   transport = ClientBase.getTransport(adminAPIUrl, username , password))
            except Exception, e:
                Logger.get("Vidyo").exception("Problem building AdminClient")
                raise e

        return cls._instance



class UserClient(ClientBase):
    """ Singleton for the client for Vidyo's user API
    """
    _instance = None

    @classmethod
    def getInstance(cls, userAPIUrl = None, username = None, password = None):

        if cls._instance is None or (userAPIUrl is not None or username is not None or password is not None):

            if userAPIUrl is None:
                userAPIUrl = getVidyoOptionValue('baseAPILocation') + getVidyoOptionValue('userAPISuffix')
            if username is None:
                username = getVidyoOptionValue('indicoUsername')
            if password is None:
                password = getVidyoOptionValue('indicoPassword')

            try:
                cls._instance = suds.client.Client(userAPIUrl,
                                                   transport = ClientBase.getTransport(userAPIUrl, username , password))
            except Exception, e:
                Logger.get("Vidyo").exception("Problem building UserClient")
                raise e

        return cls._instance
