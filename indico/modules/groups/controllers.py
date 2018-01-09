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

from operator import attrgetter

from flask import flash, jsonify, redirect, request
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import NotFound

from indico.core.auth import multipass
from indico.core.db import db
from indico.modules.admin import RHAdminBase
from indico.modules.groups import GroupProxy
from indico.modules.groups.forms import EditGroupForm, SearchForm
from indico.modules.groups.models.groups import LocalGroup
from indico.modules.groups.views import WPGroupsAdmin
from indico.modules.users import User
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHGroups(RHAdminBase):
    """Admin group overview"""

    def _process(self):
        query = LocalGroup.query.options(joinedload(LocalGroup.members)).order_by(db.func.lower(LocalGroup.name))
        groups = [g.proxy for g in query]
        providers = [p for p in multipass.identity_providers.itervalues() if p.supports_groups]
        form = SearchForm(obj=FormDefaults(exact=True))
        if not providers:
            del form.provider
        else:
            form.provider.choices = ([('', _('All')), ('indico', _('Local Groups'))] +
                                     [(p.name, p.title) for p in sorted(providers, key=attrgetter('title'))])
        search_results = None
        if form.validate_on_submit():
            search_providers = None if not providers or not form.provider.data else {form.provider.data}
            search_results = GroupProxy.search(form.name.data, exact=form.exact.data, providers=search_providers)
            search_results.sort(key=attrgetter('provider', 'name'))
        provider_titles = {p.name: p.title for p in multipass.identity_providers.itervalues()}
        provider_titles[None] = _('Local')
        return WPGroupsAdmin.render_template('groups.html', groups=groups, providers=providers, form=form,
                                             search_results=search_results, provider_titles=provider_titles)


class RHGroupBase(RHAdminBase):
    def _process_args(self):
        try:
            group = GroupProxy(request.view_args['group_id'], request.view_args['provider'])
        except ValueError:
            group = None
        if group is None or group.group is None:
            raise NotFound
        self.group = group


class RHGroupDetails(RHGroupBase):
    """Admin group details"""

    def _process(self):
        group = self.group
        provider_title = multipass.identity_providers[group.provider].title if not group.is_local else _('Local')
        return WPGroupsAdmin.render_template('group_details.html', group=group, provider_title=provider_title)


class RHGroupMembers(RHGroupBase):
    """Admin group memberlist (json)"""

    def _process(self):
        group = self.group
        tpl = get_template_module('groups/_group_members.html')
        return jsonify(success=True, html=tpl.group_members(group))


class RHGroupEdit(RHAdminBase):
    """Admin group modification/creation"""

    def _process_args(self):
        if 'group_id' in request.view_args:
            self.new_group = False
            self.group = LocalGroup.get(request.view_args['group_id'])
            if self.group is None:
                raise NotFound
        else:
            self.new_group = True
            self.group = LocalGroup()

    def _process(self):
        existing_group = self.group if not self.new_group else None
        form = EditGroupForm(obj=existing_group, group=existing_group)
        if form.validate_on_submit():
            form.populate_obj(self.group)
            if self.new_group:
                db.session.add(self.group)
                msg = _("The group '{name}' has been created.")
            else:
                msg = _("The group '{name}' has been updated.")
            db.session.flush()
            flash(msg.format(name=self.group.name), 'success')
            return redirect(url_for('.groups'))
        return WPGroupsAdmin.render_template('group_edit.html', group=existing_group, form=form)


class RHLocalGroupBase(RHAdminBase):
    def _process_args(self):
        self.group = LocalGroup.get(request.view_args['group_id'])
        if self.group is None:
            raise NotFound


class RHGroupDelete(RHLocalGroupBase):
    """Admin group deletion"""

    def _process(self):
        db.session.delete(self.group)
        flash(_("The group '{name}' has been deleted.").format(name=self.group.name), 'success')
        return redirect(url_for('.groups'))


class RHGroupDeleteMember(RHLocalGroupBase):
    """Admin group member deletion (ajax)"""

    def _process(self):
        self.group.members.discard(User.get(request.view_args['user_id']))
        return jsonify(success=True)
