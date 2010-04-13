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

"""
CDS session management(code adpated from Quixote).  There are two levels to CDS
session management system:
  - SessionManager
  - Session

A SessionManager is responsible for creating sessions, setting and reading
session cookies, maintaining the collection of all sessions, and so forth.
There should be one SessionManager instance per process.
SessionManager is a generic class borrowed from Quixote, the class 
MPSessionManager provides the session management on top of mod_python requests.

A Session is the umbrella object for a single session (notionally, a (user,
host, browser_process) triple).  Simple applications can probably get away
with putting all session data into a Session object (or, better, into an
application-specific subclass of Session).

The default implementation provided here is not persistent: when the
process shuts down, all session data is lost.  You will need to
subclass SessionManager if you want to implement persistent sessions.
"""

#default configuration values
DEFAULT_SESSION_COOKIE_NAME = "MAKACSESSION"
DEFAULT_SESSION_COOKIE_DOMAIN = None 
DEFAULT_SESSION_COOKIE_PATH = "/"
DEFAULT_CHECK_SESSION_ADDR = 0
DEFAULT_SESSION_VALIDITY = float(24 * 3600)

import sys, string, re
from time import time, localtime, strftime, clock
try:
    from mod_python import apache
except ImportError:
    pass

_qparm_re = re.compile(r'([\0- ]*'
                       r'([^\0- ;,=\"]+)="([^"]*)"'
                       r'([\0- ]*[;,])?[\0- ]*)')
_parm_re = re.compile(r'([\0- ]*'
                      r'([^\0- ;,="]+)=([^\0- ;,"]*)'
                      r'([\0- ]*[;,])?[\0- ]*)')

def parse_cookie (text):
    result = {}

    pos = 0
    while 1:
        mq = _qparm_re.match(text, pos)
        m = _parm_re.match(text, pos)
        if mq is not None:
            # Match quoted correct cookies
            name = mq.group(2)
            value = mq.group(3)
            pos = mq.end()
        elif m is not None:
            # Match evil MSIE cookies ;)
            name = m.group(2)
            value = m.group(3)
            pos = m.end()
        else:
            # this may be an invalid cookie.
            # We'll simply bail without raising an error
            # if the cookie is invalid.
            return result

        if not result.has_key(name):
            result[name] = value

    return result


def packbytes(s):
    "convert a string of bytes into a long integer"
    n = 0L
    for b in s:
        n <<= 8
        n |= ord(b)
    return n
    
try:
    # /dev/urandom is just as good as /dev/random for cookies (assuming
    # SHA-1 is secure) and it never blocks.
    open("/dev/urandom")
    def randlong(bytes):
        """Return bits of random data as a long integer."""
        return packbytes(open("/dev/urandom").read(bytes))

except IOError:
    # this is much less secure than the above function
    import sha
    _randstate = sha.new(str(time() + clock()))
    def randlong(bytes):
        """Return bits of random data as a long integer."""
        global _randstate
        s = ""
        while len(s) < bytes:
            _randstate.update(str(time() + clock()))
            s += _randstate.digest()
        return packbytes(s[:bytes])

#-----------------------------------------------------------------------

