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

import os
import uuid
from io import BytesIO
from operator import attrgetter

from flask import flash, jsonify, redirect, render_template, request, session
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import Forbidden, NotFound

from indico.core import signals
from indico.core.config import Config
from indico.core.db import db
from indico.core.errors import FormValuesError, UserValueError
from indico.core.notifications import make_email, send_email
from indico.legacy.common.cache import GenericCache
from indico.legacy.pdfinterface.conference import RegistrantsListToBookPDF, RegistrantsListToPDF
from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.designer.util import get_all_templates
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.payment.models.transactions import TransactionAction
from indico.modules.events.payment.util import register_transaction
from indico.modules.events.registration import logger
from indico.modules.events.registration.badges import RegistrantsListToBadgesPDF
from indico.modules.events.registration.controllers import RegistrationEditMixin
from indico.modules.events.registration.controllers.management import (RHManageRegFormBase, RHManageRegFormsBase,
                                                                       RHManageRegistrationBase)
from indico.modules.events.registration.forms import (BadgeSettingsForm, CreateMultipleRegistrationsForm,
                                                      EmailRegistrantsForm)
from indico.modules.events.registration.models.items import PersonalDataType, RegistrationFormItemType
from indico.modules.events.registration.models.registrations import Registration, RegistrationData
from indico.modules.events.registration.notifications import notify_registration_state_update
from indico.modules.events.registration.settings import event_badge_settings
from indico.modules.events.registration.util import (create_registration, generate_spreadsheet_from_registrations,
                                                     get_event_section_data, get_title_uuid, make_registration_form)
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.events.util import ZipGeneratorMixin
from indico.modules.users import User
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.util.placeholders import replace_placeholders
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file, url_for
from indico.web.util import jsonify_data, jsonify_template


badge_cache = GenericCache('badge-printing')


def _render_registration_details(registration):
    event = registration.registration_form.event_new
    tpl = get_template_module('events/registration/management/_registration_details.html')
    return tpl.render_registration_details(registration=registration, payment_enabled=event.has_feature('payment'))


class RHRegistrationsListManage(RHManageRegFormBase):
    """List all registrations of a specific registration form of an event"""

    def _process(self):
        if self.list_generator.static_link_used:
            return redirect(self.list_generator.get_list_url())
        reg_list_kwargs = self.list_generator.get_list_kwargs()
        return WPManageRegistration.render_template('management/regform_reglist.html', self.event_new,
                                                    regform=self.regform, **reg_list_kwargs)


class RHRegistrationsListCustomize(RHManageRegFormBase):
    """Filter options and columns to display for a registrations list of an event"""

    ALLOW_LOCKED = True

    def _process_GET(self):
        reg_list_config = self.list_generator._get_config()
        return WPManageRegistration.render_template('management/reglist_filter.html', self.event_new,
                                                    regform=self.regform,
                                                    RegistrationFormItemType=RegistrationFormItemType,
                                                    visible_items=reg_list_config['items'],
                                                    static_items=self.list_generator.static_items,
                                                    filters=reg_list_config['filters'])

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(**self.list_generator.render_list())


class RHRegistrationListStaticURL(RHManageRegFormBase):
    """Generate a static URL for the configuration of the registrations list"""

    ALLOW_LOCKED = True

    def _process(self):
        return jsonify(url=self.list_generator.generate_static_url())


class RHRegistrationDetails(RHManageRegistrationBase):
    """Displays information about a registration"""

    def _process(self):
        registration_details_html = _render_registration_details(self.registration)
        return WPManageRegistration.render_template('management/registration_details.html', self.event_new,
                                                    registration=self.registration,
                                                    registration_details_html=registration_details_html)


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
                                 RegistrationData.filename.isnot(None))
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
        self.registrations = (Registration.query.with_parent(self.regform)
                              .filter(Registration.id.in_(ids),
                                      ~Registration.is_deleted)
                              .order_by(*Registration.order_by_name)
                              .all())


class RHRegistrationEmailRegistrantsPreview(RHRegistrationsActionBase):
    """Previews the email that will be sent to registrants"""

    def _process(self):
        if not self.registrations:
            raise UserValueError(_("The selected registrants have been removed."))
        registration = self.registrations[0]
        email_body = replace_placeholders('registration-email', request.form['body'], regform=self.regform,
                                          registration=registration)
        tpl = get_template_module('events/registration/emails/custom_email.html', email_subject=request.form['subject'],
                                  email_body=email_body)
        html = render_template('events/registration/management/email_preview.html', subject=tpl.get_subject(),
                               body=tpl.get_body())
        return jsonify(html=html)


