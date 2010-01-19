# -*- coding: utf-8 -*-
##
## $Id: base.py,v 1.39 2009/06/25 15:21:49 jose Exp $
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

from MaKaC.conference import Category
from MaKaC.common.PickleJar import DictPickler

import sys, traceback, time, os

from pytz import timezone
from datetime import datetime, date

from MaKaC import conference
from MaKaC.common.timezoneUtils import setAdjustedDate
from MaKaC.common import security

from MaKaC.errors import MaKaCError, htmlScriptError, htmlForbiddenTag, TimingError
from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError, HTMLSecurityError, Warning,\
    ResultWithWarning

from MaKaC.webinterface.rh.base import RequestHandlerBase
from MaKaC.webinterface.mail import GenericMailer, GenericNotification

from MaKaC.accessControl import AccessWrapper

from MaKaC.i18n import _

"""
base module for asynchronous server requests
"""

# Just for Python 2.4 compatibility
def parseDateTime(dt, format):
    return datetime(*(time.strptime(dt, format)[0:6]))

class ExpectedParameterException(ServiceError):
    """
    Represents an exception that occurs when a type of parameter was expected
    but another one was obtained
    """

    def __init__(self, paramName, expected, got):
        ServiceError.__init__(self, "ERR-P2","'%s': Expected '%s', got instead '%s'" % (paramName, expected, got))

class EmptyParameterException(ServiceError):
    """
    Thrown when a parameter that should have a value is empty
    """
    def __init__(self, paramName=""):
        ServiceError.__init__(self, "ERR-P3","Expected parameter '%s' is empty"%paramName)

class ParameterManager(object):

    """
    The ParameterManager makes parameter processing a bit easier, by providing
    some default transformations
    """

    def __init__(self, paramList, allowEmpty=False, timezone=None):
        self._paramList = paramList
        self._allowEmpty = allowEmpty
        self._timezone = timezone

    def extract(self, paramName, pType=None, allowEmpty=None, defaultValue=None):
        """
        Extracts a parameter, given a parameter name, and optional type
        """

        # "global" policy applies if allowEmpty not set
        if (allowEmpty == None):
            allowEmpty = self._allowEmpty

        value = self._paramList.get(paramName)


        if (not allowEmpty) and (value == None):
            raise EmptyParameterException(paramName)

        if pType == str:
            if value != None:
                value = str(value)
            else:
                value = defaultValue

            if (value == '' or value == None) and not allowEmpty:
                raise EmptyParameterException(paramName)
        elif pType == datetime:
            # format will possibly be accomodated to different standards,
            # in the future

            # both strings and objects are accepted
            if type(value) == str:
                naiveDate = parseDateTime(value,'%Y/%m/%d %H:%M')
            else:
                naiveDate = parseDateTime(value['date']+' '+value['time'][:5], '%Y/%m/%d %H:%M')

            if self._timezone:
                value = timezone(self._timezone).localize(naiveDate).astimezone(timezone('utc'))
            else:
                value = naiveDate
        elif pType == date:
            # format will possibly be accomodated to different standards,
            # in the future
            value = parseDateTime(value,'%Y/%m/%d').date()
        elif pType == int:
            if value == None and allowEmpty:
                value = None
            else:
                value = int(value)
        elif pType == float:
            if value == None and allowEmpty:
                value = None
            else:
                value = float(value)
        elif pType == dict:
            if not (type(value) == dict or (allowEmpty and value == None)):
                raise ExpectedParameterException(paramName, dict, type(value))
        elif pType == list:
            if not (type(value) == list or (allowEmpty and value == None)):
                raise ExpectedParameterException(paramName, list, type(value))
        elif pType == bool:
            if not (type(value) == bool or (allowEmpty and value == None)):
                raise ExpectedParameterException(paramName, list, type(value))

        return value

    def setTimezone(self, tz):
        self._timezone = tz

