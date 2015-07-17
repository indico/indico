# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

"""
Module containing the Indico exception class hierarchy
"""

import traceback

from werkzeug.exceptions import Forbidden, NotFound

from indico.util.i18n import _
from indico.util.translations import ensure_str


def get_error_description(exception):
    """Gets a user-friendy description for an exception

    This overrides some HTTPException messages to be more suitable
    for end-users.
    """
    try:
        description = exception.description
    except AttributeError:
        return unicode(exception.message)
    if isinstance(exception, Forbidden) and description == Forbidden.description:
        return _(u"You are not allowed to access this page.")
    elif isinstance(exception, NotFound) and description == NotFound.description:
        return _(u"The page you are looking for doesn't exist.")
    else:
        return unicode(description)


class IndicoError(Exception):

    code = -32000  # json-rpc server specific errors starting code

    def __init__(self, message='', area='', explanation=''):
        self.message = message
        self._area = area
        self._explanation = explanation

    @ensure_str
    def __str__(self):
        if self._area:
            return '{} - {}'.format(self._area, self.message)
        else:
            return self.message

    def getMessage(self):
        return self.message

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
            'type': 'noReport' if isinstance(self, NoReportError) else 'unknown',
            'message': self.getMessage(),
            'data': self.__dict__,
            'requestInfo': {},
            'inner': traceback.format_exc()
        }


class AccessControlError(IndicoError):
    def __init__(self, **kw):
        self._object_type = kw.pop('object_type', 'object')
        super(AccessControlError, self).__init__(**kw)

    @ensure_str
    def __str__(self):
        return _('you are not authorised to access this {0}').format(self._object_type)


class ConferenceClosedError(IndicoError):
    def __init__(self, conf, **kw):
        self._conf = kw.pop('conf', None)
        super(ConferenceClosedError, self).__init__(**kw)

    @ensure_str
    def __str__(self):
        return _('the event has been closed')


class AccessError(AccessControlError):
    pass


class KeyAccessError(AccessControlError):
    pass


class HostnameResolveError(IndicoError):
    """
    Hostname resolution failed
    """


class ModificationError(AccessControlError):
    @ensure_str
    def __str__(self):
        return _('you are not authorised to modify this {0}').format(self._object_type)


class AdminError(AccessControlError):
    @ensure_str
    def __str__(self):
        return _('only administrators can access this {0}').format(self._object_type)


class TimingError(IndicoError):
    """
    Timetable problems
    """


class ParentTimingError(TimingError):
    pass


class EntryTimingError(TimingError):
    pass


class UserError(IndicoError):
    @ensure_str
    def __str__(self):
        if self._message:
            return self._message
        else:
            return _('Error creating user')


class NotLoggedError(IndicoError):
    pass


class FormValuesError(IndicoError):
    pass


class NoReportError(IndicoError):
    pass


class NotFoundError(IndicoError):
    pass


class HtmlScriptError(IndicoError):
    pass


class HtmlForbiddenTag(IndicoError):
    pass


class BadRefererError(IndicoError):
    pass
