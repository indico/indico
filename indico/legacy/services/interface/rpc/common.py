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

import sys
import traceback
from indico.legacy.common.fossilize import Fossilizable, fossilizes
from indico.legacy.fossils.error import ICausedErrorFossil, INoReportErrorFossil


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

    def __init__(self, message, inner=None, title=None, explanation=None):
        CausedError.__init__(self, "", message, inner, "noReport")
        self._title = title
        self._explanation = explanation

    def getTitle(self):
        """
        A title for the error (optional)
        """
        return self._title

    def getExplanation(self):
        return self._explanation


class CSRFError(NoReportError):
    def __init__(self):
        NoReportError.__init__(self, _('Oops, looks like there was a problem with your current session. Please refresh the page and try again.'))
        self.code = 'ERR-CSRF'


class RequestError(CausedError):
    pass


class ProcessError(CausedError):

    def __init__(self, code, message):
        CausedError.__init__(self, code, message, inner = traceback.format_exception(*sys.exc_info()))


class ServiceError(CausedError):
    def __init__(self, code='', message='', inner = None):
        CausedError.__init__(self, code, message, inner)


class HTMLSecurityError(CausedError):
    pass


class ServiceAccessError(NoReportError):
    pass