class RHRegistrationEmailRegistrants(RHRegistrationsActionBase):
    """Send email to selected registrants"""

    def _checkParams(self, params):
        self._doNotSanitizeFields.append('from_address')
        RHRegistrationsActionBase._checkParams(self, params)

    def _send_emails(self, form):
        for registration in self.registrations:
            email_body = replace_placeholders('registration-email', form.body.data, regform=self.regform,
                                              registration=registration)
            template = get_template_module('events/registration/emails/custom_email.html',
                                           email_subject=form.subject.data, email_body=email_body)
            bcc = [session.user.email] if form.copy_for_sender.data else []
            email = make_email(to_list=registration.email, cc_list=form.cc_addresses.data, bcc_list=bcc,
                               from_address=form.from_address.data, template=template, html=True)
            send_email(email, self.event_new, 'Registration')

    def _process(self):
        tpl = get_template_module('events/registration/emails/custom_email_default.html')
        default_body = tpl.get_html_body()
        registration_ids = request.form.getlist('registration_id')
        form = EmailRegistrantsForm(body=default_body, regform=self.regform, registration_id=registration_ids,
                                    recipients=[x.email for x in self.registrations])
        if form.validate_on_submit():
            self._send_emails(form)
            num_emails_sent = len(self.registrations)
            flash(ngettext("The email was sent.",
                           "{num} emails were sent.", num_emails_sent).format(num=num_emails_sent), 'success')
            return jsonify_data()
        return jsonify_template('events/registration/management/email.html', form=form, regform=self.regform)


class RHRegistrationDelete(RHRegistrationsActionBase):
    """Delete selected registrations"""

    def _process(self):
        for registration in self.registrations:
            registration.is_deleted = True
            signals.event.registration_deleted.send(registration)
            logger.info('Registration %s deleted by %s', registration, session.user)
            self.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Registration',
                               'Registration deleted: {}'.format(registration.full_name),
                               session.user, data={'Email': registration.email})
        num_reg_deleted = len(self.registrations)
        flash(ngettext("Registration was deleted.",
                       "{num} registrations were deleted.", num_reg_deleted).format(num=num_reg_deleted), 'success')
        return jsonify_data()


class RHRegistrationCreate(RHManageRegFormBase):
    """Create new registration (management area)"""

    def _get_user_data(self):
        user_id = request.args.get('user')
        if user_id is None:
            return {}
        elif user_id.isdigit():
            # existing indico user
            user = User.find_first(id=user_id, is_deleted=False)
            user_data = {t.name: getattr(user, t.name, None) if user else '' for t in PersonalDataType}
        else:
            # non-indico user
            data = GenericCache('pending_identities').get(user_id, {})
            user_data = {t.name: data.get(t.name) for t in PersonalDataType}
        user_data['title'] = get_title_uuid(self.regform, user_data['title'])
        return user_data

    def _process(self):
        form = make_registration_form(self.regform, management=True)()
        if form.validate_on_submit():
            data = form.data
            session['registration_notify_user_default'] = notify_user = data.pop('notify_user', False)
            create_registration(self.regform, data, management=True, notify_user=notify_user)
            flash(_("The registration was created."), 'success')
            return redirect(url_for('.manage_reglist', self.regform))
        elif form.is_submitted():
            # not very pretty but usually this never happens thanks to client-side validation
            for error in form.error_list:
                flash(error, 'error')
        return WPManageRegistration.render_template('display/regform_display.html', self.event_new,
                                                    sections=get_event_section_data(self.regform), regform=self.regform,
                                                    post_url=url_for('.create_registration', self.regform),
                                                    user_data=self._get_user_data(), management=True)


