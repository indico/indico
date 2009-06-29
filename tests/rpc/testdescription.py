from jsonrpc import ServiceProxy, JSONRPCException
import pprint
from testenv import endPoint

try:
    result =  endPoint.system.describe()
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(result)
except JSONRPCException,e:
    print repr(e.error)
