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


import distutils
import os
import sys
import traceback
from datetime import datetime, date

from flask import request, session
from pytz import timezone


from MaKaC.common.timezoneUtils import setAdjustedDate
from MaKaC.common import security
from MaKaC.common.utils import parseDateTime

from MaKaC.errors import MaKaCError, HtmlForbiddenTag, TimingError
from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError, HTMLSecurityError, Warning,\
    ResultWithWarning

from MaKaC.webinterface.rh.base import RequestHandlerBase

from MaKaC.accessControl import AccessWrapper

from MaKaC.i18n import _
from MaKaC.common.contextManager import ContextManager

from indico.core.config import Config
from indico.util.string import unicode_struct_to_utf8


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


class DateTimeParameterException(ServiceError):
    """
    Thrown when a parameter that should have a value is empty
    """
    def __init__(self, paramName, value):
        ServiceError.__init__(self, "ERR-P4","Date/Time %s = '%s' is not valid " % (paramName, value))


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
        if allowEmpty is None:
            allowEmpty = self._allowEmpty

        value = self._paramList.get(paramName)
        if value is None:
            if allowEmpty:
                value = defaultValue
            else:
                raise EmptyParameterException(paramName)

        if value is not None:
            if pType == str:
                value = str(value)
            elif pType == int:
                value = int(value)
            elif pType == float:
                value = float(value)
            elif pType == bool:
                if not type(value) == bool:
                    try:
                        value = distutils.util.strtobool(str(value))
                    except ValueError:
                        raise ExpectedParameterException(paramName, bool, type(value))
            elif pType == dict:
                if not type(value) == dict:
                    raise ExpectedParameterException(paramName, dict, type(value))
            elif pType == list:
                if not type(value) == list:
                    raise ExpectedParameterException(paramName, list, type(value))
            elif pType == date:
                # format will possibly be accomodated to different standards,
                # in the future
                value = datetime.strptime(value, '%Y/%m/%d').date()
            elif pType == datetime:
                # format will possibly be accomodated to different standards,
                # in the future
                try:
                    # both strings and objects are accepted
                    if isinstance(value, basestring):
                        naiveDate = datetime.strptime(value, '%Y/%m/%d %H:%M')
                    elif value:
                        naiveDate = datetime.strptime(value['date']+' '+value['time'][:5], '%Y/%m/%d %H:%M')
                    else:
                        naiveDate = None
                except ValueError:
                    raise DateTimeParameterException(paramName, value)

                if self._timezone and naiveDate:
                    value = timezone(self._timezone).localize(naiveDate).astimezone(timezone('utc'))
                else:
                    value = naiveDate

        if (value is None or value == "") and not allowEmpty:
            EmptyParameterException(paramName)

        return value

    def setTimezone(self, tz):
        self._timezone = tz


class ServiceBase(RequestHandlerBase):
    """
    The ServiceBase class is the basic class for services.
    """

    UNICODE_PARAMS = False
    CHECK_HTML = True

    def __init__(self, params):
        if not self.UNICODE_PARAMS:
            params = unicode_struct_to_utf8(params)
        self._reqParams = self._params = params
        self._requestStarted = False
        # Fill in the aw instance with the current information
        self._aw = AccessWrapper()
        self._aw.setUser(session.avatar)
        self._target = None
        self._startTime = None
        self._tohttps = request.is_secure
        self._endTime = None
        self._doProcess = True  #Flag which indicates whether the RH process
                                #   must be carried out; this is useful for
                                #   the checkProtection methods
        self._tempFilesToDelete = []

    # Methods =============================================================

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

    def _deleteTempFiles( self ):
        if len(self._tempFilesToDelete) > 0:
            for file in self._tempFilesToDelete:
                os.remove(file)

    def process(self):
        """
        Processes the request, analyzing the parameters, and feeding them to the
        _getAnswer() method (implemented by derived classes)
        """

        ContextManager.set('currentRH', self)

        self._checkParams()
        self._checkProtection()

        if self.CHECK_HTML:
            try:
                security.Sanitization.sanitizationCheck(self._target, self._params, self._aw, ['requestInfo'])
            except HtmlForbiddenTag as e:
                raise HTMLSecurityError('ERR-X0', 'HTML Security problem. {}'.format(e))

        if self._doProcess:
            if Config.getInstance().getProfile():
                import profile, pstats, random
                proffilename = os.path.join(Config.getInstance().getTempDir(), "service%s.prof" % random.random())
                result = [None]
                profile.runctx("result[0] = self._getAnswer()", globals(), locals(), proffilename)
                answer = result[0]
                rep = Config.getInstance().getTempDir()
                stats = pstats.Stats(proffilename)
                stats.sort_stats('cumulative', 'time', 'calls')
                stats.dump_stats(os.path.join(rep, "IndicoServiceRequestProfile.log"))
                os.remove(proffilename)
            else:
                answer = self._getAnswer()
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
    def _checkSessionUser(self):
        """
        Checks that the current user exists (is authenticated)
        """

        if self._getUser() is None:
            self._doProcess = False
            raise ServiceAccessError("You are currently not authenticated. Please log in again.")


class LoggedOnlyService(ProtectedService):
    """
    Only accessible to users who are logged in (access keys not allowed)
    """

    def _checkProtection( self ):
        self._checkSessionUser()


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
        if not target.canModify( self.getAW() ):
            if self._getUser() is None:
                self._checkSessionUser()
            else:
                raise ServiceAccessError("You don't have the rights to modify this object")
        if hasattr(self._target, "getConference") and hasattr(self._target, "isClosed"):
            if target.getConference().isClosed():
                raise ServiceAccessError("Conference %s is closed"%target.getConference().getId())

class AdminService(LoggedOnlyService):
    """
    A AdminService can only be accessed by administrators
    """
    def _checkProtection(self):
        LoggedOnlyService._checkProtection(self)
        if not session.user.is_admin:
            raise ServiceAccessError(_("Only administrators can perform this operation"))

class TextModificationBase:
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
                return ResultWithWarning(self._value, setResult).fossilize()
            else:
                return self._value

class HTMLModificationBase:
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
            naiveDate = parseDateTime(self._value)
        except ValueError:
            raise ServiceError("ERR-E2",
                               "Date/time is not in the correct format")

        try:
            self._pTime = setAdjustedDate(naiveDate, self._conf)
            return self._setParam()
        except TimingError,e:
            raise ServiceError("ERR-E2", e.getMessage())


class ListModificationBase:
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
