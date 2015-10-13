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
from io import BytesIO
from uuid import uuid4

from flask import session, request, redirect, jsonify, flash
from sqlalchemy.orm import joinedload, undefer

from indico.core.db import db
from indico.core.notifications import make_email, send_email
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management import (RHManageRegFormBase, RHManageRegistrationBase,
                                                                       RHManageRegFormsBase)
from indico.modules.events.registration.models.items import RegistrationFormItemType, RegistrationFormItem
from indico.modules.events.registration.models.registrations import Registration, RegistrationData
from indico.modules.events.registration.models.form_fields import RegistrationFormFieldData
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.events.registration.forms import EmailRegistrantsForm
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for, send_file
from indico.web.util import jsonify_data
from MaKaC.common.cache import GenericCache


cache = GenericCache('reglist-config')


def _get_filters_from_request(regform):
    filters = {}
    for field in regform.form_items:
        if field.is_field and field.input_type in {'single_choice', 'country', 'bool', 'checkbox'}:
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
        return WPManageRegistration.render_template('management/reglist_filter.html', self.event, regform=self.regform,
                                                    event=self.event, RegistrationFormItemType=RegistrationFormItemType,
                                                    visible_cols_regform_items=reg_list_config['items'],
                                                    filters=reg_list_config['filters'])

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


class RHRegistrationDownloadAttachment(RHManageRegFormsBase):
    """Download a file attached to a registration"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.field_data.locator.file
        }
    }

    def _checkParams(self, params):
        RHManageRegFormsBase._checkParams(self, params)
        self.field_data = (RegistrationData
                           .find(RegistrationData.registration_id == request.view_args['registration_id'],
                                 RegistrationData.field_data_id == request.view_args['field_data_id'],
                                 RegistrationData.file != None)  # noqa
                           .options(joinedload('registration').joinedload('registration_form'))
                           .options(undefer('file'))
                           .one())

    def _process(self):
        data = self.field_data
        metadata = data.file_metadata
        return send_file(metadata['filename'], BytesIO(data.file), mimetype=metadata['content_type'], conditional=True)


class RHRegistrationEdit(RHManageRegistrationBase):
    """Edit the submitted information of a registration"""

    def _process(self):
        return WPManageRegistration.render_template('management/registration_modify.html', self.event,
                                                    registration=self.registration)


class RHRegistrationEmailRegistrants(RHManageRegFormBase):
    """Send email to selected registrants"""

    def _checkParams(self, params):
        self._doNotSanitizeFields.append('from_address')
        RHManageRegFormBase._checkParams(self, params)

    def _get_people(self):
        ids = set(request.form.getlist('registration_ids'))
        return Registration.find(Registration.id.in_(ids)).with_parent(self.regform).all()

    def _send_emails(self, form):
        people = self._get_people()
        for person in people:
            template = get_template_module('events/registration/emails/custom_email.html',
                                           email_subject=form.subject.data, email_body=form.body.data)
            email = make_email(to_list=person.email, cc_list=form.cc_addresses.data,
                               from_address=form.from_address.data, template=template, html=True)
            send_email(email, self.event, 'Registration')

    def _process(self):
        form = EmailRegistrantsForm()
        if form.validate_on_submit():
            self._send_emails(form)
            flash(_("Emails sent"), 'success')
            return jsonify_data()
        return WPManageRegistration.render_template('management/email.html', form=form)


class RHRegistrationDelete(RHManageRegFormBase):
    """Delete selected registrations"""

    def _process(self):
        ids = set(request.form.getlist('registration_ids'))
        registrations = Registration.find(Registration.id.in_(ids)).with_parent(self.regform).all()
        for registration in registrations:
            registration.is_deleted = True
            logger.info('Registration {} deleted by {}'.format(registration, session.user))
            # TODO: Signal for deletion?
        flashed_messages = flash(_("Registrations \"{ids}\" were deleted").format(ids=",".join(ids)), 'success')
        return jsonify_data(flashed_messages=flashed_messages)
