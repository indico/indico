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
from flask import request, current_app as app
from MaKaC.common.security import Sanitization

from MaKaC.common.fossilize import fossilize, NonFossilizableException, clearCache
from MaKaC.fossils.error import ICausedErrorFossil

from MaKaC.services.interface.rpc.common import RequestError
from MaKaC.services.interface.rpc.common import ProcessError
from MaKaC.services.interface.rpc.common import CausedError
from MaKaC.services.interface.rpc.common import NoReportError
from MaKaC.services.interface.rpc.process import ServiceRunner

from MaKaC.common.logger import Logger
from indico.util.json import dumps, loads
from indico.util.string import fix_broken_obj


class Json:
    def __init__(self, content):
        self.json = encode(content)

def encode(obj):
    return dumps(obj, ensure_ascii=True)

def decode(str):
    return unicodeToUtf8(loads(str))

def unicodeToUtf8(obj):
    """ obj must be a unicode object, a list or a dictionary
        This method will loop through the object and change unicode objects into str objects encoded in utf-8.
        If a list or a dictionary is found during the loop, a recursive call is made.
        However this method does not support objects that are not lists or dictionaries.
        This method is useful to turn unicode objects from the output object given by loads(),
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


def process():

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

        # init/clear fossil cache
        clearCache()

        # read request
        requestText = request.data  # TODO: use request.json!

        Logger.get('rpc').info('json rpc request. request text= ' + str(requestText))

        if requestText == "":
            raise RequestError("ERR-R2", "Empty request.")

        # decode json
        try:
            requestBody = decode(requestText)
        except Exception, e:
            raise RequestError("ERR-R3", "Error parsing json request.", e)

        if "id" in requestBody:
            responseBody["id"] = requestBody["id"]

        result = ServiceRunner().invokeMethod(str(requestBody["method"]), requestBody.get("params", []))

        # serialize result
        try:
            responseBody["result"] = result
        except Exception:
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
                params = requestBody.get("params", [])
                Sanitization._escapeHTML(params)
                errorInfo["requestInfo"] = {"method": str(requestBody["method"]),
                                            "params": params,
                                            "origin": str(requestBody.get("origin", "unknown"))}
                Logger.get('rpc').debug('Arguments: %s' % errorInfo['requestInfo'])

        responseBody["error"] = errorInfo

    try:
        jsonResponse = encode(responseBody)
    except UnicodeError:
        Logger.get('rpc').exception("Problem encoding JSON response")
        # This is to avoid exceptions due to old data encodings (based on iso-8859-1)
        responseBody['result'] = fix_broken_obj(responseBody['result'])
        jsonResponse = encode(responseBody)

    return app.response_class(jsonResponse, mimetype='application/json')
