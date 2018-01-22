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

from flask import flash, redirect, request
from werkzeug.exceptions import NotFound

from indico.core.db.sqlalchemy.protection import ProtectionMode, render_acl
from indico.core.permissions import (FULL_ACCESS_PERMISSION, READ_ACCESS_PERMISSION, get_available_permissions,
                                     get_permissions_info)
from indico.modules.events import Event
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.management.forms import EventProtectionForm
from indico.modules.events.management.views import WPEventProtection
from indico.modules.events.operations import update_event_protection
from indico.modules.events.sessions import COORDINATOR_PRIV_SETTINGS, session_settings
from indico.modules.events.sessions.operations import update_session_coordinator_privs
from indico.modules.events.util import get_object_from_args
from indico.util import json
from indico.util.i18n import _
from indico.util.user import principal_from_fossil
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.forms.fields.principals import serialize_principal
from indico.web.util import jsonify_template


class RHShowNonInheriting(RHManageEventBase):
    """Show a list of non-inheriting child objects"""

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.obj = get_object_from_args()[2]
        if self.obj is None:
            raise NotFound

    def _process(self):
        objects = self.obj.get_non_inheriting_objects()
        return jsonify_template('events/management/non_inheriting_objects.html', objects=objects)


class RHEventACL(RHManageEventBase):
    """Display the inherited ACL of the event"""

    def _process(self):
        return render_acl(self.event)


class RHEventACLMessage(RHManageEventBase):
    """Render the inheriting ACL message"""

    def _process(self):
        mode = ProtectionMode[request.args['mode']]
        return jsonify_template('forms/protection_field_acl_message.html', object=self.event, mode=mode,
                                endpoint='event_management.acl')


class RHEventProtection(RHManageEventBase):
    """Show event protection"""

    NOT_SANITIZED_FIELDS = {'access_key'}

    def _process(self):
        form = EventProtectionForm(obj=FormDefaults(**self._get_defaults()), event=self.event)
        if form.validate_on_submit():
            current_principal_permissions = {p.principal: self._get_principal_permissions(p)
                                             for p in self.event.acl_entries}
            current_principal_permissions = {k: v for k, v in current_principal_permissions.iteritems() if v}
            new_principal_permissions = {
                principal_from_fossil(fossil, allow_emails=True, allow_networks=True): set(permissions)
                for fossil, permissions in form.permissions.data
            }
            self._update_permissions(current_principal_permissions, new_principal_permissions)

            update_event_protection(self.event, {'protection_mode': form.protection_mode.data,
                                                 'own_no_access_contact': form.own_no_access_contact.data,
                                                 'access_key': form.access_key.data,
                                                 'visibility': form.visibility.data})
            self._update_session_coordinator_privs(form)
            flash(_('Protection settings have been updated'), 'success')
            return redirect(url_for('.protection', self.event))
        return WPEventProtection.render_template('event_protection.html', self.event, 'protection', form=form)

    def _get_defaults(self):
        registration_managers = {p.principal for p in self.event.acl_entries
                                 if p.has_management_permission('registration', explicit=True)}
        event_session_settings = session_settings.get_all(self.event)
        coordinator_privs = {name: event_session_settings[val] for name, val in COORDINATOR_PRIV_SETTINGS.iteritems()
                             if event_session_settings.get(val)}
        permissions = [[serialize_principal(p.principal), list(self._get_principal_permissions(p))]
                       for p in self.event.acl_entries]
        permissions = [item for item in permissions if item[1]]

        return dict({'protection_mode': self.event.protection_mode, 'registration_managers': registration_managers,
                     'access_key': self.event.access_key, 'visibility': self.event.visibility,
                     'own_no_access_contact': self.event.own_no_access_contact, 'permissions': permissions},
                    **coordinator_privs)

    def _update_session_coordinator_privs(self, form):
        data = {field: getattr(form, field).data for field in form.priv_fields}
        update_session_coordinator_privs(self.event, data)

    def _get_principal_permissions(self, principal):
        """Retrieve a set containing the valid permissions of a principal."""
        permissions = set()
        if principal.full_access:
            permissions.add(FULL_ACCESS_PERMISSION)
        if principal.read_access:
            permissions.add(READ_ACCESS_PERMISSION)
        available_permissions = get_permissions_info(Event)[0]
        return permissions | (set(principal.permissions) & set(available_permissions))

    def _get_split_permissions(self, permissions):
        full_access_permission = FULL_ACCESS_PERMISSION in permissions
        read_access_permission = READ_ACCESS_PERMISSION in permissions
        other_permissions = permissions - {FULL_ACCESS_PERMISSION, READ_ACCESS_PERMISSION}
        return full_access_permission, read_access_permission, other_permissions

    def _update_permissions(self, current, new):
        """Handle the updates of permissions and creations/deletions of acl principals.
        :param current: A dict mapping principals to a set with its current permissions
        :param new: A dict mapping principals to a set with its new permissions
        """
        user_selectable_permissions = {v.name for k, v in get_available_permissions(Event).viewitems()
                                       if v.user_selectable}
        for principal, permissions in current.viewitems():
            if principal not in new:
                permissions_kwargs = {
                    'full_access': False,
                    'read_access': False,
                    'del_permissions': user_selectable_permissions
                }
                self.event.update_principal(principal, **permissions_kwargs)
            elif permissions != new[principal]:
                full_access, read_access, permissions = self._get_split_permissions(new[principal])
                all_user_permissions = [set(entry.permissions) for entry in self.event.acl_entries
                                        if entry.principal == principal][0]
                permissions_kwargs = {
                    'full_access': full_access,
                    'read_access': read_access,
                    'permissions': (all_user_permissions - user_selectable_permissions) | permissions
                }
                self.event.update_principal(principal, **permissions_kwargs)
        new_principals = set(new) - set(current)
        for p in new_principals:
            full_access, read_access, permissions = self._get_split_permissions(new[p])
            permissions_kwargs = {
                'full_access': full_access,
                'read_access': read_access,
                'add_permissions': permissions & user_selectable_permissions
            }
            self.event.update_principal(p, **permissions_kwargs)


class RHEventPermissionsDialog(RHManageEventBase):
    def _process(self):
        principal = json.loads(request.form['principal'])
        permissions_tree = get_permissions_info(Event)[1]
        return jsonify_template('events/management/event_permissions_dialog.html', permissions_tree=permissions_tree,
                                permissions=request.form.getlist('permissions'), principal=principal)
