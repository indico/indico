# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
    #: whether the permission is the default (set when an ACL entry is created)
    default = False
    #: the color that will be associated with the permission on the UI
    color = None


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
    if len(list(x for x in permissions.viewvalues() if x.default)) > 1:
        raise RuntimeError('Only one permission can be the default')


def get_permissions_info(_type):
    """Retrieve the permissions that can be set in the protection page and related information
    :param _type: The type of the permissions retrieved (e.g. Event, Category)
    :return: A tuple containing a dict with the available permissions and a dict with the permissions tree
    """
    from indico.modules.events import Event
    from indico.modules.categories import Category
    from indico.modules.events.contributions import Contribution
    from indico.modules.events.sessions import Session
    from indico.modules.rb.models.rooms import Room
    from indico.modules.events.tracks import Track

    description_mapping = {
        FULL_ACCESS_PERMISSION: {
            Event: _('Unrestricted management access for the whole event'),
            Session: _('Unrestricted management access for the selected session'),
            Contribution: _('Unrestricted management access for the selected contribution'),
            Room: _('Full management access over the room'),
            Category: _('Unrestricted management access for this category and all its subcategories/events'),
            Track: None
        },
        READ_ACCESS_PERMISSION: {
            Event: _('Access the public areas of the event'),
            Session: _('Access the public areas of the selected session'),
            Contribution: _('Access the public areas of the selected contribution'),
            Room: None,
            Category: _('View the category and its events'),
            Track: None
        }
    }

    selectable_permissions = {k: v for k, v in get_available_permissions(_type).viewitems() if v.user_selectable}
    special_permissions = {
        FULL_ACCESS_PERMISSION: {
            'title': _('Manage'),
            'color': 'red',
            'css_class': 'permission-full-access',
            'description': description_mapping[FULL_ACCESS_PERMISSION][_type],
            'default': False
        },
        READ_ACCESS_PERMISSION: {
            'title': _('Access'),
            'color': 'teal',
            'css_class': 'permission-read-access',
            'description': description_mapping[READ_ACCESS_PERMISSION][_type],
            'default': False
        }
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
        'description': v.description,
        'default': v.default,
        'color': v.color,
    } for k, v in selectable_permissions.viewitems()}, **special_permissions)
    default = next((k for k, v in available_permissions.viewitems() if v['default']), None)

    return available_permissions, permissions_tree, default


def get_principal_permissions(principal, _type):
    """Retrieve a set containing the valid permissions of a principal."""
    permissions = set()
    if principal.full_access:
        permissions.add(FULL_ACCESS_PERMISSION)
    if principal.read_access:
        permissions.add(READ_ACCESS_PERMISSION)
    available_permissions = get_permissions_info(_type)[0]
    return permissions | (set(principal.permissions) & set(available_permissions))


def get_unified_permissions(principal, all_permissions=False):
    """Convert principal's permissions into a list including read and full access.

    :param principal: A `User`, `GroupProxy`, `EmailPrincipal` or `EventRole` instance
    :param all_permissions: Whether to include all permissions, even if principal has full access
    """
    if not all_permissions and principal.full_access:
        return {FULL_ACCESS_PERMISSION}
    perms = set(principal.permissions)
    if principal.full_access:
        perms.add(FULL_ACCESS_PERMISSION)
    if principal.read_access:
        perms.add(READ_ACCESS_PERMISSION)
    return perms


def get_split_permissions(permissions):
    """Split a list of permissions into a `has_full_access, has_read_access, list_with_others` tuple."""
    full_access_permission = FULL_ACCESS_PERMISSION in permissions
    read_access_permission = READ_ACCESS_PERMISSION in permissions
    other_permissions = permissions - {FULL_ACCESS_PERMISSION, READ_ACCESS_PERMISSION}
    return full_access_permission, read_access_permission, other_permissions


def update_permissions(obj, form):
    """Update the permissions of an object, based on the corresponding WTForm."""
    from indico.util.user import principal_from_fossil
    from indico.modules.categories import Category
    from indico.modules.events import Event

    event = category = None
    if isinstance(obj, Category):
        category = obj
    elif isinstance(obj, Event):
        event = obj
    else:
        event = obj.event
        category = event.category

    current_principal_permissions = {p.principal: get_principal_permissions(p, type(obj))
                                     for p in obj.acl_entries}
    current_principal_permissions = {k: v for k, v in current_principal_permissions.iteritems() if v}
    new_principal_permissions = {
        principal_from_fossil(
            fossil,
            allow_emails=True,
            allow_networks=True,
            allow_pending=True,
            allow_registration_forms=True,
            event=event,
            category=category,
        ): set(permissions)
        for fossil, permissions in form.permissions.data
    }
    update_principals_permissions(obj, current_principal_permissions, new_principal_permissions)


def update_principals_permissions(obj, current, new):
    """Handle the updates of permissions and creations/deletions of acl principals.

    :param obj: The object to update. Must have ``acl_entries``
    :param current: A dict mapping principals to a set with its current permissions
    :param new: A dict mapping principals to a set with its new permissions
    """
    user_selectable_permissions = {v.name for k, v in get_available_permissions(type(obj)).viewitems()
                                   if v.user_selectable}
    for principal, permissions in current.viewitems():
        if principal not in new:
            permissions_kwargs = {
                'full_access': False,
                'read_access': False,
                'del_permissions': user_selectable_permissions
            }
            obj.update_principal(principal, **permissions_kwargs)
        elif permissions != new[principal]:
            full_access, read_access, permissions = get_split_permissions(new[principal])
            all_user_permissions = [set(entry.permissions) for entry in obj.acl_entries
                                    if entry.principal == principal][0]
            permissions_kwargs = {
                'full_access': full_access,
                'read_access': read_access,
                'permissions': (all_user_permissions - user_selectable_permissions) | permissions
            }
            obj.update_principal(principal, **permissions_kwargs)
    new_principals = set(new) - set(current)
    for p in new_principals:
        full_access, read_access, permissions = get_split_permissions(new[p])
        permissions_kwargs = {
            'full_access': full_access,
            'read_access': read_access,
            'add_permissions': permissions & user_selectable_permissions
        }
        obj.update_principal(p, **permissions_kwargs)
