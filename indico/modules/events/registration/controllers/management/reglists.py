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
from copy import deepcopy
from io import BytesIO
from uuid import uuid4

from flask import session, request, redirect, jsonify, flash
from sqlalchemy.orm import joinedload

from indico.core.config import Config
from indico.core.db import db

from indico.core import signals
from indico.core.errors import FormValuesError
from indico.core.notifications import make_email, send_email
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers import RegistrationEditMixin
from indico.modules.events.registration.controllers.management import (RHManageRegFormBase, RHManageRegistrationBase,
                                                                       RHManageRegFormsBase)
from indico.modules.events.registration.forms import EmailRegistrantsForm
from indico.modules.events.registration.models.items import (RegistrationFormItemType, RegistrationFormItem,
                                                             PersonalDataType)
from indico.modules.events.registration.models.registrations import Registration, RegistrationData
from indico.modules.events.registration.models.form_fields import (RegistrationFormFieldData,
                                                                   RegistrationFormPersonalDataField)
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.modules.events.registration.notifications import notify_registration_state_update
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.events.registration.util import (get_event_section_data, make_registration_form,
                                                     create_registration, generate_csv_from_registrations)
from indico.modules.payment import event_settings as payment_event_settings
from indico.modules.payment.models.transactions import TransactionAction
from indico.modules.payment.util import register_transaction
from indico.modules.users import User
from indico.util.i18n import _, ngettext
from indico.util.placeholders import replace_placeholders
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for, send_file
from indico.web.util import jsonify_data, jsonify_template
from MaKaC.common.cache import GenericCache
from MaKaC.PDFinterface.conference import RegistrantsListToPDF, RegistrantsListToBookPDF
from MaKaC.webinterface.pages.conferences import WConfModifBadgePDFOptions

PERSONAL_COLUMNS = ('title', 'email', 'first_name', 'last_name', 'affiliation', 'address', 'phone', 'column')
SPECIAL_COLUMNS = ('reg_date', 'price', 'state', 'checked_in', 'checked_in_date')

SPECIAL_COLUMN_LABELS = {
    'reg_date': {
        'title': _('Registation Date'),
        'id': 'reg_date'
    },
    'price': {
        'title': _('Price'),
        'id': 'price'
    },
    'state': {
        'title': _('Status'),
        'id': 'state'
    },
    'checked_in': {
        'title': _('Checked in'),
        'id': 'checked_in',
        'filter_choices': {
            '0': _('No'),
            '1': _('Yes')
        }
    },
    'checked_in_date': {
        'title': _('Checked in date'),
        'id': 'checked_in_date'
    }
}

DEFAULT_REPORT_CONFIG = {
    'items': ('title', 'email', 'affiliation') + SPECIAL_COLUMNS,
    'filters': {'fields': {}, 'items': {}}
}


cache = GenericCache('reglist-config')


def _get_filters_from_request(regform):
    filters = deepcopy(DEFAULT_REPORT_CONFIG['filters'])
    for field in regform.form_items:
        if field.is_field and field.input_type in {'single_choice', 'multi_choice', 'country', 'bool', 'checkbox'}:
            options = request.form.getlist('field_{}'.format(field.id))
            if options:
                filters['fields'][field.id] = options
    for item in SPECIAL_COLUMN_LABELS.itervalues():
        if item.get('filter_choices'):
            options = request.form.getlist('field_{}'.format(item['id']))
            if options:
                filters['items'][item['id']] = options
    return filters


def _filter_registration(regform, query, filters):
    # if not filters:
    if not filters['fields'] and not filters['items']:
        return query

    field_types = {f.id: f.field_impl for f in regform.form_items if not f.is_deleted and f.is_field}
    criteria = [db.and_(RegistrationFormFieldData.field_id == field_id,
                        field_types[field_id].create_sql_filter(data_list))
                for field_id, data_list in filters['fields'].iteritems()]

    items_criteria = []
    if 'checked_in' in filters['items']:
        checked_in_values = filters['items']['checked_in']
        # If both values 'true' and 'false' are selected, there's no point in filtering
        if len(checked_in_values) == 1:
            items_criteria.append(Registration.checked_in == bool(int(checked_in_values[0])))
    if filters['fields']:
        subquery = (RegistrationData.query
                    .with_entities(db.func.count(RegistrationData.registration_id))
                    .join(RegistrationData.field_data)
                    .filter(RegistrationData.registration_id == Registration.id)
                    .filter(db.or_(*criteria))
                    .correlate(Registration)
                    .as_scalar())
        query = query.filter(subquery == len(filters['fields']))
    return query.filter(db.or_(*items_criteria))


