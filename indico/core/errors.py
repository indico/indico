# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

"""
Module containing the Indico exception class hierarchy
"""

from ..util.i18n import _


class IndicoError(Exception):

    code = -32000  # json-rpc server specific errors starting code

    def __init__(self, message='', area='', explanation=''):
        self._message = message
        self._area = area
        self._explanation = explanation

    def __str__(self):
        if self._area:
            return '{} - {}'.format(self._area, self._message)
        else:
            return self._message

    def getMessage(self):
        return self._message

    def getArea(self):
        return self._area

    def getExplanation(self):
        """
        Some extra information, like actions that can be taken
        """
        return self._explanation

    def toDict(self):
        return {
            'code': self.code,
            'message': self.getMessage(),
            'data': self.__dict__
        }


class AccessControlError(IndicoError):
    """
    """

    def __init__(self, **kw):
        self._object_type = kw.pop('object_type', 'object')
        super(AccessControlError, self).__init__(**kw)

    def __str__(self):
        return _('you are not authorised to access this {0}').format(self.objType)


class ConferenceClosedError(IndicoError):
    """
    """

    def __init__(self, conf, **kw):
        self._conf = kw.pop('conf', None)
        super(ConferenceClosedError, self).__init__(**kw)

    def __str__(self):
        return _('the event has been closed')


class AccessError(AccessControlError):
    """
    """


class KeyAccessError(AccessControlError):
    """
    """


class HostnameResolveError(IndicoError):
    """
    Hostname resolution failed
    """


class ModificationError(AccessControlError):
    """
    """

    def __str__(self):
        return _('you are not authorised to modify this {0}').format(self.objType)


class AdminError(AccessControlError):
    """
    """

    def __str__(self):
        return _('only administrators can access this {0}').format(self.objType)


class WebcastAdminError(AccessControlError):
    """
    """

    def __str__(self):
        return _('only webcast administrators can access this {0}').format(self.objType)


class TimingError(IndicoError):
    """
    Timetable problems
    """


class ParentTimingError(TimingError):
    """
    """


class EntryTimingError(TimingError):
    """
    """


class UserError(IndicoError):
    """
    """

    def __str__(self):
        if self._message:
            return self._message
        else:
            return _('Error creating user')


class NotLoggedError(IndicoError):
    """
    """


class FormValuesError(IndicoError):
    """
    """


class NoReportError(IndicoError):
    """
    """


class NotFoundError(IndicoError):
    """
    """


class PluginError(IndicoError):
    """
    """


class HtmlScriptError(IndicoError):
    """
    """


class HtmlForbiddenTag(IndicoError):
    """
    """


class BadRefererError(IndicoError):
    """
    """