class SessionManager:
    """
    SessionManager acts as a dictionary of all sessions, mapping session
    ID strings to individual session objects.  Session objects are
    instances of Session (or a custom subclass for your application).
    SessionManager is also responsible for creating and destroying
    sessions, for generating and interpreting session cookies, and for
    session persistence (if any -- this implementation is not
    persistent).

    Most applications can just use this class directly; sessions will
    be kept in memory-based dictionaries, and will be lost when the
    handling process dies.  Alternatively an application can subclass
    SessionManager to implement specific behaviour, such as persistence.

    For working on top of mod_python, the base class must be MPSessionManager.

    Instance attributes:
      session_class : class
        the class that is instantiated to create new session objects
        (in new_session())
      sessions : mapping { session_id:string : Session }
        the collection of sessions managed by this SessionManager
    """

    ACCESS_TIME_RESOLUTION = 1 # in seconds


    def __init__ (self, session_class=None, session_mapping=None):
        """SessionManager(session_class : class = Session,
                          session_mapping : mapping = {})

        Create a new session manager.  There should be one session
        manager per handling process (or even better per application).

        session_class is used by the new_session() method -- it returns
        an instance of session_class.
        """
        self.sessions = {}
        if session_class is None:
            self.session_class = Session
        else:
            self.session_class = session_class
        if session_mapping is None:
            self.sessions = {}
        else:
            self.sessions = session_mapping

    def __repr__ (self):
        return "<%s at %x>" % (self.__class__.__name__, id(self))


    # -- Mapping interface ---------------------------------------------
    # (subclasses shouldn't need to override any of this, unless
    # your application passes in a session_mapping object that
    # doesn't provide all of the mapping methods needed here)

    def keys (self):
        """keys() -> [string]

        Return the list of session IDs of sessions in this session manager.
        """
        return self.sessions.keys()

    def sorted_keys (self):
        """sorted_keys() -> [string]

        Return the same list as keys(), but sorted.
        """
        keys = self.keys()
        keys.sort()
        return keys

    def values (self):
        """values() -> [Session]

        Return the list of sessions in this session manager.
        """
        return self.sessions.values()

    def items (self):
        """items() -> [(string, Session)]

        Return the list of (session_id, session) pairs in this session
        manager.
        """
        return self.sessions.items()

    def get (self, session_id, default=None):
        """get(session_id : string, default : any = None) -> Session

        Return the session object identified by 'session_id', or None if
        no such session.
        """
        return self.sessions.get(session_id, default)

    def __getitem__ (self, session_id):
        """__getitem__(session_id : string) -> Session

        Return the session object identified by 'session_id'.  Raise KeyError
        if no such session.
        """
        return self.sessions[session_id]

    def has_key (self, session_id):
        """has_key(session_id : string) -> boolean

        Return true if a session identified by 'session_id' exists in
        the session manager.
        """
        return self.sessions.has_key(session_id)

    # has_session() is a synonym for has_key() -- if you override
    # has_key(), be sure to repeat this alias!
    has_session = has_key

    def __setitem__ (self, session_id, session):
        """__setitem__(session_id : string, session : Session)

        Store 'session' in the session manager under 'session_id'.
        """
        if not isinstance(session, self.session_class):
            raise TypeError("session not an instance of %r: %r"
                            % (self.session_class, session))
        assert session_id == session.id, "session ID mismatch"
        self.sessions[session_id] = session

    def __delitem__ (self, session_id):
        """__getitem__(session_id : string) -> Session

        Remove the session object identified by 'session_id' from the session
        manager.  Raise KeyError if no such session.
        """
        del self.sessions[session_id]



    # -- Configuration params--------------------------------------------
    # Some configurable aspects. It returns the default values provided
    #   by the module constants. Subclasses can override these methods
    #   and set up the values at their convenience (example: from a 
    #   configuration object)
    def _getSessionCookieName(self):
        """Returns the preferred cookie name for the sessions
        """
        return DEFAULT_SESSION_COOKIE_NAME

    def _getSessionCheckAddress(self):
        """Indicates whether the IP address of the session must be checked
            to ensure a session is only allowed in the scope of a single IP
        """
        return DEFAULT_CHECK_SESSION_ADDR

    def _getSessionCookieDomain(self):
        """Returns the preferred cookie domain for the sessions
        """
        return DEFAULT_SESSION_COOKIE_DOMAIN

    def _getSessionCookiePath(self):
        """Returns the preferred cookie path for the sessions
        """
        return DEFAULT_SESSION_COOKIE_PATH

    # -- Session management --------------------------------------------
    # these build on the storage mechanism implemented by the
    # above mapping methods, and are concerned with all the high-
    # level details of managing web sessions

    def new_session(self, request, id):
        """new_session(request : HTTPRequest, id : string)
           -> Session

        Return a new session object, ie. an instance of the session_class
        class passed to the constructor (defaults to Session).
        """
        return self.session_class(request, id)

    def _get_session_id (self, request):
        """_get_session_id(request : HTTPRequest) -> string

        Find the ID of the current session by looking for the session
        cookie in 'request'.  Return None if no such cookie or the
        cookie has been expired, otherwise return the cookie's value.
        """
        id = request.cookies.get(self._getSessionCookieName())
        if id == "" or id == "*del*":
            return None
        else:
            return id
            
    def _create_session (self, request):
        # Generate a session ID, which is just the value of the session
        # cookie we are about to drop on the user.  (It's also the key
        # used with the session manager mapping interface.)
        id = None
        while id is None or self.has_session(id):
            id = "%016X" % randlong(8)  # 64-bit random number

        # Create a session object which will be looked up the next
        # time this user comes back carrying the session cookie
        # with the session ID just generated.
        return self.new_session(request, id)

    def get_session (self, request):
        """get_session(request : HTTPRequest) -> Session

        Fetch or create a session object for the current session, and
        return it.  If a session cookie is found in the HTTP request
        object 'request', use it to look up and return an existing
        session object.  If no session cookie is found, create a new
        session.  If the session cookie refers to a non-existent
        session, raise SessionError.  If the check_session_addr flag
        is true, then a mismatch between the IP address stored
        in an existing session the IP address of the current request
        also causes SessionError.

        Note that this method does *not* cause the new session to be
        stored in the session manager, nor does it drop a session cookie
        on the user.  Those are both the responsibility of
        maintain_session(), called at the end of a request.
        """
        id = self._get_session_id(request)
        session = None
        if id is not None:
            session = self.get(id)
            if session is None:
                # Note that it's important to revoke the session cookie
                # so the user doesn't keep getting "Expired session ID"
                # error pages.  However, it has to be done in the
                # response object for the error document, which doesn't
                # exist yet.  Thus, the code that formats SessionError
                # exceptions -- SessionError.format() by default -- is
                # responsible for revoking the session cookie.  Yuck.
                raise SessionError(session_id=id)
            if (self._getSessionCheckAddress() and
                session.get_remote_address() != request.get_environ("REMOTE_ADDR")):
                raise SessionError("Remote IP address does not match the "
                                   "IP address that created the session",
                                   session_id=id)
        
        if id is None or session is None:
            # Generate a session ID and create the session.
            session = self._create_session(request)
        
        #check if session is still valid
        if not self.isSessionValid(session):
            #remove the sesion and create a new one
            if self.has_session(session.id):
                del self[session.id]
            session = self._create_session(request)
            
        
        session._set_access_time(self.ACCESS_TIME_RESOLUTION)
        return session

    # get_session ()
    def isSessionValid(self, session):
        if session.get_creation_age() > DEFAULT_SESSION_VALIDITY:
            return False
        return True

    def maintain_session (self, request, session):
        """maintain_session(request : HTTPRequest, session : Session)

        Maintain session information.  This method is called by
        SessionPublisher after servicing an HTTP request, just before
        the response is returned.  If a session contains information it
        is saved and a cookie dropped on the client.  If not, the
        session is discarded and the client will be instructed to delete
        the session cookie (if any).
        """
        if not session.has_info():
            # Session has no useful info -- forget it.  If it previously
            # had useful information and no longer does, we have to
            # explicitly forget it.
            if self.has_session(session.id):
                del self[session.id]
                self.revoke_session_cookie(request)
            return
        if not self.has_session(session.id):
            # This is the first time this session has had useful
            # info -- store it and set the session cookie.
            self[session.id] = session
            self.set_session_cookie(request, session.id)

        elif session.is_dirty():
            # We have already stored this session, but it's dirty
            # and needs to be stored again.  This will never happen
            # with the default Session class, but it's there for
            # applications using a persistence mechanism that requires
            # repeatedly storing the same object in the same mapping.
            self[session.id] = session
        

    def set_session_cookie (self, request, session_id):
        """set_session_cookie(request : HTTPRequest, session_id : string)

        Ensure that a session cookie with value 'session_id' will be
        returned to the client via 'request.response'.
        """
