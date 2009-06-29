from MaKaC.common import Config

import sha

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

    from MaKaC.services.interface.rpc import handlers

    # a unique identifier for the service
    shaObj = sha.new(Config.getInstance().getBaseURL())
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
