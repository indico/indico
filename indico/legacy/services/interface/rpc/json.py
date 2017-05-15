# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from flask import request, current_app as app
from flask.wrappers import BadRequest

from indico.legacy.common.security import Sanitization
from indico.legacy.common.fossilize import (
    NonFossilizableException,
    clearCache,
    fossilize
)
from indico.legacy.services.interface.rpc.common import (
    CausedError,
    NoReportError,
    RequestError
)
from indico.legacy.services.interface.rpc.process import ServiceRunner

from indico.core.logger import Logger
from indico.util.json import dumps, loads
from indico.util.string import fix_broken_obj, unicode_struct_to_utf8


def encode(obj):
    return dumps(obj, ensure_ascii=True)


def decode(s):
    return unicode_struct_to_utf8(loads(s))


def process():

    responseBody = {
        'version': '1.1',
        'error': None,
        'result': None
    }
    requestBody = None
    try:
        # init/clear fossil cache
        clearCache()

        # read request
        try:
            requestBody = request.get_json()
            Logger.get('rpc').info('json rpc request. request: {0}'.format(requestBody))
        except BadRequest:
            raise RequestError('ERR-R1', 'Invalid mime-type.')
        if not requestBody:
            raise RequestError('ERR-R2', 'Empty request.')
        if 'id' in requestBody:
            responseBody['id'] = requestBody['id']

        # run request
        responseBody['result'] = ServiceRunner().invokeMethod(str(requestBody['method']),
                                                              requestBody.get('params', []))
    except CausedError as e:
        try:
            errorInfo = fossilize(e)
        except NonFossilizableException as e2:
            # catch Exceptions that are not registered as Fossils
            # and log them
            errorInfo  = {'code': '', 'message': str(e2)}
            Logger.get('dev').exception('Exception not registered as fossil')

        # NoReport errors (i.e. not logged in) shouldn't be logged
        if not isinstance(e, NoReportError) and not getattr(e, '_disallow_report', False):
            Logger.get('rpc').exception('Service request failed. '
                                        'Request text:\r\n{0}\r\n\r\n'.format(requestBody))

            if requestBody:
                params = requestBody.get('params', [])
                Sanitization._escapeHTML(params)
                errorInfo["requestInfo"] = {
                    'method': str(requestBody['method']),
                    'params': params,
                    'origin': str(requestBody.get('origin', 'unknown'))
                }
                Logger.get('rpc').debug('Arguments: {0}'.format(errorInfo['requestInfo']))
        responseBody['error'] = errorInfo

    try:
        jsonResponse = dumps(responseBody, ensure_ascii=True)
    except UnicodeError:
        Logger.get('rpc').exception('Problem encoding JSON response')
        # This is to avoid exceptions due to old data encodings (based on iso-8859-1)
        responseBody['result'] = fix_broken_obj(responseBody['result'])
        jsonResponse = encode(responseBody)

    return app.response_class(jsonResponse, mimetype='application/json')
