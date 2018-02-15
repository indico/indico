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

import random

from flask import request, session
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.models.roles import EventRole
from indico.modules.events.roles import logger
from indico.modules.events.roles.forms import RoleForm
from indico.modules.events.roles.util import get_role_colors, serialize_role
from indico.modules.events.roles.views import WPEventRoles
from indico.modules.users import User
from indico.util.user import principal_from_fossil
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data, jsonify_form


def _get_roles(event):
    return (EventRole.query.with_parent(event)
            .options(joinedload('members'))
            .all())


def _render_roles(event):
    tpl = get_template_module('events/roles/_roles.html')
    return tpl.render_roles(_get_roles(event))


def _render_role(role, collapsed=True):
    tpl = get_template_module('events/roles/_roles.html')
    return tpl.render_role(role, collapsed=collapsed)


class RHEventRoles(RHManageEventBase):
    """Event role management"""

    def _process(self):
        return WPEventRoles.render_template('roles.html', self.event, roles=_get_roles(self.event))


class RHAddEventRole(RHManageEventBase):
    """Add a new event role"""

    def _process(self):
        form = RoleForm(event=self.event, color=self._get_color())
        if form.validate_on_submit():
            role = EventRole(event=self.event)
            form.populate_obj(role)
            db.session.flush()
            logger.info('Event role %r created by %r', role, session.user)
            self.event.log(EventLogRealm.management, EventLogKind.positive, 'Roles',
                           'Added role: "{}"'.format(role.name), session.user)
            return jsonify_data(html=_render_roles(self.event), role=serialize_role(role))
        return jsonify_form(form)

    def _get_color(self):
        used_colors = {role.color for role in self.event.roles}
        unused_colors = set(get_role_colors()) - used_colors
        return random.choice(tuple(unused_colors) or get_role_colors())


class RHManageEventRole(RHManageEventBase):
    """Base class to manage a specific event role"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.role
        }
    }

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.role = EventRole.get_one(request.view_args['role_id'])


class RHEditEventRole(RHManageEventRole):
    """Edit an event role"""

    def _process(self):
        form = RoleForm(obj=self.role, event=self.event)
        if form.validate_on_submit():
            form.populate_obj(self.role)
            db.session.flush()
            logger.info('Event role %r updated by %r', self.role, session.user)
            self.event.log(EventLogRealm.management, EventLogKind.change, 'Roles',
                           'Updated role: "{}"'.format(self.role.name), session.user)
            return jsonify_data(html=_render_role(self.role))
        return jsonify_form(form)


class RHDeleteEventRole(RHManageEventRole):
    """Delete an event role"""

    def _process(self):
        db.session.delete(self.role)
        logger.info('Event role %r deleted by %r', self.role, session.user)
        self.event.log(EventLogRealm.management, EventLogKind.negative, 'Roles',
                       'Deleted role: "{}"'.format(self.role.name), session.user)
        return jsonify_data(html=_render_roles(self.event))


class RHRemoveEventRoleMember(RHManageEventRole):
    """Remove a user from an event role"""

    normalize_url_spec = dict(RHManageEventRole.normalize_url_spec, preserved_args={'user_id'})

    def _process_args(self):
        RHManageEventRole._process_args(self)
        self.user = User.get_one(request.view_args['user_id'])

    def _process(self):
        if self.user in self.role.members:
            self.role.members.remove(self.user)
            logger.info('User %r removed from role %r by %r', self.user, self.role, session.user)
            self.event.log(EventLogRealm.management, EventLogKind.negative, 'Roles',
                           'Removed user from role "{}"'.format(self.role.name), session.user,
                           data={'Name': self.user.full_name,
                                 'Email': self.user.email})
        return jsonify_data(html=_render_role(self.role, collapsed=False))


class RHAddEventRoleMembers(RHManageEventRole):
    """Add users to an event role"""

    def _process(self):
        for data in request.json['users']:
            user = principal_from_fossil(data, allow_pending=True, allow_groups=False)
            if user not in self.role.members:
                self.role.members.add(user)
                logger.info('User %r added to role %r by %r', user, self.role, session.user)
                self.event.log(EventLogRealm.management, EventLogKind.positive, 'Roles',
                               'Added user to role "{}"'.format(self.role.name), session.user,
                               data={'Name': user.full_name,
                                     'Email': user.email})
        return jsonify_data(html=_render_role(self.role, collapsed=False))
