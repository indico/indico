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


class ManagementRole(object):
    """Base class for management roles.

    To create a new role, subclass this class and register
    it using the `acl.get_management_roles` signal.
    ManagementRole classes are never instatiated.
    """

    #: unique name of the role - must be all-lowercase
    name = None
    #: displayed name of the role (shown to users)
    friendly_name = None
    #: description of the role (optional)
    description = None


@memoize_request
def get_available_roles(type_):
    """Gets a dict containing all roles for a given object type"""
    return named_objects_from_signal(signals.acl.get_management_roles.send(type_))


def check_roles(type_):
    """
    Retrieves the roles for an object type and ensures they are
    defined properly.

    This function should be executed from a function connected to the
    `app_created` signal to avoid failures related to invalid role
    definitions later at runtime.
    """
    roles = get_available_roles(type_)
    if not all(x.islower() for x in roles):
        raise RuntimeError('Management roles must be all-lowercase')