##        request.response.set_cookie(self._getSessionCookieName(), session_id,
##                                    Domain = self._getSessionCookieDomain(),
##                                    Path = self._getSessionCookiePath(),
##                                    Version = "1")
        
        request.response.set_cookie(self._getSessionCookieName(), session_id,
                                    Path = self._getSessionCookiePath(),
                                    Version = "1")
        

    def revoke_session_cookie (self, request):
        """revoke_session_cookie(request : HTTPRequest)

        Remove the session cookie from the remote user's session by
        resetting the value and maximum age in 'request.response'.  Also
        remove the cookie from 'request' so that further processing of
        this request does not see the cookie's revoked value.
        """
        response = request.response
        response.set_cookie(self._getSessionCookieName(), "",
                            domain = self._getSessionCookieDomain(),
                            path = self._getSessionCookiePath(),
                            max_age = 0)
        if request.cookies.has_key(self._getSessionCookieName()):
            del request.cookies[self._getSessionCookieName()]

    def expire_session (self, request):
        """expire_session(request : HTTPRequest)

        Expire the current session, ie. revoke the session cookie from
        the client and remove the session object from the session
        manager and from 'request'.
        """
        self.revoke_session_cookie(request)
        try:
            del self[request.session.id]
        except KeyError:
            # This can happen if the current session hasn't been saved
            # yet, eg. if someone tries to leave a session with no
            # interesting data.  That's not a big deal, so ignore it.
            pass
        request.session = None

    def has_session_cookie (self, request, must_exist=0):
        """has_session_cookie(request : HTTPRequest,
                              must_exist : boolean = false)
           -> boolean

        Return true if 'request' already has a cookie identifying a
        session object.  If 'must_exist' is true, the cookie must
        correspond to a currently existing session; otherwise (the
        default), we just check for the existence of the session cookie
        and don't inspect its content at all.
        """
        id = request.cookies.get(self._getSessionCookieName())
        if id is None:
            return 0
        if must_exist:
            return self.has_session(id)
        else:
            return 1

