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

from flask import request, session
from sqlalchemy.orm import contains_eager

from indico.core.db import db
from indico.modules.admin import RHAdminBase
from indico.modules.categories.models.categories import Category
from indico.modules.events.models.events import Event
from indico.modules.networks import logger
from indico.modules.networks.forms import IPNetworkGroupForm
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.modules.networks.views import WPNetworksAdmin
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHNetworkBase(RHAdminBase):
    pass


class RHManageNetworks(RHNetworkBase):
    """Management list for IPNetworks"""

    def _process(self):
        network_groups = IPNetworkGroup.find().order_by(IPNetworkGroup.name).all()
        return WPNetworksAdmin.render_template('networks.html', network_groups=network_groups)


class RHCreateNetworkGroup(RHNetworkBase):
    """Dialog to create an IPNetworkGroup"""

    def _process(self):
        form = IPNetworkGroupForm()
        if form.validate_on_submit():
            network_group = IPNetworkGroup()
            form.populate_obj(network_group)
            db.session.add(network_group)
            db.session.flush()
            logger.info('Network group %s created by %s', network_group, session.user)
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHAdminNetworkGroupBase(RHNetworkBase):
    """Base class for managing in IPNetworkGroup"""

    def _checkParams(self):
        self.network_group = IPNetworkGroup.get_one(request.view_args['network_group_id'])


class RHEditNetworkGroup(RHAdminNetworkGroupBase):
    """Dialog to edit an IPNetworkGroup"""

    def _process(self):
        form = IPNetworkGroupForm(obj=self.network_group)
        if form.validate_on_submit():
            form.populate_obj(self.network_group)
            logger.info('Network group %s edited by %s', self.network_group, session.user)
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHDeleteNetworkGroup(RHAdminNetworkGroupBase):
    """Dialog to delete an IPNetworkGroup"""

    def _process_GET(self):
        query = (self.network_group.in_event_acls
                 .join(Event)
                 .options(contains_eager('event_new'))
                 .order_by(Event.title))
        events = [principal.event_new for principal in query]
        query = (self.network_group.in_category_acls
                 .join(Category)
                 .order_by(Category.title)
                 .options(contains_eager('category')))
        categories = [principal.category for principal in query]
        return jsonify_template('networks/delete_network.html', network_group=self.network_group, categories=categories,
                                events=events)

    def _process_POST(self):
        db.session.delete(self.network_group)
        logger.info('Network group %s deleted by %s', self.network_group, session.user)
        return jsonify_data(flash=False)
