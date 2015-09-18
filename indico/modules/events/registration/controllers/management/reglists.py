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

from collections import OrderedDict
from flask import session, request
from sqlalchemy.orm import contains_eager

from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormItem
from indico.modules.events.registration.models.registrations import Registration, RegistrationData
from indico.modules.events.registration.models.registration_form_fields import (RegistrationFormFieldData,
                                                                                RegistrationFormField)
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.events.registration.util import get_user_info
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data

# TODO: Create a better mapping
USER_INFO = OrderedDict([
    ('user_id', _('ID')),
    ('user_surname', _('Surname')),
    ('user_name', _('First name')),
    ('user_email', _('Email')),
    ('user_position', _('Position')),
    ('user_institution', _('Institution')),
    ('user_phone', _('Phone')),
    ('user_city', _('City')),
    ('user_country', _('Country')),
    ('user_address', _('Address')),
    ('user_paid', _('Paid')),
    ('user_payment_id', _('Payment ID')),
    ('user_payment_amount', _('Payment amount'))
])


def _filter_registration(query):
    filters = {}
    for key in request.form.iterkeys():
        field_name = key.split('_')
        if field_name[0] == 'radiogroup':
            filters[int(field_name[1])] = request.form.getlist(key)

    for field_id, data_list in filters.iteritems():
        query = query.filter(
            (RegistrationFormField.id != field_id) | (RegistrationData.data.op('#>>')('{}').in_(data_list))
        )
    return query.filter(RegistrationData.data != None)


def _query_registrations(regform):
    return (Registration.query
                        .with_parent(regform)
                        .join(Registration.data)
                        .join(RegistrationData.field_data)
                        .join(RegistrationFormFieldData.field)
                        .options(contains_eager('data').contains_eager('field_data').contains_eager('field')))


class RHRegistrationsListManage(RHManageRegFormBase):
    """List all registrations of a specific registration form of an event"""

    def _process(self):
        session_key = 'reg_list_columns_{}'.format(self.regform.id)
        visible_columns = session.get(session_key, {'items': [], 'user_info': []})
        regform_items = RegistrationFormItem.find_all(RegistrationFormItem.id.in_(visible_columns['items']))
        registrations = _query_registrations(self.regform).all()
        return WPManageRegistration.render_template('management/regform_reglist.html', self.event, regform=self.regform,
                                                    event=self.event, visible_cols_regform_items=regform_items,
                                                    visible_cols_user_info=visible_columns['user_info'],
                                                    user_info=USER_INFO, get_user_info=get_user_info,
                                                    registrations=registrations)


class RHRegistrationsListCustomize(RHManageRegFormBase):
    """Filter options and columns to display for a registrations list of an event"""

    def _process_GET(self):
        session_key = 'reg_list_columns_{}'.format(self.regform.id)
        visible_columns = session.get(session_key, {'items': [], 'user_info': []})
        return WPManageRegistration.render_template('management/reglist_filter.html', self.event, regform=self.regform,
                                                    event=self.event, RegistrationFormItemType=RegistrationFormItemType,
                                                    visible_cols_regform_items=visible_columns['items'],
                                                    visible_cols_user_info=visible_columns['user_info'],
                                                    user_info=USER_INFO)

    def _process_POST(self):
        session_key = 'reg_list_columns_{}'.format(self.regform.id)
        visible_regform_items = json.loads(request.values['visible_cols_regform_items'])
        visible_user_info = json.loads(request.values['visible_cols_user_info'])
        session.setdefault(session_key, {})
        session[session_key]['items'] = visible_regform_items
        session[session_key]['user_info'] = visible_user_info
        session.modified = True
        regform_items = RegistrationFormItem.find_all(RegistrationFormItem.id.in_(visible_regform_items))
        registrations = _query_registrations(self.regform)
        registrations = _filter_registration(registrations).all()
        tpl = get_template_module('events/registration/management/_reglist.html')
        reg_list = tpl.render_registrations_list(registrations=registrations, visible_cols_regform_items=regform_items,
                                                 visible_cols_user_info=visible_user_info, user_info=USER_INFO,
                                                 get_user_info=get_user_info)
        return jsonify_data(registrations_list=reg_list)
