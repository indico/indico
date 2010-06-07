# -*- coding: utf-8 -*-
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

from MaKaC.common.logger import Logger
from MaKaC.plugins.Collaboration.Vidyo.api.client import AdminClient, UserClient
from suds import WebFault
from MaKaC.plugins.Collaboration.Vidyo.common import VidyoConnectionException
from urllib2 import URLError


class ApiBase(object):
    """ Provides the _handleServiceCallException method
    """

    @classmethod
    def _handleServiceCallException(cls, e):
        Logger.get("Vidyo").exception("Service call exception")
        cause = e.args[0]
        if type(cause) is tuple and cause[0] == 401:
            raise VidyoConnectionException(e)
        elif type(e) == URLError:
            raise VidyoConnectionException(e)
        else:
            raise e



class AdminApi(ApiBase):
    """ This class performs low-level operations by getting the corresponding
        client and calling a SOAP service.
        We write info statements to the log with the details of what we are doing.
        Each class method performs a single service call to Vidyo.
    """


    @classmethod
    def addRoom(cls, newRoom, confId, bookingId):
        Logger.get('Vidyo').info("""Evt:%s, booking:%s, opening connection to Vidyo Admin API""" % (confId, bookingId))
        try:
            vidyoClient = AdminClient.getInstance()
        except Exception, e:
            raise VidyoConnectionException(e)

        Logger.get('Vidyo').info("""Evt:%s, booking:%s, calling Admin API's addRoom operation with room: %s""" %
                                (confId, bookingId, str(newRoom)))
        try:
            answer = vidyoClient.service.addRoom(newRoom)
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, Admin API's addRoom operation got answer: %s""" %
                                    (confId, bookingId, str(answer)))
            return answer
        except WebFault, e:
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, Admin API's addRoom operation got WebFault: %s""" %
                                    (confId, bookingId, e.fault.faultstring))
            raise e

        except Exception, e:
            cls._handleServiceCallException(e)


    @classmethod
    def updateRoom(cls, roomId, updatedRoom, confId, bookingId):
        Logger.get('Vidyo').info("""Evt:%s, booking:%s, opening connection to Vidyo Admin API""" % (confId, bookingId))
        try:
            vidyoClient = AdminClient.getInstance()
        except Exception, e:
            raise VidyoConnectionException(e)

        Logger.get('Vidyo').info("""Evt:%s, booking:%s, calling Admin API's updateRoom operation with roomId: %s and room: %s""" %
                                (confId, bookingId, str(roomId), str(updatedRoom)))
        try:
            answer = vidyoClient.service.updateRoom(roomId, updatedRoom)
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, Admin API's updateRoom operation got answer: %s""" %
                                    (confId, bookingId, str(answer)))

            return answer

        except WebFault, e:
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, Admin API's updateRoom operation got WebFault: %s""" %
                                    (confId, bookingId, e.fault.faultstring))
            raise e

        except Exception, e:
            cls._handleServiceCallException(e)


    @classmethod
    def getRooms(cls, searchFilter, confId, bookingId):
        #WARNING: until bug is corrected, name description and groupName in returned rooms are wrong

        Logger.get('Vidyo').info("""Evt:%s, booking:%s, opening connection to Vidyo Admin API""" % (confId, bookingId))
        try:
            vidyoClient = AdminClient.getInstance()
        except Exception, e:
            raise VidyoConnectionException(e)

        Logger.get('Vidyo').info("""Evt:%s, booking:%s, calling Admin API's getRooms operation with search filter: %s""" %
                                         (confId, bookingId, str(searchFilter)))
        try:
            answer = vidyoClient.service.getRooms(searchFilter)
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, Admin API's getRooms operation got answer: %s""" %
                                             (confId, bookingId, str(answer)))

            return answer

        except WebFault, e:
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, Admin API's getRooms operation got WebFault: %s""" %
                                    (confId, bookingId, e.fault.faultstring))
            raise e

        except Exception, e:
            cls._handleServiceCallException(e)


    @classmethod
    def getRoom(cls, roomId, confId, bookingId):
        #WARNING: until bug is corrected, name description and groupName in returned rooms are wrong

        Logger.get('Vidyo').info("""Evt:%s, booking:%s, opening connection to Vidyo Admin API""" % (confId, bookingId))
        try:
            vidyoClient = AdminClient.getInstance()
        except Exception, e:
            raise VidyoConnectionException(e)

        Logger.get('Vidyo').info("""Evt:%s, booking:%s, calling Admin API's getRoom operation with roomId: %s""" %
                                         (confId, bookingId, str(roomId)))
        try:
            answer = vidyoClient.service.getRoom(roomId)
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, Admin API's getRoom operation got answer: %s""" %
                                             (confId, bookingId, str(answer)))

            return answer

        except WebFault, e:
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, Admin API's getRoom operation got WebFault: %s""" %
                                    (confId, bookingId, e.fault.faultstring))
            raise e

        except Exception, e:
            cls._handleServiceCallException(e)


    @classmethod
    def deleteRoom(cls, roomId, confId, bookingId):
        Logger.get('Vidyo').info("""Evt:%s, booking:%s, opening connection to Vidyo Admin API""" % (confId, bookingId))
        try:
            vidyoClient = AdminClient.getInstance()
        except Exception, e:
            raise VidyoConnectionException(e)

        Logger.get('Vidyo').info("""Evt:%s, booking:%s, calling Admin API's deleteRoom operation with roomId: %s""" %
                                         (confId, bookingId, str(roomId)))
        try:
            answer = vidyoClient.service.deleteRoom(roomId)
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, Admin API's deleteRoom operation got answer: %s""" %
                                             (confId, bookingId, str(answer)))

            return answer
        except WebFault, e:
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, Admin API's deleteRoom operation got WebFault: %s""" %
                                    (confId, bookingId, e.fault.faultstring))
            raise e

        except Exception, e:
            cls._handleServiceCallException(e)



class UserApi(ApiBase):
    """ This class performs low-level operations by getting the corresponding
        client and calling a SOAP service.
        We write info statements to the log with the details of what we are doing.
    """


    @classmethod
    def search(cls, searchFilter, confId, bookingId):
        Logger.get('Vidyo').info("""Evt:%s, booking:%s, opening connection to Vidyo Admin API""" % (confId, bookingId))
        try:
            vidyoClient = UserClient.getInstance()
        except Exception, e:
            raise VidyoConnectionException(e)

        Logger.get('Vidyo').info("""Evt:%s, booking:%s, calling User API's search operation with filter: %s""" %
                                         (confId, bookingId, str(searchFilter)))
        try:
            answer = vidyoClient.service.search(searchFilter)
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, User API's search operation got answer: %s""" %
                                             (confId, bookingId, str(answer)))

            return answer

        except WebFault, e:
            Logger.get('Vidyo').info("""Evt:%s, booking:%s, User API's search operation operation got WebFault: %s""" %
                                    (confId, bookingId, e.fault.faultstring))
            raise e

        except Exception, e:
            cls._handleServiceCallException(e)
