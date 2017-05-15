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
Module containing the legacy indico exception class hierarchy
"""

from indico.legacy.common.fossilize import fossilizes, Fossilizable
from indico.core.fossils.errors import IErrorReportFossil, IErrorNoReportFossil
from indico.util.translations import ensure_str


class MaKaCError(Exception, Fossilizable):

    fossilizes(IErrorReportFossil)

    def __init__(self, msg="", area="", explanation=None):
        self._msg = self.message = msg
        self._area = area
        self._explanation = explanation

    def getMessage(self):
        return self._msg

    @ensure_str
    def __str__(self):
        if self._area != "":
            return "%s - %s" % (self._area, self._msg)
        else:
            return self._msg

    def getArea(self):
        return self._area

    def getExplanation(self):
        """
        Some extra information, like actions that can be taken
        """

        return self._explanation


class AccessControlError(MaKaCError):
    """
    """

    fossilizes(IErrorNoReportFossil)

    def __init__(self, objectType="object"):
        MaKaCError.__init__(self)
        self.objType = objectType

    @ensure_str
    def __str__(self):
        return _("you are not authorised to access this %s") % self.objType

    def getMessage(self):
        return str(self)


class AccessError(AccessControlError):
    """
    """
    pass


class KeyAccessError(AccessControlError):
    """
    """
    pass


class ModificationError(AccessControlError):
    """
    """

    @ensure_str
    def __str__(self):
        return _("you are not authorised to modify this %s") % self.objType


class NotLoggedError(MaKaCError):
    """
    """
    fossilizes(IErrorNoReportFossil)


class NoReportError(MaKaCError):
    """
    """
    fossilizes(IErrorNoReportFossil)


class NotFoundError(MaKaCError):
    """
    Legacy indico's own NotFound version (just for legacy support)
    """
    fossilizes(IErrorNoReportFossil)

    def __init__(self, message, title=""):
        if not title:
            title = message
            message = ''
        super(NotFoundError, self).__init__(title, explanation=message)


class HtmlForbiddenTag(NoReportError):
    pass


class BadRefererError(MaKaCError):
    pass
