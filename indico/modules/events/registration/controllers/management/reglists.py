# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import os
import uuid
from io import BytesIO

from flask import flash, jsonify, redirect, render_template, request, session
from sqlalchemy.orm import joinedload, subqueryload
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.core import signals
from indico.core.config import config
from indico.core.db import db
from indico.core.errors import NoReportError
from indico.core.notifications import make_email, send_email
from indico.legacy.common.cache import GenericCache
from indico.legacy.pdfinterface.conference import RegistrantsListToBookPDF, RegistrantsListToPDF
from indico.modules.designer import PageLayout, TemplateType
from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.designer.util import get_inherited_templates
from indico.modules.events import EventLogKind, EventLogRealm
from indico.modules.events.payment.models.transactions import TransactionAction
from indico.modules.events.payment.util import register_transaction
from indico.modules.events.registration import logger
from indico.modules.events.registration.badges import (RegistrantsListToBadgesPDF,
                                                       RegistrantsListToBadgesPDFDoubleSided,
                                                       RegistrantsListToBadgesPDFFoldable)
from indico.modules.events.registration.controllers import RegistrationEditMixin
from indico.modules.events.registration.controllers.management import (RHManageRegFormBase, RHManageRegFormsBase,
                                                                       RHManageRegistrationBase)
from indico.modules.events.registration.forms import (BadgeSettingsForm, CreateMultipleRegistrationsForm,
                                                      EmailRegistrantsForm, ImportRegistrationsForm,
                                                      RejectRegistrantsForm)
from indico.modules.events.registration.models.items import PersonalDataType, RegistrationFormItemType
from indico.modules.events.registration.models.registrations import Registration, RegistrationData, RegistrationState
from indico.modules.events.registration.notifications import notify_registration_state_update
from indico.modules.events.registration.settings import event_badge_settings
from indico.modules.events.registration.util import (create_registration, generate_spreadsheet_from_registrations,
                                                     get_event_section_data, get_ticket_attachments, get_title_uuid,
                                                     import_registrations_from_csv, make_registration_form)
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.events.util import ZipGeneratorMixin
from indico.modules.users import User
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.util.placeholders import replace_placeholders
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file, url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


badge_cache = GenericCache('badge-printing')


def _render_registration_details(registration):
    event = registration.registration_form.event
    tpl = get_template_module('events/registration/management/_registration_details.html')
    return tpl.render_registration_details(registration=registration, payment_enabled=event.has_feature('payment'))


class RHRegistrationsListManage(RHManageRegFormBase):
    """List all registrations of a specific registration form of an event."""

    def _process(self):
        if self.list_generator.static_link_used:
            return redirect(self.list_generator.get_list_url())
        reg_list_kwargs = self.list_generator.get_list_kwargs()
        badge_templates = [tpl for tpl in set(self.event.designer_templates) | get_inherited_templates(self.event)
                           if tpl.type == TemplateType.badge]
        has_tickets = any(tpl.is_ticket for tpl in badge_templates)
        has_badges = any(not tpl.is_ticket for tpl in badge_templates)
        return WPManageRegistration.render_template('management/regform_reglist.html', self.event,
                                                    has_badges=has_badges, has_tickets=has_tickets, **reg_list_kwargs)


class RHRegistrationsListCustomize(RHManageRegFormBase):
    """Filter options and columns to display for a registrations list of an event."""

    ALLOW_LOCKED = True

    def _process_GET(self):
        reg_list_config = self.list_generator._get_config()
        return jsonify_template('events/registration/management/reglist_filter.html',
                                regform=self.regform,
                                RegistrationFormItemType=RegistrationFormItemType,
                                visible_items=reg_list_config['items'],
                                static_items=self.list_generator.static_items,
                                filters=reg_list_config['filters'])

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(**self.list_generator.render_list())


class RHRegistrationListStaticURL(RHManageRegFormBase):
    """Generate a static URL for the configuration of the registrations list."""

    ALLOW_LOCKED = True

    def _process(self):
        return jsonify(url=self.list_generator.generate_static_url())


class RHRegistrationDetails(RHManageRegistrationBase):
    """Display information about a registration."""

    def _process(self):
        registration_details_html = _render_registration_details(self.registration)
        return WPManageRegistration.render_template('management/registration_details.html', self.event,
                                                    registration=self.registration,
                                                    registration_details_html=registration_details_html)


