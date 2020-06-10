# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from operator import attrgetter

from flask import flash, jsonify, redirect, request
from werkzeug.exceptions import NotFound

from indico.core.db.sqlalchemy.protection import ProtectionMode, render_acl
from indico.core.permissions import (get_available_permissions, get_permissions_info, get_principal_permissions,
                                     update_permissions)
from indico.modules.categories.models.roles import CategoryRole
from indico.modules.categories.util import serialize_category_role
from indico.modules.core.controllers import PrincipalsMixin
from indico.modules.events import Event
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.management.forms import EventProtectionForm
from indico.modules.events.management.views import WPEventProtection
from indico.modules.events.operations import update_event_protection
from indico.modules.events.roles.util import serialize_event_role
from indico.modules.events.sessions import COORDINATOR_PRIV_SETTINGS, session_settings
from indico.modules.events.sessions.operations import update_session_coordinator_privs
from indico.modules.events.util import get_object_from_args
from indico.util import json
from indico.util.i18n import _
from indico.util.marshmallow import PrincipalDict
from indico.web.args import use_rh_kwargs
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.forms.fields.principals import PermissionsField, serialize_principal
from indico.web.rh import RH
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

    def _process(self):
        form = EventProtectionForm(obj=FormDefaults(**self._get_defaults()), event=self.event)
        selectable_permissions = {k for k, v in get_available_permissions(Event).viewitems() if v.user_selectable}
        user_permissions = [(p.principal, set(p.permissions)) for p in self.event.acl_entries]
        form.permissions.hidden_permissions = [
            (serialize_principal(principal), sorted(perms))
            for principal, perms in user_permissions
            if perms and not (perms & selectable_permissions)
        ]
        if form.validate_on_submit():
            update_permissions(self.event, form)
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
        permissions = [[serialize_principal(p.principal), list(get_principal_permissions(p, Event))]
                       for p in self.event.acl_entries]
        permissions = [item for item in permissions if item[1]]

        return dict({'protection_mode': self.event.protection_mode, 'registration_managers': registration_managers,
                     'access_key': self.event.access_key, 'visibility': self.event.visibility,
                     'own_no_access_contact': self.event.own_no_access_contact, 'permissions': permissions},
                    **coordinator_privs)

    def _update_session_coordinator_privs(self, form):
        data = {field: getattr(form, field).data for field in form.priv_fields}
        update_session_coordinator_privs(self.event, data)


class RHPermissionsDialog(RH):
    def _process(self):
        principal = json.loads(request.form['principal'])
        permissions_tree = get_permissions_info(PermissionsField.type_mapping[request.view_args['type']])[1]
        return jsonify_template('events/management/permissions_dialog.html', permissions_tree=permissions_tree,
                                permissions=request.form.getlist('permissions'), principal=principal)


class RHEventPrincipals(PrincipalsMixin, RHManageEventBase):
    ALLOW_LOCKED = True
    PERMISSION = 'ANY'

    @use_rh_kwargs({
        'values': PrincipalDict(allow_groups=True, allow_external_users=True, allow_event_roles=True,
                                allow_category_roles=True, missing={})
    }, rh_context=('event',))
    def _process(self, values):
        self.values = values
        return PrincipalsMixin._process(self)


class RHEventRolesJSON(RHManageEventBase):
    PERMISSION = 'ANY'

    def _process(self):
        event_roles = sorted(self.event.roles, key=attrgetter('code'))
        return jsonify([serialize_event_role(er, legacy=False) for er in event_roles])


class RHCategoryRolesJSON(RHManageEventBase):
    PERMISSION = 'ANY'

    def _process(self):
        category_roles = CategoryRole.get_category_roles(self.event.category)
        return jsonify([serialize_category_role(cr, legacy=False) for cr in category_roles])
