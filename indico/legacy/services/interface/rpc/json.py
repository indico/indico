# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, request

from indico.core.logger import Logger
from indico.legacy.services.interface.rpc.process import invoke_method
from indico.util.fossilize import clearCache


def process():
    clearCache()
    payload = request.json
    Logger.get('rpc').info('json rpc request. request: %r', payload)
    rv = {}
    if 'id' in payload:
        rv['id'] = payload['id']
    rv['result'] = invoke_method(str(payload['method']), payload.get('params', []))
    return jsonify(rv)
