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

from flask import session, request, redirect, jsonify, flash, render_template
from sqlalchemy.orm import joinedload, undefer

from indico.core.config import Config
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
from indico.modules.events.registration.util import (get_event_section_data, make_registration_form,
                                                     create_registration, generate_csv_from_registrations)
from indico.modules.payment import event_settings as payment_event_settings
from indico.modules.payment.models.transactions import TransactionAction
from indico.modules.payment.util import register_transaction
from indico.util.i18n import _, ngettext
from indico.util.placeholders import replace_placeholders
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for, send_file
from indico.web.util import jsonify_data, jsonify_template
from MaKaC.common.cache import GenericCache
from indico.core.errors import FormValuesError
from MaKaC.PDFinterface.conference import RegistrantsListToPDF, RegistrantsListToBookPDF


cache = GenericCache('reglist-config')


def _get_filters_from_request(regform):
    filters = {}
    for field in regform.form_items:
        if field.is_field and field.input_type in {'single_choice', 'multi_choice', 'country', 'bool', 'checkbox'}:
            options = request.form.getlist('field_{}'.format(field.id))
            if options:
                filters[field.id] = options
    return filters


def _filter_registration(regform, query, filters):
    if not filters:
        return query

    field_types = {f.id: f.field_impl for f in regform.form_items if not f.is_deleted and f.is_field}
    criteria = [db.and_(RegistrationFormFieldData.field_id == field_id,
                        field_types[field_id].create_sql_filter(data_list))
                for field_id, data_list in filters.iteritems()]
    subquery = (RegistrationData.query
                .with_entities(db.func.count(RegistrationData.registration_id))
                .join(RegistrationData.field_data)
                .filter(RegistrationData.registration_id == Registration.id)
                .filter(db.or_(*criteria))
                .correlate(Registration)
                .as_scalar())
    return query.filter(subquery == len(filters))


def _query_registrations(regform):
    return (Registration.query
            .with_parent(regform)
            .filter(~Registration.is_deleted)
            .options(joinedload('data').joinedload('field_data').joinedload('field')))


def _get_visible_column_ids(items):
    items = set(items)
    special_cols = {'reg_date', 'state', 'price'}
    return (items - special_cols), (items & special_cols)


def _get_reg_list_config(regform):
    session_key = 'reglist_config_{}'.format(regform.id)
    report_config_uuid = request.args.get('config')
    if report_config_uuid:
        configuration = cache.get(report_config_uuid)
        if configuration and configuration['regform_id'] == regform.id:
            session[session_key] = configuration['data']
    return session.get(session_key, {'items': [], 'filters': {}})


class RHRegistrationsListManage(RHManageRegFormBase):
    """List all registrations of a specific registration form of an event"""

    def _process(self):
        reg_list_config = _get_reg_list_config(regform=self.regform)
        if 'config' in request.args:
            return redirect(url_for('.manage_reglist', self.regform))
        items_ids, special_items = _get_visible_column_ids(reg_list_config['items'])
        regform_items = RegistrationFormItem.find_all(RegistrationFormItem.id.in_(items_ids),
                                                      ~RegistrationFormItem.is_deleted)
        registrations_query = _query_registrations(self.regform)
        total_regs = registrations_query.count()
        registrations = _filter_registration(self.regform, registrations_query, reg_list_config['filters']).all()
        return WPManageRegistration.render_template('management/regform_reglist.html', self.event, regform=self.regform,
                                                    event=self.event, visible_cols_regform_items=regform_items,
                                                    registrations=registrations, special_items=special_items,
                                                    total_registrations=total_regs)


class RHRegistrationsListCustomize(RHManageRegFormBase):
    """Filter options and columns to display for a registrations list of an event"""

    def _process_GET(self):
        reg_list_config = _get_reg_list_config(self.regform)
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
        regform_items = RegistrationFormItem.find_all(RegistrationFormItem.id.in_(items_ids),
                                                      ~RegistrationFormItem.is_deleted)
        registrations_query = _query_registrations(self.regform)
        total_regs = registrations_query.count()
        registrations = _filter_registration(self.regform, registrations_query, filters).all()
        tpl = get_template_module('events/registration/management/_reglist.html')
        reg_list = tpl.render_registration_list(registrations=registrations, visible_cols_regform_items=regform_items,
                                                special_items=special_items, total_registrations=total_regs)
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
                                                    registration=self.registration,
                                                    payment_enabled=payment_event_settings.get(self.event, 'enabled'),
                                                    from_management=True)


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


class RHRegistrationsActionBase(RHManageRegFormBase):
    """Base class for classes performing actions on registrations"""

    def _checkParams(self, params):
        RHManageRegFormBase._checkParams(self, params)
        ids = set(request.form.getlist('registration_id'))
        self.registrations = (Registration
                              .find(Registration.id.in_(ids), ~Registration.is_deleted)
                              .with_parent(self.regform)
                              .all())