class RHRegistrationCreateMultiple(RHManageRegFormBase):
    """Create multiple registrations for Indico users (management area)"""

    def _register_user(self, user, notify):
        # Fill only the personal data fields, custom fields are left empty.
        data = {pdt.name: getattr(user, pdt.name, None) for pdt in PersonalDataType}
        data['title'] = get_title_uuid(self.regform, data['title'])
        with db.session.no_autoflush:
            create_registration(self.regform, data, management=True, notify_user=notify)

    def _process(self):
        form = CreateMultipleRegistrationsForm(regform=self.regform, open_add_user_dialog=(request.method == 'GET'),
                                               notify_users=session.get('registration_notify_user_default', True))

        if form.validate_on_submit():
            session['registration_notify_user_default'] = form.notify_users.data
            for user in form.user_principals.data:
                self._register_user(user, form.notify_users.data)
            return jsonify_data(**self.list_generator.render_list())

        return jsonify_template('events/registration/management/registration_create_multiple.html', form=form)


class RHRegistrationsExportBase(RHRegistrationsActionBase):
    """Base class for all registration list export RHs"""

    ALLOW_LOCKED = True

    def _checkParams(self, params):
        RHRegistrationsActionBase._checkParams(self, params)
        self.export_config = self.list_generator.get_list_export_config()


class RHRegistrationsExportPDFTable(RHRegistrationsExportBase):
    """Export registration list to a PDF in table style"""

    def _process(self):
        pdf = RegistrantsListToPDF(self._conf, reglist=self.registrations, display=self.export_config['regform_items'],
                                   static_items=self.export_config['static_item_ids'])
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
        pdf = RegistrantsListToBookPDF(self._conf, reglist=self.registrations,
                                       display=self.export_config['regform_items'],
                                       static_items=self.export_config['static_item_ids'])
        return send_file('RegistrantsBook.pdf', BytesIO(pdf.getPDFBin()), 'PDF')


class RHRegistrationsExportCSV(RHRegistrationsExportBase):
    """Export registration list to a CSV file"""

    def _process(self):
        headers, rows = generate_spreadsheet_from_registrations(self.registrations, self.export_config['regform_items'],
                                                                self.export_config['static_item_ids'])
        return send_csv('registrations.csv', headers, rows)


class RHRegistrationsExportExcel(RHRegistrationsExportBase):
    """Export registration list to an XLSX file"""

    def _process(self):
        headers, rows = generate_spreadsheet_from_registrations(self.registrations, self.export_config['regform_items'],
                                                                self.export_config['static_item_ids'])
        return send_xlsx('registrations.xlsx', headers, rows, tz=self.event_new.tzinfo)


class RHRegistrationsPrintBadges(RHRegistrationsActionBase):
    ALLOW_LOCKED = True
    normalize_url_spec = {
        'locators': {
            lambda self: self.regform
        },
        'preserved_args': {'uuid', 'template_id'}
    }

    def _checkParams(self, params):
        RHRegistrationsActionBase._checkParams(self, params)
        self.template = DesignerTemplate.get_one(request.view_args['template_id'])

    def _checkProtection(self):
        RHRegistrationsActionBase._checkProtection(self)

        # Check that template belongs to this event or a category that
        # is a parent
        if self.template.owner != self.event_new and self.template.owner.id not in self.event_new.category_chain:
            raise Forbidden

    def _process(self):
        config_params = badge_cache.get(request.view_args['uuid'])
        if not config_params:
            raise NotFound

        registration_ids = config_params.pop('registration_ids')
        pdf = RegistrantsListToBadgesPDF(self.template, config_params, self.event_new, registration_ids)
        return send_file('Badges-{}.pdf'.format(self.event_new.id), pdf.get_pdf(), 'PDF')


class RHRegistrationsConfigBadges(RHRegistrationsActionBase):
    """Print badges for the selected registrations"""

    ALLOW_LOCKED = True

    def _checkParams(self, params):
        RHManageRegFormBase._checkParams(self, params)
        ids = set(request.form.getlist('registration_id'))
        self.registrations = (Registration.query.with_parent(self.regform)
                              .filter(Registration.id.in_(ids),
                                      ~Registration.is_deleted)
                              .order_by(*Registration.order_by_name)
                              .all()) if ids else []
        self.template_id = request.args.get('template_id')

    def _process(self):
        badge_templates = sorted((tpl for tpl in get_all_templates(self.event_new) if tpl.type.name == 'badge'),
                                 key=attrgetter('title'))
        settings = event_badge_settings.get_all(self.event_new.id)
        form = BadgeSettingsForm(self.event_new, template=self.template_id, **settings)
        registrations = self.registrations or self.regform.registrations
        if self.event_new.is_locked:
            del form.save_values

        if form.validate_on_submit():
            data = form.data
            data.pop('submitted', None)
            template_id = data.pop('template')
            if data.pop('save_values', False):
                event_badge_settings.set_multi(self.event_new, data)
            data['registration_ids'] = [x.id for x in registrations]

            key = unicode(uuid.uuid4())
            badge_cache.set(key, data, time=1800)
            download_url = url_for('.registrations_print_badges', self.regform, template_id=template_id, uuid=key)
            return jsonify_data(flash=False, redirect=download_url, redirect_no_loading=True)
        return jsonify_template('events/registration/management/print_badges.html', event=self.event_new,
                                regform=self.regform, settings_form=form, templates=badge_templates,
                                registrations=registrations)


