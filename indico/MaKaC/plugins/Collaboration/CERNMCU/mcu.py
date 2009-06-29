# -*- coding: utf-8 -*-
##
## $Id: mcu.py,v 1.4 2009/04/25 13:55:51 dmartinc Exp $
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

from MaKaC.plugins.base import PluginsHolder
from MaKaC.plugins.Collaboration.CERNMCU.common import getCERNMCUOptionValueByName
from MaKaC.common.xmlrpcTimeout import getServerWithTimeout
import xmlrpclib

secondsToWait = 10

class MCU(object):
    _instance = None    
    
    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = getServerWithTimeout(getCERNMCUOptionValueByName('MCUAddress'), timeout = secondsToWait)
            
        return cls._instance
    
def MCUTrue():
    return xmlrpclib.boolean(True)

def MCUFalse():
    return xmlrpclib.boolean(False)

def MCUTime(timeStr):
    return xmlrpclib.DateTime(timeStr)

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
    "participantProtocol": 'h323',
    "participantType" : 'by_address',
    "deferConnection" : MCUTrue()   
}
    
def MCUParams(**args):
        cernmcu = PluginsHolder().getPluginType('Collaboration').getPlugin('CERNMCU')
        args["authenticationUser"] = cernmcu.getOption('indicoID').getValue()
        args["authenticationPassword"] = cernmcu.getOption('indicoPassword').getValue()
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
    

        