class RHRegistrationEmailRegistrants(RHRegistrationsActionBase):
    """Send email to selected registrants"""

    def _checkParams(self, params):
        self._doNotSanitizeFields.append('from_address')
        RHRegistrationsActionBase._checkParams(self, params)

    def _send_emails(self, form):
        for registration in self.registrations:
            email_body = replace_placeholders('registration-email', form.body.data, registration=registration)
            template = get_template_module('events/registration/emails/custom_email.html',
                                           email_subject=form.subject.data, email_body=email_body)
            email = make_email(to_list=registration.email, cc_list=form.cc_addresses.data,
                               from_address=form.from_address.data, template=template, html=True)
            send_email(email, self.event, 'Registration')

    def _process(self):
        tpl = get_template_module('events/registration/emails/custom_email_default.html', event=self.event)
        default_body = tpl.get_html_body()
        form = EmailRegistrantsForm(body=default_body)
        if form.validate_on_submit():
            self._send_emails(form)
            num_emails_sent = len(self.registrations)
            flash(ngettext("The email was sent.",
                           "{num} emails were sent.", num_emails_sent).format(num=num_emails_sent), 'success')
            return jsonify_data()
        return jsonify_template('events/registration/management/email.html', form=form)


class RHRegistrationDelete(RHRegistrationsActionBase):
    """Delete selected registrations"""

    def _process(self):
        for registration in self.registrations:
            registration.is_deleted = True
            logger.info('Registration {} deleted by {}'.format(registration, session.user))
            # TODO: Signal for deletion?
        num_reg_deleted = len(self.registrations)
        flash(ngettext("Registration was deleted.",
                       "{num} registrations were deleted.", num_reg_deleted).format(num=num_reg_deleted), 'success')
        return jsonify_data()


class RHRegistrationCreate(RHManageRegFormBase):
    """Create new registration (management area)"""

    def _process(self):
        form = make_registration_form(self.regform)()
        if form.validate_on_submit():
            create_registration(self.regform, form.data)
            flash(_("The registration was created."), 'success')
            return redirect(url_for('.manage_reglist', self.regform))
        elif form.is_submitted():
            # not very pretty but usually this never happens thanks to client-side validation
            for error in form.error_list:
                flash(error, 'error')
        return WPManageRegistration.render_template('display/regform_display.html', self.event, event=self.event,
                                                    sections=get_event_section_data(self.regform), regform=self.regform,
                                                    currency=payment_event_settings.get(self.event, 'currency'),
                                                    post_url=url_for('.create_registration', self.regform),
                                                    user_data={})


class RHRegistrationsExportBase(RHRegistrationsActionBase):
    """Base class for all registration list export RHs"""

    def _checkParams(self, params):
        RHRegistrationsActionBase._checkParams(self, params)
        reg_list_config = _get_reg_list_config(self.regform)
        self.items_ids, self.special_items = _get_visible_column_ids(reg_list_config['items'])
        self.regform_items = RegistrationFormItem.find_all(RegistrationFormItem.id.in_(self.items_ids),
                                                           ~RegistrationFormItem.is_deleted)


class RHRegistrationsExportPDFTable(RHRegistrationsExportBase):
    """Export registration list to a PDF in table style"""

    def _process(self):
        pdf = RegistrantsListToPDF(self.event, reglist=self.registrations, display=self.regform_items,
                                   special_items=self.special_items)
        try:
            data = pdf.getPDFBin()
        except Exception:
            if Config.getInstance().getDebug():
                raise
            raise FormValuesError(_("Text too large to generate a PDF with table style. "
                                    "Please try again generating with book style."))
        return send_file('RegistrantsList.pdf', BytesIO(data), 'PDF')


class RHRegistrationsExportPDFBook(RHRegistrationsExportBase):
    """Export registration list to a PDF in book style"""

    def _process(self):
        pdf = RegistrantsListToBookPDF(self.event, reglist=self.registrations, display=self.regform_items,
                                       special_items=self.special_items)
        return send_file('RegistrantsBook.pdf', BytesIO(pdf.getPDFBin()), 'PDF')


class RHRegistrationsExportCSV(RHRegistrationsExportBase):
    """Export registration list to a CSV file"""

    def _process(self):
        csv_file = generate_csv_from_registrations(self.registrations, self.regform_items, self.special_items)
        return send_file('registrations.csv', csv_file, 'text/csv')


class RHRegistrationTogglePayment(RHManageRegistrationBase):
    """Modify the payment status of a registration"""

    def _process(self):
        payment_completed = request.form.get('payment_status') == '1'
        currency = payment_event_settings.get(self.registration.registration_form.event, 'currency')
        action = TransactionAction.complete if not payment_completed else TransactionAction.cancel
        register_transaction(registrant=self.registration,
                             amount=self.registration.price,
                             currency=currency,
                             action=action,
                             provider='_manual',
                             data={'changed_by_name': session.user.full_name,
                                   'changed_by_id': session.user.id})
        flash(_("The registration payment was updated successfully."), 'success')
        return jsonify_template('events/registration/management/registration_details.html',
                                registration=self.registration,
                                payment_enabled=payment_event_settings.get(self.event, 'enabled'))
