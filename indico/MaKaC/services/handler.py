try:
    from mod_python import apache
except ImportError:
    pass
import MaKaC.services.interface.rpc.json as jsonrpc


def handler(req):
    # runs services according to the URL
    if req.uri.endswith('json-rpc'):
        return jsonrpc_handler(req)
    elif req.uri.endswith('test'):
        return test_handler(req)
    else:
        req.write('Service not found!')
        return apache.HTTP_NOT_FOUND

def jsonrpc_handler(req):
    return jsonrpc.process(req)

def test_handler(req):
    req.write("InDiCo")
    return apache.OK