# SessionManager


class Session:
    """
    Holds information about the current session.  The only information
    that is likely to be useful to applications is the 'user' attribute,
    which applications can use as they please.

    Instance attributes:
      id : string
        the session ID (generated by SessionManager and used as the
        value of the session cookie)
      __remote_address : string
        IP address of user owning this session (only set when the
        session is created -- requests for this session from a different
        IP address will either raise SessionError or be treated
        normally, depending on the CHECK_SESSION_ADDR flag)
      __creation_time : float
      __access_time : float
        two ways of keeping track of the "age" of the session.
        Note that '__access_time' is maintained by the SessionManager that
        owns this session, using _set_access_time().

    Feel free to access 'id' directly, but do not modify it. The other
    attributes are private -- keep your grubby hands off of them and use
    the appropriate accessor methods.
    """

    MAX_FORM_TOKENS = 16 # maximum number of outstanding form tokens

    def __init__ (self, request, id):
        self.id = id
        self.__remote_address = request.get_environ("REMOTE_ADDR")
        self.__creation_time = self.__access_time = time()
        self._lang=None

    def __repr__ (self):
        return "<%s at %x: %s>" % (self.__class__.__name__, id(self), self.id)

    def __str__ (self):
        return "session %s" % self.id

    def has_info (self):
        """has_info() -> boolean

        Return true if this session contains any information that must
        be saved.
        """
        return 1

    def is_dirty (self):
        """is_dirty() -> boolean

        Return true if this session has changed since it was last saved
        such that it needs to be saved again.
        
        Default implementation always returns false since the default
        storage mechanism is an in-memory dictionary, and you don't have
        to put the same object into the same slot of a dictionary twice.
        If sessions are stored to, eg., files in a directory or slots in
        a hash file, is_dirty() should probably be an alias or wrapper
        for has_info().  See doc/session-mgmt.txt.
        """
        return 0

    def dump (self, file=None, header=1, deep=1):
        time_fmt = "%Y-%m-%d %H:%M:%S"
        ctime = strftime(time_fmt, localtime(self.__creation_time))
        atime = strftime(time_fmt, localtime(self.__access_time))

        if header:
            file.write('session %s:' % self.id)
        file.write('  user %s' % self.user)
        file.write('  __remote_address: %s' % self.__remote_address)
        file.write('  created %s, last accessed %s' % (ctime, atime))
        file.write('  _form_tokens: %s\n' % self._form_tokens)

    # dump()


    # -- Simple accessors and modifiers --------------------------------

    def get_remote_address (self):
        """Return the IP address (dotted-quad string) that made the
        initial request in this session.
        """
        return self.__remote_address

    def get_creation_time (self):
        """Return the time that this session was created (seconds
        since epoch).
        """
        return self.__creation_time

    def get_access_time (self):
        """Return the time that this session was last accessed (seconds
        since epoch).
        """
        return self.__access_time

    def get_creation_age (self, _now=None):
        """Return the number of seconds since session was created."""
        # _now arg is not strictly necessary, but there for consistency
        # with get_access_age()
        return (_now or time()) - self.__creation_time

    def get_access_age (self, _now=None):
        """Return the number of seconds since session was last accessed."""
        # _now arg is for SessionManager's use
        return (_now or time()) - self.__access_time


    # -- Methods for SessionManager only -------------------------------

    def _set_access_time (self, resolution):
        now = time()
        if now - self.__access_time > resolution:
            self.__access_time = now

#    def getLang(self):
  #      return self._lang
    
  #  def setLang(self,lang):
   #     self._lang=lang

