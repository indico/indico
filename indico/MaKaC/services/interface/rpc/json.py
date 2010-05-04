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

import simplejson
from MaKaC.common.fossilize import fossilize, NonFossilizableException
from MaKaC.fossils.error import ICausedErrorFossil
try:
    from mod_python import apache
except ImportError:
    pass

from MaKaC.common.PickleJar import DictPickler

from MaKaC.services.interface.rpc.common import RequestError
from MaKaC.services.interface.rpc.common import ProcessError
from MaKaC.services.interface.rpc.common import CausedError
from MaKaC.services.interface.rpc.common import NoReportError
from MaKaC.services.interface.rpc.process import invokeMethod

from MaKaC.common.logger import Logger

class Json:
    def __init__(self, content):
        self.json = encode(content)

def encode(obj):
    return simplejson.dumps(obj, ensure_ascii=False)

def decode(str):
    return unicodeToUtf8(simplejson.loads(str))

def unicodeToUtf8(obj):
    """ obj must be a unicode object, a list or a dictionary
        This method will loop through the object and change unicode objects into str objects encoded in utf-8.
        If a list or a dictionary is found during the loop, a recursive call is made.
        However this method does not support objects that are not lists or dictionaries.
        This method is useful to turn unicode objects from the output object given by simplejson.loads(),
        into str objects encoded in utf-8.
        In case of a persistent object or an object inside a persistent object,
        you will need to notify the database of changes in the object after calling this method.
        Author: David Martin Clavo
    """

    # replace a single unicode object
    if isinstance(obj, unicode):
        return obj.encode("utf-8",'replace')

    # replace unicode objects inside a list
    if isinstance(obj,list):
        for i in range(0, len(obj)):
            obj[i] = unicodeToUtf8(obj[i])

    #replace unicode objects inside a dictionary
    if isinstance(obj,dict):
        for k,v in obj.items():
            del obj[k] #we delete the old unicode key
            #keys in JSON objects can only be strings, but we still call unicodeToUtf8
            #for the key in case we have a Python object whose key is a number, etc.
            obj[unicodeToUtf8(k)] = unicodeToUtf8(v)

    return obj

def process(req):

    responseBody = {
        "version": "1.1",
        "error": None,
        "result": None
    }
    requestBody = None
    try:
        # check content type (if the users know what they are using)
        #if req.content_type != "application/json":
        #    raise RequestError("Invalid content type. It must be 'application/json'.")

        # read request
        requestText = req.read()

        Logger.get('rpc').debug('json rpc request. request text= ' + str(requestText))

        if requestText == "":
            raise RequestError("ERR-R2", "Empty request.")

        # decode json
        try:
            requestBody = decode(requestText)
        except Exception, e:
            raise RequestError("ERR-R3", "Error parsing json request.", e)

        if "id" in requestBody:
            responseBody["id"] = requestBody["id"]

        result = invokeMethod(str(requestBody["method"]), requestBody.get("params", []), req)

        # serialize result
        try:
            responseBody["result"] = result
        except Exception, e:
            raise ProcessError("ERR-P1", "Error during serialization.")

    except CausedError, e:

        try:
            errorInfo = fossilize(e)
        except NonFossilizableException, e2:
            # catch Exceptions that are not registered as Fossils
            # and log them
            errorInfo  = {'code':'', 'message': str(e2)}
            Logger.get('dev').exception('Exception not registered as fossil')


        if isinstance(e, NoReportError):
            # NoReport errors (i.e. not logged in) shouldn't be logged
            pass
        else:
            Logger.get('rpc').exception('Service request failed. Request text:\r\n%s\r\n\r\n' % str(requestText))

            if requestBody:
                errorInfo["requestInfo"] = {"method": str(requestBody["method"]),
                                            "params": requestBody.get("params", [])}
                Logger.get('rpc').debug('Arguments: %s' % errorInfo['requestInfo'])


        responseBody["error"] = errorInfo

    jsonResponse = encode(responseBody)

    req.content_type = "application/json"
    req.write(jsonResponse)
    return apache.OK