def _query_registrations(regform):
    return (Registration.query
            .with_parent(regform)
            .filter(~Registration.is_deleted)
            .options(joinedload('data').joinedload('field_data').joinedload('field'))
            .order_by(db.func.lower(Registration.last_name), db.func.lower(Registration.first_name)))


def _split_column_ids(items):
    """Split column ids between custom and 'basic' (personal + special)."""
    special_cols = [item for item in items if isinstance(item, basestring)]
    return [item for item in items if item not in special_cols], list(special_cols)


def _split_special_ids(items):
    """Split column ids between 'DB-stored' (custom + personal) and special."""
    special = []
    normal = []

    for item in items:
        if item in SPECIAL_COLUMNS:
            special.append(item)
        else:
            normal.append(item)
    return normal, special


def _get_basic_columns(form, ids):
    """
    Retrieve information needed for the header of "basic" columns (personal + special).

    Returns a list of ``{'id': ..., 'caption': ...}`` dictionaries.
    """
    result = []
    for item_id in PERSONAL_COLUMNS:
        if item_id in ids:
            field = RegistrationFormItem.find_one(registration_form=form,
                                                  personal_data_type=PersonalDataType[item_id])
            result.append({
                'id': field.id,
                'caption': field.title
            })

    for item_id in SPECIAL_COLUMNS:
        if item_id in ids:
            result.append({
                'id': item_id,
                'caption': SPECIAL_COLUMN_LABELS[item_id]['title']
            })
    return result


def _column_ids_to_db(form, ids):
    """Translate string-based ids to DB-based RegistrationFormItem ids."""
    result = []
    for item_id in ids:
        if isinstance(item_id, basestring):
            personal_data = PersonalDataType.get(item_id)
            if personal_data:
                result.append(RegistrationFormPersonalDataField.find_one(registration_form=form,
                                                                         personal_data_type=personal_data).id)
            else:
                result.append(item_id)
        else:
            result.append(item_id)
    return result


def _get_reg_list_config(regform):
    session_key = 'reglist_config_{}'.format(regform.id)
    report_config_uuid = request.args.get('config')
    if report_config_uuid:
        configuration = cache.get(report_config_uuid)
        if configuration and configuration['regform_id'] == regform.id:
            session[session_key] = configuration['data']
    return session.get(session_key, DEFAULT_REPORT_CONFIG)


def _render_registration_list(regform, registrations, total_registrations=None):
    reg_list_config = _get_reg_list_config(regform=regform)
    item_ids, basic_item_ids = _split_column_ids(reg_list_config['items'])
    basic_columns = _get_basic_columns(regform, basic_item_ids)
    regform_items = RegistrationFormItem.find_all(RegistrationFormItem.id.in_(item_ids),
                                                  ~RegistrationFormItem.is_deleted)
    tpl = get_template_module('events/registration/management/_reglist.html')
    reglist = tpl.render_registration_list(registrations=registrations, visible_cols_regform_items=regform_items,
                                           basic_columns=basic_columns, total_registrations=total_registrations)
    return reglist


class RHRegistrationsListManage(RHManageRegFormBase):
    """List all registrations of a specific registration form of an event"""

    def _process(self):
        reg_list_config = _get_reg_list_config(regform=self.regform)
        if 'config' in request.args:
            return redirect(url_for('.manage_reglist', self.regform))

        item_ids, basic_item_ids = _split_column_ids(reg_list_config['items'])
        basic_columns = _get_basic_columns(self.regform, basic_item_ids)
        regform_items = RegistrationFormItem.find_all(RegistrationFormItem.id.in_(item_ids),
                                                      ~RegistrationFormItem.is_deleted)
        registrations_query = _query_registrations(self.regform)
        total_regs = registrations_query.count()
        registrations = _filter_registration(self.regform, registrations_query, reg_list_config['filters']).all()
        return WPManageRegistration.render_template('management/regform_reglist.html', self.event, regform=self.regform,
                                                    event=self.event, visible_cols_regform_items=regform_items,
                                                    registrations=registrations, basic_columns=basic_columns,
                                                    total_registrations=total_regs,
                                                    filtering_enabled=total_regs != len(registrations))


