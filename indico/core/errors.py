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

"""
Module containing the Indico exception class hierarchy
"""

from werkzeug.exceptions import BadRequest, Forbidden, HTTPException, NotFound

from indico.util.i18n import _
from indico.util.string import to_unicode


def get_error_description(exception):
    """Gets a user-friendy description for an exception

    This overrides some HTTPException messages to be more suitable
    for end-users.
    """
    try:
        description = exception.description
    except AttributeError:
        return to_unicode(exception.message)
    if isinstance(exception, Forbidden) and description == Forbidden.description:
        return _(u"You are not allowed to access this page.")
    elif isinstance(exception, NotFound) and description == NotFound.description:
        return _(u"The page you are looking for doesn't exist.")
    elif isinstance(exception, BadRequest) and description == BadRequest.description:
        return _(u"The request was invalid or contained invalid arguments.")
    else:
        return to_unicode(description)


class IndicoError(Exception):
    pass


class NoReportError(IndicoError):
    @classmethod
    def wrap_exc(cls, exc):
        assert isinstance(exc, HTTPException)
        exc._disallow_report = True
        return exc


class UserValueError(NoReportError):
    """Error to indicate that the user entered invalid data.

    This behaves basically like NoReportError but it comes with
    a 400 status code instead of the usual 500 code.
    """
    http_status_code = 400
