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

from MaKaC.common.PickleJar import Retrieves
import sys
import traceback
from MaKaC.common.fossilize import Fossilizable, fossilizes
from MaKaC.fossils.error import ICausedErrorFossil, INoReportErrorFossil

class CausedError(Exception, Fossilizable):

    """
    A normal error, triggered on the server side
    """

    fossilizes(ICausedErrorFossil)

    def __init__(self, code, message, inner=None, type=None):
        self.code = code
        self.message = message
        self.inner = inner
        self.type = type

    def getMessage(self):
        return self.message

    def getCode(self):
        return self.code

    def getInner(self):
        return self.inner

    def getType(self):
        return self.type

    def __str__(self):
        if not self.inner:
            return "%s : %s (no inner exception)" % (self.code, self.message)
        else:
            if type(self.inner) is list:
                inner = "\r\n".join(self.inner)
            else:
                inner = self.inner
            return "%s : %s\r\n\r\nInner Exception:\r\n%s" % (self.code, self.message, inner)

class NoReportError(CausedError):
    """
    An error that doesn't get reported (no log entry, no warning e-mail,
    no error report form)
    """

    fossilizes(INoReportErrorFossil)

    def __init__(self, code, message, inner=None, title=None, explanation=None):
        CausedError.__init__(self, code, message, inner, "noReport")
        self._title = title
        self._explanation = explanation

    def getTitle(self):
        """
        A title for the error (optional)
        """
        return self._title

    def getExplanation(self):
        return self._explanation

class RequestError(CausedError):
    pass

class ProcessError(CausedError):

    def __init__(self, code, message):
        CausedError.__init__(self, code, message, inner = traceback.format_exception(*sys.exc_info()))

class ServiceError(CausedError):
    pass

class PermissionError(CausedError):
    pass

class HTMLSecurityError(CausedError):
    pass

class ServiceAccessError(NoReportError):
    pass

class TimingNoReportError(NoReportError):
    pass


class Warning(object):

    def __init__(self, title, content):
        self._title = title
        self._content = content

    @Retrieves(['MaKaC.services.interface.rpc.common.Warning'], 'title')
    def getTitle(self):
        return self._title

    @Retrieves(['MaKaC.services.interface.rpc.common.Warning'], 'content')
    def getProblems(self):
        return self._content

class ResultWithWarning(object):

    def __init__(self, result, warning):
        self._result = result
        self._warning = warning

    @Retrieves(['MaKaC.services.interface.rpc.common.ResultWithWarning'], 'result', isPicklableObject = True)
    def getResult(self):
        return self._result

    @Retrieves(['MaKaC.services.interface.rpc.common.ResultWithWarning'], 'warning', isPicklableObject = True)
    def getWarning(self):
        return self._warning

    @Retrieves(['MaKaC.services.interface.rpc.common.ResultWithWarning'], 'hasWarning')
    def hasWarning(self):
        return True
