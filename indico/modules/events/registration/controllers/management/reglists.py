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

import itertools
import json
from uuid import uuid4

from flask import session, request, redirect, jsonify
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.events.registration.controllers.management import RHManageRegFormBase, RHManageRegistrationBase
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormItem
from indico.modules.events.registration.models.registrations import Registration, RegistrationData
from indico.modules.events.registration.models.form_fields import RegistrationFormFieldData
from indico.modules.events.registration.views import WPManageRegistration
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.util import jsonify_data
from MaKaC.common.cache import GenericCache


cache = GenericCache('reglist-config')


def _get_filters_from_request(regform):
    filters = {}
    for field in regform.form_items:
        if field.is_field and field.input_type in {'radio', 'country', 'bool'}:
            options = request.form.getlist('field_{}'.format(field.id))
            if options:
                filters[field.id] = options
    return filters


def _filter_registration(query, filters):
    if not filters:
        return query

    criteria = [db.and_(RegistrationFormFieldData.field_id == field_id,
                        RegistrationData.data.op('#>>')('{}').in_(data_list))
                for field_id, data_list in filters.iteritems()]
    subquery = (RegistrationData.query
                .with_entities(db.func.count(RegistrationData.registration_id))
                .join(RegistrationData.field_data)
                .filter(RegistrationData.registration_id == Registration.id)
                .filter(db.or_(*criteria))
                .correlate(Registration)
                .as_scalar())
    return query.filter(subquery == len(filters))


def _query_registrations(regform, filters):
    query = (Registration.query
             .with_parent(regform)
             .options(joinedload('data').joinedload('field_data').joinedload('field')))
    return _filter_registration(query, filters)


def _get_visible_column_ids(items):
    items = set(items)
    special_cols = {'reg_date', 'state', 'price'}
    return (items - special_cols), (items & special_cols)


class RHRegistrationsListManage(RHManageRegFormBase):
    """List all registrations of a specific registration form of an event"""

    def _process(self):
        session_key = 'reglist_config_{}'.format(self.regform.id)
        report_config_uuid = request.args.get('config')
        if report_config_uuid:
            configuration = cache.get(report_config_uuid)
            if configuration and configuration['regform_id'] == self.regform.id:
                session[session_key] = configuration['data']
                return redirect(url_for('.manage_reglist', self.regform))
        reg_list_config = session.get(session_key, {'items': [], 'filters': {}})
        items_ids, special_items = _get_visible_column_ids(reg_list_config['items'])
        regform_items = RegistrationFormItem.find_all(RegistrationFormItem.id.in_(items_ids))
        registrations = _query_registrations(self.regform, reg_list_config['filters']).all()
        return WPManageRegistration.render_template('management/regform_reglist.html', self.event, regform=self.regform,
                                                    event=self.event, visible_cols_regform_items=regform_items,
                                                    registrations=registrations, special_items=special_items)


class RHRegistrationsListCustomize(RHManageRegFormBase):
    """Filter options and columns to display for a registrations list of an event"""

    def _process_GET(self):
        session_key = 'reglist_config_{}'.format(self.regform.id)
        reg_list_config = session.get(session_key, {'items': [], 'filters': {}})
        filters = set(itertools.chain.from_iterable(reg_list_config['filters'].itervalues()))
        return WPManageRegistration.render_template('management/reglist_filter.html', self.event, regform=self.regform,
                                                    event=self.event, RegistrationFormItemType=RegistrationFormItemType,
                                                    visible_cols_regform_items=reg_list_config['items'],
                                                    filters=filters)

    def _process_POST(self):
        filters = _get_filters_from_request(self.regform)
        session_key = 'reglist_config_{}'.format(self.regform.id)
        visible_regform_items = json.loads(request.values['visible_cols_regform_items'])
        reglist_config = session.setdefault(session_key, {})
        reglist_config['filters'] = filters
        reglist_config['items'] = visible_regform_items
        session.modified = True
        items_ids, special_items = _get_visible_column_ids(visible_regform_items)
        regform_items = RegistrationFormItem.find_all(RegistrationFormItem.id.in_(items_ids))
        registrations = _query_registrations(self.regform, filters).all()
        tpl = get_template_module('events/registration/management/_reglist.html')
        reg_list = tpl.render_registration_list(registrations=registrations, visible_cols_regform_items=regform_items,
                                                special_items=special_items)
        return jsonify_data(registration_list=reg_list)


class RHRegistrationListStaticURL(RHManageRegFormBase):
    """Generate a static URL for the configuration of the registrations list"""

    def _process(self):
        session_key = 'reglist_config_{}'.format(self.regform.id)
        configuration = {
            'regform_id': self.regform.id,
            'data': session.get(session_key)
        }
        url = url_for('.manage_reglist', self.regform, _external=True)
        if configuration:
            uuid = unicode(uuid4())
            url = url_for('.manage_reglist', self.regform, config=uuid, _external=True)
            cache.set(uuid, configuration)
        return jsonify(url=url)


class RHRegistrationDetails(RHManageRegistrationBase):
    """Displays information about a registration"""

    def _process(self):
        return WPManageRegistration.render_template('management/registration_details.html', self.event,
                                                    registration=self.registration)


class RHRegistrationEdit(RHManageRegistrationBase):
    """Edit the submitted information of a registration"""

    def _process(self):
        return WPManageRegistration.render_template('management/registration_modify.html', self.event,
                                                    registration=self.registration)
