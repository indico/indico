# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import g, session
from werkzeug.exceptions import Forbidden

from indico.core.logger import sentry_set_tags


class ServiceBase(object):
    """
    The ServiceBase class is the basic class for services.
    """

    def __init__(self, params):
        self._params = params

    def _process_args(self):
        pass

    def _check_access(self):
        pass

    def process(self):
        """
        Process the request, analyzing the parameters, and feeding them to the
        _getAnswer() method (implemented by derived classes)
        """

        g.rh = self
        sentry_set_tags({'rh': self.__class__.__name__})

        self._process_args()
        self._check_access()
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