class ServiceBase(RequestHandlerBase):
    """
    The ServiceBase class is the basic class for services.
    """

    def __init__(self, params, remoteHost, session):
        """
        Constructor.  Initializes provate variables
        @param req: HTTP Request provided by the previous layer
        """
        self._params = params
        self._requestStarted = False
        self._websession = session
        # Fill in the aw instance with the current information
        self._aw = AccessWrapper()
        self._aw.setIP(remoteHost)
        self._aw.setSession(session)
        self._aw.setUser(session.getUser())
        self._target = None
        self._startTime = None
        self._endTime = None
        self._doProcess = True  #Flag which indicates whether the RH process
                                #   must be carried out; this is useful for
                                #   the checkProtection methods
        self._tempFilesToDelete = []
    
    # Methods =============================================================
        
    def _getSession( self ):
        """
        Returns the web session associated to the received mod_python 
        request.
        """
        return self._websession
    
    def _checkParams(self):
        """
        Checks the request parameters (normally overloaded)
        """
        pass
    
    def _checkProtection( self ):
        """
        Checks protection when accessing resources (normally overloaded)
        """
        pass

    def _processError(self):
        """
        Treats errors occured during the process of a RH, returning an error string.
        @param e: the exception
        @type e: An Exception-derived type
        """
        
        trace = traceback.format_exception(*sys.exc_info())
        
        return ''.join(trace)

    def _sendEmails( self ):
        if hasattr( self, "_emailsToBeSent" ):
            for email in self._emailsToBeSent:
                GenericMailer.send(GenericNotification(email))

    def _deleteTempFiles( self ):
        if len(self._tempFilesToDelete) > 0:
            for file in self._tempFilesToDelete:
                os.remove(file)
      
    def process(self):
        """
        Processes the request, analyzing the parameters, and feeding them to the
        _getAnswer() method (implemented by derived classes)
        """

        self._setLang()
        self._checkParams()
        self._checkProtection()

        try:
            security.sanitizationCheck(self._target,
                                   self._params,
                                   self._aw)
        except (htmlScriptError, htmlForbiddenTag), e:
            raise HTMLSecurityError('ERR-X0','HTML Security problem - you might be using forbidden tags: %s ' % str(e))
            
        if self._doProcess:
            answer = self._getAnswer()

            self._sendEmails()
            self._deleteTempFiles()
            
            return answer 

    def _getAnswer(self):
        """
        To be overloaded. It should contain the code that does the actual
        business logic and returns a result (python JSON-serializable object).
        If this method is not overloaded, an exception will occur.
        If you don't want to return an answer, you should still implement this method with 'pass'.
        """
        # This exception will happen if the _getAnswer method is not implemented in a derived class
        raise MaKaCError("No answer was returned")



class ProtectedService(ServiceBase):
    """
    A ProtectedService can only be accessed by authenticated users
    """

    def _checkSessionUser(self):
        """
        Checks that the current user exists (is authenticated)
        """
        if self._getUser() == None:
            self._doProcess = False
            raise ServiceAccessError("ERR-P4", "You are currently not authenticated. Please log in again.")

    def _checkProtection(self):
        """
        Overloads ServiceBase._checkProtection, assuring that the user
        is authenticated
        """
        ServiceBase._checkProtection(self)
        self._checkSessionUser()


class ProtectedDisplayService(ProtectedService):
    """
    A ProtectedDisplayService can only be accessed by users that
    are authorized to "see" the target resource
    """
    
    def _checkProtection( self ):
        """
        Overloads ProtectedService._checkProtection, assuring that
        the user is authorized to view the target resource
        """
        if not self._target.canView( self.getAW() ):
            
            from MaKaC.conference import Link, LocalFile

            # in some cases, the target does not directly have an owner
            if (isinstance(self._target, Link) or
                isinstance(self._target, LocalFile)):
                target = self._target.getOwner()
            else:
                target = self._target
            if not isinstance(target, Category):
                if target.getAccessKey() != "" or target.getConference().getAccessKey() != "":
                    raise ServiceAccessError("ERR-P4", "You are currently not authenticated or cannot access this service. Please log in again if necessary.")
            if self._getUser() == None:
                self._checkSessionUser()
            else:
                raise ServiceAccessError("ERR-P4", "You cannot access this service. Please log in again if necessary.")


class LoggedOnlyService(ProtectedService):
    """
    Nothing new relating to ProtectedService,
    but the name is nicer, and didn't want to break
    the Protected(.*)Service name scheme
    """
    pass

            

