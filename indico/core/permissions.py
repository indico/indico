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

from __future__ import unicode_literals

from indico.core import signals
from indico.util.caching import memoize_request
from indico.util.i18n import _
from indico.util.signals import named_objects_from_signal


FULL_ACCESS_PERMISSION = '_full_access'
READ_ACCESS_PERMISSION = '_read_access'


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
    #: whether the permission can be set in the permissions widget (protection page)
    user_selectable = False


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


def get_permissions_info(_type):
    """Retrieve the permissions that can be set in the protection page and related information
    :param _type: The type of the permissions retrieved (e.g. Event, Category)
    :return: A tuple containing a dict with the available permissions and a dict with the permissions tree
    """
    from indico.modules.events import Event
    from indico.modules.events.contributions import Contribution
    from indico.modules.events.sessions import Session

    description_mapping = {
        FULL_ACCESS_PERMISSION: {
            Event: _('Unrestricted management access for the whole event'),
            Session: _('Unrestricted management access for the selected session'),
            Contribution: _('Unrestricted management access for the selected contribution')
        },
        READ_ACCESS_PERMISSION: {
            Event: _('Access the public areas of the event'),
            Session: _('Access the public areas of the selected session'),
            Contribution: _('Access the public areas of the selected contribution')
        }
    }

    selectable_permissions = {k: v for k, v in get_available_permissions(_type).viewitems() if v.user_selectable}
    special_permissions = {
        FULL_ACCESS_PERMISSION: {'title': _('Manage'), 'css_class': 'danger',
                                 'description': description_mapping[FULL_ACCESS_PERMISSION][_type]},
        READ_ACCESS_PERMISSION: {'title': _('Access'), 'css_class': 'accept',
                                 'description': description_mapping[READ_ACCESS_PERMISSION][_type]}
    }
    permissions_tree = {
        FULL_ACCESS_PERMISSION: {
            'title': special_permissions[FULL_ACCESS_PERMISSION]['title'],
            'description': special_permissions[FULL_ACCESS_PERMISSION]['description'],
            'children': {
                perm.name: {'title': perm.friendly_name, 'description': perm.description}
                for name, perm in selectable_permissions.viewitems()
            }
        },
        READ_ACCESS_PERMISSION: {
            'title': special_permissions[READ_ACCESS_PERMISSION]['title'],
            'description': special_permissions[READ_ACCESS_PERMISSION]['description']
        }
    }
    available_permissions = dict({k: {
        'title': v.friendly_name,
        'css_class': 'permission-{}-{}'.format(_type.__name__.lower(), v.name),
        'description': v.description
    } for k, v in selectable_permissions.viewitems()}, **special_permissions)
    return available_permissions, permissions_tree


def get_principal_permissions(principal, _type):
    """Retrieve a set containing the valid permissions of a principal."""
    permissions = set()
    if principal.full_access:
        permissions.add(FULL_ACCESS_PERMISSION)
    if principal.read_access:
        permissions.add(READ_ACCESS_PERMISSION)
    available_permissions = get_permissions_info(_type)[0]
    return permissions | (set(principal.permissions) & set(available_permissions))
