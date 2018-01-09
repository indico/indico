# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from flask import g, session
from werkzeug.exceptions import Forbidden

from indico.core.logger import sentry_set_tags
from indico.legacy.common.security import Sanitization
from indico.util.string import unicode_struct_to_utf8


class ServiceBase(object):
    """
    The ServiceBase class is the basic class for services.
    """

    UNICODE_PARAMS = False
    CHECK_HTML = True

    def __init__(self, params):
        if not self.UNICODE_PARAMS:
            params = unicode_struct_to_utf8(params)
        self._params = params

    def _process_args(self):
        pass

    def _check_access(self):
        pass

    def process(self):
        """
        Processes the request, analyzing the parameters, and feeding them to the
        _getAnswer() method (implemented by derived classes)
        """

        g.rh = self
        sentry_set_tags({'rh': self.__class__.__name__})

        self._process_args()
        self._check_access()

        if self.CHECK_HTML:
            Sanitization.sanitizationCheck(self._params)
        return self._getAnswer()

    def _getAnswer(self):
        """
        To be overloaded. It should contain the code that does the actual
        business logic and returns a result (python JSON-serializable object).
        If this method is not overloaded, an exception will occur.
        If you don't want to return an answer, you should still implement this method with 'pass'.
        """
        raise NotImplementedError


class LoggedOnlyService(ServiceBase):
    def _check_access(self):
        if session.user is None:
            raise Forbidden("You are currently not authenticated. Please log in again.")
