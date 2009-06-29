import datetime
from MaKaC.user import LoginInfo
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.user import AvatarHolder

from MaKaC.services.implementation.base import ServiceBase
from MaKaC.services.interface.rpc.common import ServiceError

class SystemLogin(ServiceBase):

    # test.login

    _asyndicoDoc = {
        'summary':  'Logs a user in, provided a username and a password. Returns a cookie in the HTTP header. Returns an informative string.',
        'params': [{'name': 'username', 'type': 'str'},                
                   {'name': 'password', 'type': 'str'}],
        'return': 'str'
        }
    
    def _checkParams(self):
        ServiceBase._checkParams(self)
        
        self._username = self._params.get('username',None)      
        self._password = self._params.get('password',None)
    
    def _getAnswer(self):
        li = LoginInfo( self._username, self._password )   
        auth = AuthenticatorMgr()
        av = auth.getAvatar(li)
        if not av:
            from MaKaC.services.interface.rpc.common import ServiceError
            raise ServiceError("Wrong login or password")
        
        elif not av.isActivated():
            from MaKaC.services.interface.rpc.common import ServiceError
            raise ServiceError("Your account is not active. Please activate it and retry.")
        else:
            self._getSession().setUser( av )
        return '%s OK %s' % (self._username, datetime.datetime.now())

def echo(params, remoteHost, session):

    # test.echo

    _asyndicoDoc = {
        'summary':  'Echoes any parameters that you put in.',
        }
    
    return params

def runCoverage(params, remoteHost, session):

    from MaKaC.services.interface.rpc.process import lookupHandler

    methodList = params['methodList']

    results = {}

    import figleaf
    import cPickle

    for (methodName, args) in methodList:    
        handler = lookupHandler(methodName)

        error = None
        result = None
        
        figleaf.start()
        
        try:
            
            if hasattr(handler, "process"):
                result = handler(args, remoteHost, session).process()
            else:
                result = handler(args, remoteHost, session)

        except Exception, e:
            error = "%s: %s" % (e.__class__, str(e))

        results[methodName] = { 'parameters': args,
                                'result': result,
                                'error': error }

    coverage = figleaf.get_info()
    fData = cPickle.dumps(coverage)        
    
    figleaf.stop()
    
    return {"results": results,
            "figLeafData": fData }

methodMap = {
    "login": SystemLogin,
    "echo": echo,
    "runCoverage": runCoverage
}