class RHRegistrationsListCustomize(RHManageRegFormBase):
    """Filter options and columns to display for a registrations list of an event"""

    def _process_GET(self):
        reg_list_config = _get_reg_list_config(self.regform)
        visible_columns = reg_list_config['items']

        return WPManageRegistration.render_template('management/reglist_filter.html', self.event, regform=self.regform,
                                                    event=self.event, RegistrationFormItemType=RegistrationFormItemType,
                                                    visible_cols_regform_items=visible_columns,
                                                    filters=reg_list_config['filters'],
                                                    special_items=SPECIAL_COLUMN_LABELS)

    def _process_POST(self):
        filters = _get_filters_from_request(self.regform)
        session_key = 'reglist_config_{}'.format(self.regform.id)
        visible_regform_items = json.loads(request.values['visible_cols_regform_items'])

        reglist_config = session.setdefault(session_key, {})
        reglist_config['filters'] = filters
        reglist_config['items'] = visible_regform_items

        session.modified = True
        registrations_query = _query_registrations(self.regform)
        total_regs = registrations_query.count()
        registrations = _filter_registration(self.regform, registrations_query, filters).all()

        return jsonify_data(registration_list=_render_registration_list(self.regform, registrations, total_regs),
                            filtering_enabled=total_regs != len(registrations))


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
                                                    currency=payment_event_settings.get(self.event, 'currency'),
                                                    payment_enabled=self.event.has_feature('payment'),
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
                                 RegistrationData.filename != None)  # noqa
                           .options(joinedload('registration').joinedload('registration_form'))
                           .one())

    def _process(self):
        return self.field_data.send()


class RHRegistrationEdit(RegistrationEditMixin, RHManageRegistrationBase):
    """Edit the submitted information of a registration."""

    view_class = WPManageRegistration
    template_file = 'management/registration_modify.html'
    management = True

    normalize_url_spec = {
        'locators': {
            lambda self: self.registration
        }
    }

    @property
    def success_url(self):
        return url_for('.registration_details', self.registration)


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
            signals.event.registration_deleted.send(registration)
            logger.info('Registration %s deleted by %s', registration, session.user)
        num_reg_deleted = len(self.registrations)
        flash(ngettext("Registration was deleted.",
                       "{num} registrations were deleted.", num_reg_deleted).format(num=num_reg_deleted), 'success')
        return jsonify_data()


class RHRegistrationCreate(RHManageRegFormBase):
    """Create new registration (management area)"""

    def _checkParams(self, params):
        RHManageRegFormBase._checkParams(self, params)
        user_id = request.args.get('user')
        self.user = User.find_first(User.id == user_id, ~User.is_deleted) if user_id else None

    def _process(self):
        form = make_registration_form(self.regform)()
        if form.validate_on_submit():
            create_registration(self.regform, form.data, management=True)
            flash(_("The registration was created."), 'success')
            return redirect(url_for('.manage_reglist', self.regform))
        elif form.is_submitted():
            # not very pretty but usually this never happens thanks to client-side validation
            for error in form.error_list:
                flash(error, 'error')
        user_data = {t.name: getattr(self.user, t.name, None) if self.user else '' for t in PersonalDataType}
        return WPManageRegistration.render_template('display/regform_display.html', self.event, event=self.event,
                                                    sections=get_event_section_data(self.regform), regform=self.regform,
                                                    currency=payment_event_settings.get(self.event, 'currency'),
                                                    post_url=url_for('.create_registration', self.regform),
                                                    user_data=user_data, management=True)


class RHRegistrationsExportBase(RHRegistrationsActionBase):
    """Base class for all registration list export RHs"""

    def _checkParams(self, params):
        RHRegistrationsActionBase._checkParams(self, params)
        reg_list_config = _get_reg_list_config(self.regform)
        item_ids, self.special_item_ids = _split_special_ids(reg_list_config['items'])
        self.item_ids = _column_ids_to_db(self.regform, item_ids)

        self.regform_items = RegistrationFormItem.find(RegistrationFormItem.id.in_(self.item_ids),
                                                       ~RegistrationFormItem.is_deleted).with_parent(
                                                           self.regform).all()


