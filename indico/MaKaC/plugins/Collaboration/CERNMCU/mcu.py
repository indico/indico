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

from MaKaC.plugins.Collaboration.CERNMCU.common import getCERNMCUOptionValueByName,\
    secondsToWait
from MaKaC.common.xmlrpcTimeout import getServerWithTimeout
import time
import datetime
import xmlrpclib

class MCU(object):
    _instance = None

    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = getServerWithTimeout(getCERNMCUOptionValueByName('MCUAddress'), encoding='UTF-8', timeout = secondsToWait)

        return cls._instance

def MCUTrue():
    return xmlrpclib.boolean(True)

def MCUFalse():
    return xmlrpclib.boolean(False)

iso8601format = "%Y%m%dT%H:%M:%S"

def MCUTime(dt):
    return xmlrpclib.DateTime(dt.strftime(iso8601format))

def datetimeFromMCUTime(mcutime):
    """ returns a naive datetime from a xmlrpclib.DateTime object
    """
    #We use this expression and not the commented one because the latter is only available in python 2.5
    return datetime.datetime(*(time.strptime(mcutime.value, iso8601format)[0:6]))
    #return datetime.datetime.strptime(mcutime.value, iso8601format)


confCommonParams = {
    "registerWithGatekeeper" : MCUTrue(),
    "registerWithSIPRegistrar" : MCUTrue(),
    "multicastStreamingEnabled" : MCUFalse(),
    "unicastStreamingEnabled" : MCUTrue(),
    "h239Enabled" : MCUFalse(),
    "private" : MCUFalse(),
    #"maximumAudioPorts" : 0,
    #"maximumVideoPorts" : 0,
    #"reservedAudioPorts" : 0,
    #"reservedVideoPorts" : 0,
    "repetition" : 'none',
    "customLayoutEnabled" : MCUFalse(),
    "chairControl" : 'floorControlOnly'
}

participantCommonParams = {
    "participantType" : 'by_address',
    "deferConnection" : MCUTrue(),
    "displayNameOverrideStatus": MCUTrue()
}

def MCUParams(**args):
    args["authenticationUser"] = getCERNMCUOptionValueByName('indicoID')
    args["authenticationPassword"] = getCERNMCUOptionValueByName('indicoPassword')
    return args

def MCUConfCommonParams(**args):
    args.update(confCommonParams)
    return MCUParams(**args)

def MCUParticipantCommonParams(**args):
    args.update(participantCommonParams)
    return MCUParams(**args)

def paramsForLog(args_in):
    args_out = args_in.copy()
    args_out["authenticationPassword"] = "(hidden)"
    return args_out


