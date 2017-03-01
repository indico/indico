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

from indico.core.config import Config

import hashlib

def fetchClasses(module, namespace):
    table = {}

    # search the tree and gather the names

    for name, clazz in module.methodMap.iteritems():
        if namespace:
            name = "%s.%s" % (namespace, name)
        table[name] = clazz

    if hasattr(module,'endpointMap'):
        for n, mod in module.endpointMap.iteritems():
            if namespace:
                n = "%s.%s" % (namespace, n)
            table.update(fetchClasses(mod, n))
    return table



def describeProcedures(module):

    def addIfExists(doc, key, dest):
        if doc.has_key(key):
            dest[key] = doc[key]

    table = fetchClasses(module, None)
    procList = {}

    for name, clazz in table.iteritems():
        proc = procList[name] = {}
        proc['name'] = name
        if hasattr(clazz, '_asyndicoDoc'):
            doc = clazz._asyndicoDoc

            addIfExists(doc, 'summary', proc)
            addIfExists(doc, 'help', proc)
            addIfExists(doc, 'idempotent', proc)
            addIfExists(doc, 'params', proc)
            addIfExists(doc, 'return', proc)

    return procList


def describe(params, remoteHost, session):

    # service description: http://json-rpc.org/wd/JSON-RPC-1-1-WD-20060807.html#ServiceDescription

    from indico.legacy.services.interface.rpc import handlers

    # a unique identifier for the service
    shaObj = hashlib.sha1(Config.getInstance().getBaseURL())
    jsonRpcServiceId = shaObj.hexdigest()
    # endpoint
    jsonRpcServiceURL = Config.getInstance().getBaseURL() + '/services/json-rpc/'
    # procedure description
    jsonRpcServiceProcedures = describeProcedures(handlers)

    return {"name": "Indico JSON-RPC API",
            "sdversion": "1.0",
            "id" : "http://indico.cern.ch/ServiceDirectory/#%s" % jsonRpcServiceId,
            "summary": "This service provides remote access to Indico",
            "help":"%sindex.html" % jsonRpcServiceURL,
            "address": jsonRpcServiceURL,
            "procs": jsonRpcServiceProcedures

            }