class RHRegistrationTogglePayment(RHManageRegistrationBase):
    """Modify the payment status of a registration"""

    def _process(self):
        pay = request.form.get('pay') == '1'
        if pay != self.registration.is_paid:
            currency = self.registration.currency if pay else self.registration.transaction.currency
            amount = self.registration.price if pay else self.registration.transaction.amount
            action = TransactionAction.complete if pay else TransactionAction.cancel
            register_transaction(registration=self.registration,
                                 amount=amount,
                                 currency=currency,
                                 action=action,
                                 data={'changed_by_name': session.user.full_name,
                                       'changed_by_id': session.user.id})
        return jsonify_data(html=_render_registration_details(self.registration))


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
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationReject(RHManageRegistrationBase):
    """Reject a registration"""

    def _process(self):
        _modify_registration_status(self.registration, approve=False)
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationCheckIn(RHManageRegistrationBase):
    """Set checked in state of a registration"""

    def _process_PUT(self):
        self.registration.checked_in = True
        return jsonify_data(html=_render_registration_details(self.registration))

    def _process_DELETE(self):
        self.registration.checked_in = False
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationBulkCheckIn(RHRegistrationsActionBase):
    """Bulk apply check-in/not checked-in state to registrations"""

    def _process(self):
        check_in = request.form['check_in'] == '1'
        msg = 'checked-in' if check_in else 'not checked-in'
        for registration in self.registrations:
            registration.checked_in = check_in
            logger.info('Registration %s marked as %s by %s', registration, msg, session.user)
        flash(_("Selected registrations marked as {} successfully.").format(msg), 'success')
        return jsonify_data(**self.list_generator.render_list())


class RHRegistrationsModifyStatus(RHRegistrationsActionBase):
    """Accept/Reject selected registrations"""

    def _process(self):
        approve = request.form['approve'] == '1'
        for registration in self.registrations:
            _modify_registration_status(registration, approve)
        flash(_("The status of the selected registrations was updated successfully."), 'success')
        return jsonify_data(**self.list_generator.render_list())


class RHRegistrationsExportAttachments(RHRegistrationsExportBase, ZipGeneratorMixin):
    """Export registration attachments in a zip file"""

    def _prepare_folder_structure(self, attachment):
        registration = attachment.registration
        regform_title = secure_filename(attachment.registration.registration_form.title, 'registration_form')
        registrant_name = secure_filename("{}_{}".format(registration.get_full_name(),
                                          unicode(registration.friendly_id)), registration.friendly_id)
        file_name = secure_filename("{}_{}_{}".format(attachment.field_data.field.title, attachment.field_data.field_id,
                                                      attachment.filename), attachment.filename)
        return os.path.join(*self._adjust_path_length([regform_title, registrant_name, file_name]))

    def _iter_items(self, attachments):
        for reg_attachments in attachments.itervalues():
            for reg_attachment in reg_attachments:
                yield reg_attachment

    def _process(self):
        attachments = {}
        file_fields = [item for item in self.regform.form_items if item.input_type == 'file']
        for registration in self.registrations:
            data = registration.data_by_field
            attachments_for_registration = [data.get(file_field.id) for file_field in file_fields
                                            if data.get(file_field.id) and data.get(file_field.id).storage_file_id]
            if attachments_for_registration:
                attachments[registration.id] = attachments_for_registration
        return self._generate_zip_file(attachments, name_prefix='attachments', name_suffix=self.regform.id)