class RHRegistrationDownloadAttachment(RHManageRegFormsBase):
    """Download a file attached to a registration."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.field_data.locator.file
        }
    }

    def _process_args(self):
        RHManageRegFormsBase._process_args(self)
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
    """Base class for classes performing actions on registrations."""

    registration_query_options = ()

    def _process_args(self):
        RHManageRegFormBase._process_args(self)
        ids = set(request.form.getlist('registration_id'))
        self.registrations = (Registration.query.with_parent(self.regform)
                              .filter(Registration.id.in_(ids),
                                      ~Registration.is_deleted)
                              .order_by(*Registration.order_by_name)
                              .options(*self.registration_query_options)
                              .all())


class RHRegistrationEmailRegistrantsPreview(RHRegistrationsActionBase):
    """Preview the email that will be sent to registrants."""

    def _process(self):
        if not self.registrations:
            raise NoReportError.wrap_exc(BadRequest(_("The selected registrants have been removed.")))
        registration = self.registrations[0]
        email_body = replace_placeholders('registration-email', request.form['body'], regform=self.regform,
                                          registration=registration)
        email_subject = replace_placeholders('registration-email', request.form['subject'], regform=self.regform,
                                             registration=registration)
        tpl = get_template_module('events/registration/emails/custom_email.html', email_subject=email_subject,
                                  email_body=email_body)
        html = render_template('events/registration/management/email_preview.html', subject=tpl.get_subject(),
                               body=tpl.get_body())
        return jsonify(html=html)


class RHRegistrationEmailRegistrants(RHRegistrationsActionBase):
    """Send email to selected registrants."""

    def _send_emails(self, form):
        for registration in self.registrations:
            email_body = replace_placeholders('registration-email', form.body.data, regform=self.regform,
                                              registration=registration)
            email_subject = replace_placeholders('registration-email', form.subject.data, regform=self.regform,
                                                 registration=registration)
            template = get_template_module('events/registration/emails/custom_email.html',
                                           email_subject=email_subject, email_body=email_body)
            bcc = [session.user.email] if form.copy_for_sender.data else []
            attach_ticket = 'attach_ticket' in form and form.attach_ticket.data and not registration.is_ticket_blocked
            attachments = get_ticket_attachments(registration) if attach_ticket else None
            email = make_email(to_list=registration.email, cc_list=form.cc_addresses.data, bcc_list=bcc,
                               from_address=form.from_address.data, template=template, html=True,
                               attachments=attachments)
            send_email(email, self.event, 'Registration')

    def _process(self):
        tpl = get_template_module('events/registration/emails/custom_email_default.html')
        default_body = tpl.get_html_body()
        registration_ids = request.form.getlist('registration_id')
        form = EmailRegistrantsForm(body=default_body, regform=self.regform, registration_id=registration_ids,
                                    recipients=[x.email for x in self.registrations])
        if not self.regform.tickets_enabled:
            del form.attach_ticket
        if form.validate_on_submit():
            self._send_emails(form)
            num_emails_sent = len(self.registrations)
            flash(ngettext("The email was sent.",
                           "{num} emails were sent.", num_emails_sent).format(num=num_emails_sent), 'success')
            return jsonify_data()

        registrations_without_ticket = [r for r in self.registrations if r.is_ticket_blocked]
        return jsonify_template('events/registration/management/email.html', form=form, regform=self.regform,
                                all_registrations_count=len(self.registrations),
                                registrations_without_ticket_count=len(registrations_without_ticket))


class RHRegistrationDelete(RHRegistrationsActionBase):
    """Delete selected registrations."""

    def _process(self):
        for registration in self.registrations:
            registration.is_deleted = True
            signals.event.registration_deleted.send(registration)
            logger.info('Registration %s deleted by %s', registration, session.user)
            registration.log(EventLogRealm.management, EventLogKind.negative, 'Registration',
                             'Registration deleted: {}'.format(registration.full_name),
                             session.user, data={'Email': registration.email})
        num_reg_deleted = len(self.registrations)
        flash(ngettext("Registration was deleted.",
                       "{num} registrations were deleted.", num_reg_deleted).format(num=num_reg_deleted), 'success')
        return jsonify_data()


class RHRegistrationCreate(RHManageRegFormBase):
    """Create new registration (management area)."""

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
        return WPManageRegistration.render_template('display/regform_display.html', self.event,
                                                    sections=get_event_section_data(self.regform), regform=self.regform,
                                                    post_url=url_for('.create_registration', self.regform),
                                                    user_data=self._get_user_data(), management=True)


class RHRegistrationCreateMultiple(RHManageRegFormBase):
    """Create multiple registrations for Indico users (management area)."""

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
    """Base class for all registration list export RHs."""

    ALLOW_LOCKED = True
    registration_query_options = (subqueryload('data'),)

    def _process_args(self):
        RHRegistrationsActionBase._process_args(self)
        self.export_config = self.list_generator.get_list_export_config()


class RHRegistrationsExportPDFTable(RHRegistrationsExportBase):
    """Export registration list to a PDF in table style."""

    def _process(self):
        pdf = RegistrantsListToPDF(self.event, reglist=self.registrations, display=self.export_config['regform_items'],
                                   static_items=self.export_config['static_item_ids'])
        try:
            data = pdf.getPDFBin()
        except Exception:
            if config.DEBUG:
                raise
            raise NoReportError(_("Text too large to generate a PDF with table style. "
                                  "Please try again generating with book style."))
        return send_file('RegistrantsList.pdf', BytesIO(data), 'application/pdf')


class RHRegistrationsExportPDFBook(RHRegistrationsExportBase):
    """Export registration list to a PDF in book style."""

    def _process(self):
        static_item_ids, item_ids = self.list_generator.get_item_ids()
        pdf = RegistrantsListToBookPDF(self.event, self.regform, self.registrations, item_ids, static_item_ids)
        return send_file('RegistrantsBook.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')


class RHRegistrationsExportCSV(RHRegistrationsExportBase):
    """Export registration list to a CSV file."""

    def _process(self):
        headers, rows = generate_spreadsheet_from_registrations(self.registrations, self.export_config['regform_items'],
                                                                self.export_config['static_item_ids'])
        return send_csv('registrations.csv', headers, rows)


class RHRegistrationsExportExcel(RHRegistrationsExportBase):
    """Export registration list to an XLSX file."""

    def _process(self):
        headers, rows = generate_spreadsheet_from_registrations(self.registrations, self.export_config['regform_items'],
                                                                self.export_config['static_item_ids'])
        return send_xlsx('registrations.xlsx', headers, rows, tz=self.event.tzinfo)


class RHRegistrationsImport(RHRegistrationsActionBase):
    """Import registrations from a CSV file."""

    def _process(self):
        form = ImportRegistrationsForm(regform=self.regform)

        if form.validate_on_submit():
            skip_moderation = self.regform.moderation_enabled and form.skip_moderation.data
            registrations = import_registrations_from_csv(self.regform, form.source_file.data,
                                                          skip_moderation=skip_moderation,
                                                          notify_users=form.notify_users.data)
            flash(ngettext("{} registration has been imported.",
                           "{} registrations have been imported.",
                           len(registrations)).format(len(registrations)), 'success')
            return jsonify_data(flash=False, redirect=url_for('.manage_reglist', self.regform),
                                redirect_no_loading=True)
        return jsonify_template('events/registration/management/import_registrations.html', form=form,
                                regform=self.regform)


class RHRegistrationsPrintBadges(RHRegistrationsActionBase):
    ALLOW_LOCKED = True
    normalize_url_spec = {
        'locators': {
            lambda self: self.regform
        },
        'preserved_args': {'uuid', 'template_id'}
    }

    def _process_args(self):
        RHRegistrationsActionBase._process_args(self)
        self.template = DesignerTemplate.get_or_404(request.view_args['template_id'])

    def _check_access(self):
        RHRegistrationsActionBase._check_access(self)

        # Check that template belongs to this event or a category that
        # is a parent
        if self.template.owner != self.event and self.template.owner.id not in self.event.category_chain:
            raise Forbidden

    def _process(self):
        config_params = badge_cache.get(request.view_args['uuid'])
        if not config_params:
            raise NotFound
        if config_params['page_layout'] == PageLayout.foldable:
            pdf_class = RegistrantsListToBadgesPDFFoldable
        elif config_params['page_layout'] == PageLayout.double_sided:
            pdf_class = RegistrantsListToBadgesPDFDoubleSided
        else:
            pdf_class = RegistrantsListToBadgesPDF
        registration_ids = config_params.pop('registration_ids')
        registrations = (Registration.query.with_parent(self.event)
                         .filter(Registration.id.in_(registration_ids),
                                 Registration.is_active)
                         .order_by(*Registration.order_by_name)
                         .options(subqueryload('data').joinedload('field_data'))
                         .all())
        signals.event.designer.print_badge_template.send(self.template, regform=self.regform,
                                                         registrations=registrations)
        pdf = pdf_class(self.template, config_params, self.event, registrations)
        return send_file('Badges-{}.pdf'.format(self.event.id), pdf.get_pdf(), 'application/pdf')


class RHRegistrationsConfigBadges(RHRegistrationsActionBase):
    """Print badges for the selected registrations."""

    ALLOW_LOCKED = True
    TICKET_BADGES = False

    format_map_portrait = {
        'A0': (84.1, 118.9),
        'A1': (59.4, 84.1),
        'A2': (42.0, 59.4),
        'A3': (29.7, 42.0),
        'A4': (21.0, 29.7),
        'A5': (14.8, 21.0),
        'A6': (10.5, 14.8),
        'A7': (7.4, 10.5),
        'A8': (5.2, 7.4),
    }

    format_map_landscape = {name: (h, w) for name, (w, h) in format_map_portrait.iteritems()}

    def _process_args(self):
        RHManageRegFormBase._process_args(self)
        ids = set(request.form.getlist('registration_id'))
        self.registrations = (Registration.query.with_parent(self.regform)
                              .filter(Registration.id.in_(ids),
                                      ~Registration.is_deleted)
                              .order_by(*Registration.order_by_name)
                              .all()) if ids else []
        self.template_id = request.args.get('template_id', self._default_template_id)

    def _get_format(self, tpl):
        from indico.modules.designer.pdf import PIXELS_CM
        format_map = self.format_map_landscape if tpl.data['width'] > tpl.data['height'] else self.format_map_portrait
        return next((frm for frm, frm_size in format_map.iteritems()
                     if (frm_size[0] == float(tpl.data['width']) / PIXELS_CM and
                         frm_size[1] == float(tpl.data['height']) / PIXELS_CM)), 'custom')

    @property
    def _default_template_id(self):
        return None

    def _filter_registrations(self, registrations):
        return registrations

    def _process(self):
        all_templates = set(self.event.designer_templates) | get_inherited_templates(self.event)
        badge_templates = {tpl.id: {
            'data': tpl.data,
            'backside_tpl_id': tpl.backside_template_id,
            'orientation': 'landscape' if tpl.data['width'] > tpl.data['height'] else 'portrait',
            'format': self._get_format(tpl)
        } for tpl in all_templates if tpl.type.name == 'badge'}
        settings = event_badge_settings.get_all(self.event.id)
        form = BadgeSettingsForm(self.event, template=self.template_id, tickets=self.TICKET_BADGES, **settings)
        all_registrations = [r for r in (self.registrations or self.regform.registrations) if r.is_active]
        registrations = self._filter_registrations(all_registrations)
        if self.event.is_locked:
            del form.save_values

        if form.validate_on_submit():
            data = form.data
            if data['page_layout'] == PageLayout.foldable:
                data['top_margin'] = 0
                data['bottom_margin'] = 0
                data['left_margin'] = 0
                data['right_margin'] = 0
                data['margin_columns'] = 0
                data['margin_rows'] = 0
                data['dashed_border'] = False
            data.pop('submitted', None)
            template_id = data.pop('template')
            if data.pop('save_values', False):
                event_badge_settings.set_multi(self.event, data)
            data['registration_ids'] = [x.id for x in registrations]

            key = unicode(uuid.uuid4())
            badge_cache.set(key, data, time=1800)
            download_url = url_for('.registrations_print_badges', self.regform, template_id=template_id, uuid=key)
            return jsonify_data(flash=False, redirect=download_url, redirect_no_loading=True)
        return jsonify_template('events/registration/management/print_badges.html', event=self.event,
                                regform=self.regform, settings_form=form, templates=badge_templates,
                                registrations=registrations, all_registrations=all_registrations)


class RHRegistrationsConfigTickets(RHRegistrationsConfigBadges):
    """Print tickets for selected registrations."""

    TICKET_BADGES = True

    @property
    def _default_template_id(self):
        return unicode(self.regform.ticket_template_id) if self.regform.ticket_template_id else None

    def _filter_registrations(self, registrations):
        return [r for r in registrations if not r.is_ticket_blocked]


class RHRegistrationTogglePayment(RHManageRegistrationBase):
    """Modify the payment status of a registration."""

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
    if registration.state != RegistrationState.pending:
        return
    if approve:
        registration.update_state(approved=True)
    else:
        registration.update_state(rejected=True)
    db.session.flush()
    notify_registration_state_update(registration)
    status = 'approved' if approve else 'rejected'
    logger.info('Registration %s was %s by %s', registration, status, session.user)


class RHRegistrationApprove(RHManageRegistrationBase):
    """Accept a registration."""

    def _process(self):
        _modify_registration_status(self.registration, approve=True)
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationReject(RHManageRegistrationBase):
    """Reject a registration."""

    def _process(self):
        form = RejectRegistrantsForm()
        if form.validate_on_submit():
            self.registration.rejection_reason = form.rejection_reason.data
            _modify_registration_status(self.registration, approve=False)
            return jsonify_data(html=_render_registration_details(self.registration))
        return jsonify_form(form, disabled_until_change=False, submit='Reject')


class RHRegistrationReset(RHManageRegistrationBase):
    """Reset a registration back to a non-approved status."""

    def _process(self):
        if self.registration.has_conflict():
            raise NoReportError(_('Cannot reset this registration since there is another valid registration for the '
                                  'same user or email.'))
        if self.registration.state in (RegistrationState.complete, RegistrationState.unpaid):
            self.registration.update_state(approved=False)
        elif self.registration.state == RegistrationState.rejected:
            self.registration.rejection_reason = None
            self.registration.update_state(rejected=False)
        elif self.registration.state == RegistrationState.withdrawn:
            self.registration.update_state(withdrawn=False)
            notify_registration_state_update(self.registration)
        else:
            raise BadRequest(_('The registration cannot be reset in its current state.'))
        self.registration.checked_in = False
        logger.info('Registration %r was reset by %r', self.registration, session.user)
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationManageWithdraw(RHManageRegistrationBase):
    """Let a manager withdraw a registration."""

    def _process(self):
        if self.registration.state in (RegistrationState.withdrawn, RegistrationState.rejected):
            raise BadRequest(_('The registration cannot be withdrawn in its current state.'))
        self.registration.update_state(withdrawn=True)
        flash(_('The registration has been withdrawn.'), 'success')
        logger.info('Registration %r was withdrawn by %r', self.registration, session.user)
        notify_registration_state_update(self.registration)
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationCheckIn(RHManageRegistrationBase):
    """Set checked in state of a registration."""

    def _process_PUT(self):
        if self.registration.state not in (RegistrationState.complete, RegistrationState.unpaid):
            raise BadRequest(_('This registration cannot be marked as checked-in'))
        self.registration.checked_in = True
        signals.event.registration_checkin_updated.send(self.registration)
        return jsonify_data(html=_render_registration_details(self.registration))

    def _process_DELETE(self):
        self.registration.checked_in = False
        signals.event.registration_checkin_updated.send(self.registration)
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationBulkCheckIn(RHRegistrationsActionBase):
    """Bulk apply check-in/not checked-in state to registrations."""

    def _process(self):
        check_in = request.form['flag'] == '1'
        msg = 'checked-in' if check_in else 'not checked-in'
        for registration in self.registrations:
            if registration.state not in (RegistrationState.complete, RegistrationState.unpaid):
                continue
            registration.checked_in = check_in
            signals.event.registration_checkin_updated.send(registration)
            logger.info('Registration %s marked as %s by %s', registration, msg, session.user)
        flash(_("Selected registrations marked as {} successfully.").format(msg), 'success')
        return jsonify_data(**self.list_generator.render_list())


class RHRegistrationsModifyStatus(RHRegistrationsActionBase):
    """Accept/Reject selected registrations."""

    def _process(self):
        approve = request.form.get('flag') == '1'
        if approve:
            for registration in self.registrations:
                _modify_registration_status(registration, approve)
            flash(_("The status of the selected registrations was successfully '{}'.").format('approved'), 'success')
            return jsonify_data(**self.list_generator.render_list())
        else:
            form = RejectRegistrantsForm(obj=FormDefaults(flag=request.args.get('flag'),
                                                          registration_id=request.args.getlist('registration_id')))
            if form.validate_on_submit():
                for registration in self.registrations:
                    registration.rejection_reason = form.rejection_reason.data
                    _modify_registration_status(registration, approve)
                flash(_("The status of the selected registrations was successfully '{}'.").format('rejected'),
                      'success')
                return jsonify_data(**self.list_generator.render_list())
            return jsonify_form(form, disabled_until_change=False, submit='Reject')


class RHRegistrationsExportAttachments(RHRegistrationsExportBase, ZipGeneratorMixin):
    """Export registration attachments in a zip file."""

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
