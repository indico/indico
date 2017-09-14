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

from __future__ import unicode_literals

from indico.core import signals
from indico.util.caching import memoize_request
from indico.util.signals import named_objects_from_signal


class ManagementPermission(object):
    """Base class for management permissions.

    To create a new permission, subclass this class and register
    it using the `acl.get_management_permissions` signal.
    ManagementPermission classes are never instatiated.
    """

    #: unique name of the permission - must be all-lowercase
    name = None
    #: displayed name of the permission (shown to users)
    friendly_name = None
    #: description of the permission (optional)
    description = None


@memoize_request
def get_available_permissions(type_):
    """Gets a dict containing all permissions for a given object type"""
    return named_objects_from_signal(signals.acl.get_management_permissions.send(type_))


def check_permissions(type_):
    """
    Retrieves the permissions for an object type and ensures they are
    defined properly.

    This function should be executed from a function connected to the
    `app_created` signal to avoid failures related to invalid permission
    definitions later at runtime.
    """
    permissions = get_available_permissions(type_)
    if not all(x.islower() for x in permissions):
        raise RuntimeError('Management permissions must be all-lowercase')