class RHRegistrationsExportPDFTable(RHRegistrationsExportBase):
    """Export registration list to a PDF in table style"""

    def _process(self):
        pdf = RegistrantsListToPDF(self.event, reglist=self.registrations, display=self.regform_items,
                                   special_items=self.special_item_ids)
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
                                       special_items=self.special_item_ids)
        return send_file('RegistrantsBook.pdf', BytesIO(pdf.getPDFBin()), 'PDF')


class RHRegistrationsExportCSV(RHRegistrationsExportBase):
    """Export registration list to a CSV file"""

    def _process(self):
        csv_file = generate_csv_from_registrations(self.registrations, self.regform_items, self.special_item_ids)
        return send_file('registrations.csv', csv_file, 'text/csv')


class RHRegistrationsPrintBadges(RHRegistrationsActionBase):
    """Print badges for the selected registrations"""

    def _process(self):
        badge_templates = self.event.getBadgeTemplateManager().getTemplates().items()
        badge_templates.sort(key=lambda x: x[1].getName())
        pdf_options = WConfModifBadgePDFOptions(self.event).getHTML()
        badge_design_url = url_for('event_mgmt.confModifTools-badgePrinting', self.event)
        create_pdf_url = url_for('event_mgmt.confModifTools-badgePrintingPDF', self.event)

        return WPManageRegistration.render_template('management/print_badges.html', self.event, regform=self.regform,
                                                    templates=badge_templates, pdf_options=pdf_options,
                                                    registrations=self.registrations,
                                                    registration_ids=[x.id for x in self.registrations],
                                                    badge_design_url=badge_design_url, create_pdf_url=create_pdf_url)


class RHRegistrationTogglePayment(RHManageRegistrationBase):
    """Modify the payment status of a registration"""

    def _process(self):
        pay = request.form.get('pay') == '1'
        can_be_paid = pay and self.registration.state == RegistrationState.unpaid
        can_be_unpaid = not pay and self.registration.state == RegistrationState.complete and self.registration.price
        if can_be_paid or can_be_unpaid:
            event = self.registration.registration_form.event
            currency = payment_event_settings.get(event, 'currency') if pay else self.registration.transaction.currency
            amount = self.registration.price if pay else self.registration.transaction.amount
            action = TransactionAction.complete if pay else TransactionAction.cancel
            register_transaction(registration=self.registration,
                                 amount=amount,
                                 currency=currency,
                                 action=action,
                                 data={'changed_by_name': session.user.full_name,
                                       'changed_by_id': session.user.id})
            flash(_("The registration payment was updated successfully."), 'success')
        return jsonify_template('events/registration/management/registration_details.html',
                                registration=self.registration,
                                payment_enabled=self.event.has_feature('payment'))


def _modify_registration_status(registration, approve):
    if approve:
        registration.update_state(approved=True)
    else:
        registration.update_state(rejected=True)
    db.session.flush()
    notify_registration_state_update(registration)
    status = 'approved' if approve else 'rejected'
    logger.info('Registration %s was %s by %s', registration, status, session.user)


class RHRegistrationApprove(RHManageRegistrationBase):
    """Accept a registration"""

    def _process(self):
        _modify_registration_status(self.registration, approve=True)
        flash(_("The registration status was updated successfully."), 'success')
        return redirect(url_for('.manage_reglist', self.regform))


class RHRegistrationReject(RHManageRegistrationBase):
    """Reject a registration"""

    def _process(self):
        _modify_registration_status(self.registration, approve=False)
        flash(_("The registration was rejected successfully."), 'success')
        return redirect(url_for('.manage_reglist', self.regform))


class RHRegistrationsModifyStatus(RHRegistrationsActionBase):
    """Accept/Reject selected registrations"""

    def _process(self):
        approve = request.form['approve'] == '1'
        for registration in self.registrations:
            _modify_registration_status(registration, approve)
        flash(_("The status of the selected registrations was updated successfully."), 'success')
        registrations = _query_registrations(self.regform).all()
        return jsonify_data(registration_list=_render_registration_list(self.regform, registrations=registrations))