class MPSessionManager(SessionManager):
    """Specialised SessionManager which allows to use Quixote's session 
       management system with mod_python request objects. The role of this
       class is basically convert mod_python request objects in other type
       of objects (RequestWrapper) which can be handled by the SessionManager
       class.
       With this we are able to re-use the Quixote's code (very few 
       modifications have been done) in a very transparent way.
    """
    
    def get_session (self, request):
        """Proxy method to SessionManager get_session. It converts the 
           mod_python request objects in a SessionManager compatible one
           and executes the parent implementation passing the compatible object
        """
        rw = RequestWrapper.getWrapper( request )
        s = SessionManager.get_session( self, rw )
        rw.setSession( s )
        return s
        
    def maintain_session (self, request, session):
        """Proxy method to SessionManager maintain_session. It converts the 
           mod_python request objects in a SessionManager compatible one
           and executes the parent implementation passing the compatible object
        """
        rw = RequestWrapper.getWrapper( request )
        SessionManager.maintain_session( self, rw, session )
        
    def has_session_cookie (self, request, must_exist=0):
        """Proxy method to SessionManager has_session_cookie. It converts the 
           mod_python request objects in a SessionManager compatible one
           and executes the parent implementation passing the compatible object
        """
        rw = RequestWrapper.getWrapper( request )
        return SessionManager.has_session_cookie( self, rw, must_exist )

    def expire_session (self, request):
        """Proxy method to SessionManager expire_session. It converts the 
           mod_python request objects in a SessionManager compatible one
           and executes the parent implementation passing the compatible object
        """
        rw = RequestWrapper.getWrapper( request )
        SessionManager.expire_session(self, rw )
    
    def revoke_session_cookie (self, request):
        rw = RequestWrapper.getWrapper( request )
        SessionManager.revoke_session_cookie(self, rw )

    def delete_session(self, id):
        try:
            del self[id]
        except KeyError:
            # This can happen if the current session hasn't been saved
            # yet, eg. if someone tries to leave a session with no
            # interesting data.  That's not a big deal, so ignore it.
            pass


class RequestWrapper:
    """This class implements a HTTP request which is compatible with Quixote's
       session management system. It builds a wrapper arround mod_python request
       objects to adapt it to Quixote's classes.
       Intance attributes:
            __request: MPRequest
                Reference to the wrapped mod_python request object
            cookies: Dictionary
                Conatins the received cookies (these found in headers_in) 
                indexed by the cookie name
            environ: Dictionary
                Contains a list of different variables or parameters of the
                HTTP request
            response: ResponseWrapper
                Reference to the HTTP response wrapping object
            session: Session
                Refence to the current session associated with the request,
                if any
    """

    def __init__(self, request):
        """Constructor of the class. Initialises the necessesary values. It 
            should never be used, use getWrapper method instead.
        """
        self.__request = request
        try:
            self.cookies = parse_cookie(self.__request.headers_in[ "Cookie" ])
        except KeyError, e:
            self.cookies = {}
        self.environ = {}
        try:
            self.environ["REMOTE_ADDR"] = self.__request.get_remote_host(apache.REMOTE_NOLOOKUP)
        except AttributeError:
            self.environ["REMOTE_ADDR"] = ""
        self.response = ResponseWrapper( request )
        try:
            self.session = request.session
        except AttributeError, e:
            self.session = None
        request.cds_wrapper = self #sticks the current wrapper to the mp request
                                   # so in succesive request it can be recovered

    def getWrapper( req ):
        """Returns a RequestWrapper for a given request.
            
            The session manager modifies the contents of the wrapper and 
            therefore its state must be kept. This method returns the request 
            sticked wrapper (carrying the current status) and if it doesn't
            have any it creates a new one. The RequestWrapper initialisation
            method will take care of sticking any new wrapper to the request.
        """
        try:
            w = req.cds_wrapper
        except AttributeError:
            w = RequestWrapper( req )
        return w
    getWrapper = staticmethod( getWrapper )

    def get_environ(self, name):
        """Returns a "environ" variable value
        """
        return self.environ[name]

    def setSession(self, session):
        """Sets the reference to a sessioni. It also sets this reference in the
           mod_python request object so it can be kept for future requests.
        """
        self.session = session
        self.__request.session = session


class ResponseWrapper:
    """This class implements a HTTP response which is compatible with Quixote's
       session management system. It builds a wrapper arround mod_python request
       objects to adapt it to Quixote's classes.
       Instance attributes:
            request: RequestWrapper
                Reference to the request object to which this will represent 
                the reply
    """
    
    def __init__(self, request):
        """Constructor of the class.
        """
        self.request = request

    def set_cookie(self, cookie_name, cookie_value, **attrs):
        """
        """
        options = ""
        for (name, value) in attrs.items():
            if value is None:
                continue
            if name in ("Max_age", "Path", "Domain", "Path", "Version"):
                name = name.replace("_", "-")
                options += "; %s=%s"%(name, value)
            elif name =="secure" and value:
                options += "; secure"
        self.request.headers_out["Set-Cookie"] = "%s=%s%s"%(cookie_name, cookie_value, options)


class SessionError(Exception):
    """
    """

    def __init__(self, msg="", **args):
        pass