class ProtectedModificationService(ProtectedService):
    """
    A ProtectedModificationService can only be accessed by users that
    are authorized to modify the target resource
    """
    def _checkProtection( self ):
        """
        Overloads ProtectedService._checkProtection, so that it is
        verified if the user has modification access to the resource
        """

        target = self._target
        if (type(target) == conference.SessionSlot):
            target = target.getSession()
        
        if not target.canModify( self.getAW() ):
            if target.getModifKey() != "":
                raise ServiceAccessError("ERR-P5", "You don't have the rights to modify this object")
            if self._getUser() == None:
                self._checkSessionUser()
            else:
                raise ServiceAccessError("ERR-P5", "You don't have the rights to modify this object")
        if hasattr(self._target, "getConference") and hasattr(self._target, "isClosed"):
            if target.getConference().isClosed():
                raise ServiceAccessError("ERR-P6", "Conference %s is closed"%target.getConference().getId())

class AdminService(ProtectedService):
    """
    A AdminService can only be accessed by administrators
    """
    def _checkProtection( self ):
        """
        Overloads ProtectedService._checkProtection
        """

        ProtectedService._checkProtection(self)

        if not self._getUser().isAdmin():
            raise ServiceAccessError("ERR-P7", _("Only administrators can perform this operation"))

class TextModificationBase( object ):
    """
    Base class for text field modification
    """

    def _getAnswer( self ):
        """ Calls _handleGet() or _handleSet() on the derived classes, in order to make it happen. Provides
            them with self._value.
            
            When calling _handleGet(), it will return the value to return.
            When calling _handleSet(), it will return:
            -either self._value if there were no problems
            -either a FieldModificationWarning object (pickled) if there are warnings to give to the user
        """

        # fetch the 'value' parameter (default for text)
        if self._params.has_key('value'):
            self._value = self._params['value']
        else:
            # None if not passed
            self._value = None

        if self._value == None:
            return self._handleGet()
        else:
            setResult = self._handleSet()
            if isinstance(setResult, Warning):
                return DictPickler.pickle(ResultWithWarning(self._value, setResult))
            else:
                return self._value

class HTMLModificationBase( object ):
    """
    Base class for HTML field modification
    """
    def _getAnswer( self ):
        """
        Calls _handle() on the derived classes, in order to make it happen. Provides
        them with self._value.
        """
        
        if self._params.has_key('value'):
            self._value = self._params['value']
        else:
            self._value = None
        
        if self._value == None:
            return self._handleGet()
        else:
            self._handleSet()
        
        return self._value


class DateTimeModificationBase( TextModificationBase ):
    """ Date and time modification base class
        Its _handleSet method is called by TextModificationBase's _getAnswer method.
        DateTimeModificationBase's _handletSet method will call the _setParam method
        from the classes that inherits from DateTimeModificationBase.
        _handleSet will return whatever _setParam returns (usually None if there were no problems,
        or a FieldModificationWarning object with information about a problem / warning to give to the user) 
    """
    def _handleSet(self):
        try:
            naiveDate = parseDateTime(self._value,'%d/%m/%Y %H:%M')
        except ValueError:
            raise ServiceError("ERR-E2",
                               "Date/time is not in the correct format")

        try:
            self._pTime = setAdjustedDate(naiveDate, self._conf)
            return self._setParam()
        except TimingError,e:
            raise ServiceError("ERR-E2", e.getMsg())

class ListModificationBase ( object ):
    """ Base class for a list modification.
        The class that inherits from this must have:
        -a _handleGet() method that returns a list.
        -a _handleSet() method which can use self._value to process the input. self._value will be a list.
    """
    
    def _getAnswer(self):
        if self._params.has_key('value'):
            pm = ParameterManager(self._params)
            self._value = pm.extract("value", pType=list, allowEmpty=True)
        else:
            self._value = None
            
        if self._value == None:
            return self._handleGet()
        else:
            self._handleSet()
        
        return self._value

class TwoListModificationBase ( object ):
    """ Base class for two lists modification.
        The class that inherits from this must have:
        -a _handleGet() method that returns a list, given self._destination
        -a _handleSet() method which can use self._value and self._destination to process the input.
        self._value will be a list. self._destination will be 'left' or 'right'
    """
    
    def _getAnswer(self):
        self._destination = self._params.get('destination', None)
        if self._destination == None or (self._destination != 'right' and self._destination != 'left'):
            #TODO: add this error to the wiki
            raise ServiceError("ERR-E4", 'Destination list not set to "right" or "left"')
            
        if self._params.has_key('value'):
            pm = ParameterManager(self._params)
            self._value = pm.extract("value", pType=list, allowEmpty=False)
        else:
            self._value = None
            
        if self._value == None:
            return self._handleGet()
        else:
            self._handleSet()
        
        return self._value
    

