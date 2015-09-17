# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import json

from flask import session, request

from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormItem
from indico.modules.events.registration.views import WPManageRegistration
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data


class RHRegistrationsListManage(RHManageRegFormBase):
    """List all registrations of a specific registration form of an event"""

    def _process(self):
        visible_columns = session.get('reg_list_columns', {'items': []})
        visible_reg_items = RegistrationFormItem.find_all(RegistrationFormItem.id.in_(visible_columns['items']))
        return WPManageRegistration.render_template('management/regform_reglist.html', self.event, regform=self.regform,
                                                    event=self.event, visible_reg_items=visible_reg_items)


class RHRegistrationsListCustomize(RHManageRegFormBase):
    """Filter options and columns to display for a registrations list of an event"""

    def _process_GET(self):
        visible_columns = session.get('reg_list_columns', {'items': []})
        return WPManageRegistration.render_template('management/reglist_filter.html', self.event, regform=self.regform,
                                                    event=self.event, RegistrationFormItemType=RegistrationFormItemType,
                                                    visible_columns=visible_columns)

    def _process_POST(self):
        visible_columns = json.loads(request.values['visible_columns'])
        if not session.get('reg_list_columns'):
            session['reg_list_columns'] = {}
        session['reg_list_columns']['items'] = visible_columns.get('items', [])
        session.modified = True
        visible_reg_items = RegistrationFormItem.find_all(RegistrationFormItem.id.in_(visible_columns.get('items', [])))
        tpl = get_template_module('events/registration/management/_reglist.html')
        registrations_list = tpl.render_registrations_list(regform=self.regform, visible_reg_items=visible_reg_items)
        return jsonify_data(registrations_list=registrations_list)
