# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import dataclasses
import itertools
import os
import uuid
from collections import defaultdict
from contextlib import contextmanager
from io import BytesIO
from operator import attrgetter

from babel.numbers import format_currency
from flask import flash, jsonify, redirect, render_template, request, session
from pypdf import PdfWriter
from sqlalchemy.orm import joinedload, subqueryload
from webargs import fields
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from indico.core import signals
from indico.core.cache import make_scoped_cache
from indico.core.config import config
from indico.core.db import db
from indico.core.errors import NoReportError
from indico.core.notifications import make_email, send_email
from indico.legacy.pdfinterface.conference import RegistrantsListToBookPDF, RegistrantsListToPDF
from indico.modules.categories.models.categories import Category
from indico.modules.designer import PageLayout, TemplateType
from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.designer.util import get_badge_format, get_inherited_templates
from indico.modules.events import EventLogRealm
from indico.modules.events.payment.util import toggle_registration_payment
from indico.modules.events.registration import logger
from indico.modules.events.registration.badges import (RegistrantsListToBadgesPDF,
                                                       RegistrantsListToBadgesPDFDoubleSided,
                                                       RegistrantsListToBadgesPDFFoldable)
from indico.modules.events.registration.controllers import (CheckEmailMixin, RegistrationEditMixin,
                                                            UploadRegistrationFileMixin, UploadRegistrationPictureMixin)
from indico.modules.events.registration.controllers.management import (RHManageRegFormBase, RHManageRegFormsBase,
                                                                       RHManageRegistrationBase)
from indico.modules.events.registration.forms import (BadgeSettingsForm, CreateMultipleRegistrationsForm,
                                                      EmailRegistrantsForm, ImportRegistrationsForm, PublishReceiptForm,
                                                      RegistrationBasePriceForm,
                                                      RegistrationExceptionalModificationForm, RejectRegistrantsForm)
from indico.modules.events.registration.models.items import PersonalDataType, RegistrationFormItemType
from indico.modules.events.registration.models.registrations import Registration, RegistrationData, RegistrationState
from indico.modules.events.registration.notifications import (notify_registration_receipt_created,
                                                              notify_registration_state_update)
from indico.modules.events.registration.settings import event_badge_settings
from indico.modules.events.registration.util import (ActionMenuEntry, create_registration,
                                                     generate_spreadsheet_from_registrations,
                                                     get_flat_section_submission_data, get_initial_form_values,
                                                     get_ticket_attachments, get_title_uuid, get_user_data,
                                                     import_registrations_from_csv, make_registration_schema)
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.events.util import ZipGeneratorMixin
from indico.modules.logs import LogKind
from indico.modules.logs.util import make_diff_log
from indico.modules.receipts.models.files import ReceiptFile
from indico.util.date_time import now_utc, relativedelta
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.util.marshmallow import Principal
from indico.util.placeholders import replace_placeholders
from indico.util.signals import values_from_signal
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.web.args import parser, use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file, url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


badge_cache = make_scoped_cache('badge-printing')


def _render_registration_details(registration):
    from indico.modules.events.registration.schemas import RegistrationTagSchema

    event = registration.registration_form.event
    tpl = get_template_module('events/registration/management/_registration_details.html')

    schema = RegistrationTagSchema(many=True)
    assigned_tags = schema.dump(registration.tags)
    all_tags = schema.dump(event.registration_tags)

    return tpl.render_registration_details(registration=registration, payment_enabled=event.has_feature('payment'),
                                           assigned_tags=assigned_tags, all_tags=all_tags)


class RHRegistrationsListManage(RHManageRegFormBase):
    """List all registrations of a specific registration form of an event."""

    def _process(self):
        if self.list_generator.static_link_used:
            return redirect(self.list_generator.get_list_url())
        reg_list_kwargs = self.list_generator.get_list_kwargs()
        regform = self.regform

        event = regform.event
        badge_templates = [tpl for tpl in set(event.designer_templates) | get_inherited_templates(event)
                           if tpl.type == TemplateType.badge]

        action_menu_items = [
            ActionMenuEntry(
                _('E-mail'),
                'mail',
                url=url_for('.email_registrants', regform),
                dialog_title=_('Send e-mail'),
                weight=100,
                hide_if_locked=True,
            ), ActionMenuEntry(
                _('Download Attachments'),
                'attachment',
                type='href-custom',
                url=url_for('.registrations_attachments_export', regform),
                weight=60,
                extra_classes='js-submit-list-form regform-download-attachments',
            ),
            ActionMenuEntry(
                _('Edit Tags'),
                'tag',
                url=url_for('.manage_registration_tags_assign', regform),
                weight=50,
                # XXX this is a hack to keep the item disabled when there are no tags defined
                requires_selected=bool(regform.event.registration_tags),
                reload_page=True
            )
        ]

        # the regform has at least one ticket template
        if any(tpl.is_ticket for tpl in badge_templates):
            action_menu_items.append(ActionMenuEntry(
                _('Print Badges'),
                'id-badge',
                url=url_for('.registrations_config_badges', regform),
                weight=90,
            ))

        # the regform has at least one badge template
        if any(not tpl.is_ticket for tpl in badge_templates):
            action_menu_items.append(ActionMenuEntry(
                _('Print Tickets'),
                'ticket',
                url=url_for('.registrations_config_tickets', regform),
                weight=80,
            ))

        if event.has_feature('payment'):
            action_menu_items.append(ActionMenuEntry(
                _('Update Registration Fee'),
                'coins',
                url=url_for('.registrations_update_price', regform),
                weight=40,
                reload_page=True
            ))

        action_menu_items = sorted(
            itertools.chain(
                action_menu_items,
                values_from_signal(signals.event.registrant_list_action_menu.send(regform), as_list=True)
            ),
            key=attrgetter('weight'),
            reverse=True
        )

        return WPManageRegistration.render_template('management/regform_reglist.html', self.event,
                                                    action_menu_items=action_menu_items, **reg_list_kwargs)


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
        self.field_data = (RegistrationData.query
                           .filter(RegistrationData.registration_id == request.view_args['registration_id'],
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
        return url_for('event_registration.registration_details', self.registration)


class RHRegistrationsActionBase(RHManageRegFormBase):
    """Base class for classes performing actions on registrations."""

    registration_query_options = ()

    @use_kwargs({
        'registration_ids': fields.List(fields.Integer(), data_key='registration_id', load_default=lambda: []),
    })
    def _process_args(self, registration_ids):
        RHManageRegFormBase._process_args(self)
        self.registrations = (Registration.query.with_parent(self.regform)
                              .filter(Registration.id.in_(registration_ids),
                                      ~Registration.is_deleted)
                              .order_by(*Registration.order_by_name)
                              .options(*self.registration_query_options)
                              .all())


class RHRegistrationEmailRegistrantsPreview(RHRegistrationsActionBase):
    """Preview the email that will be sent to registrants."""

    def _process(self):
        if not self.registrations:
            raise NoReportError.wrap_exc(BadRequest(_('The selected registrants have been removed.')))
        registration = self.registrations[0]
        email_body = replace_placeholders('registration-email', request.form['body'], regform=self.regform,
                                          registration=registration)
        email_subject = replace_placeholders('registration-email', request.form['subject'], regform=self.regform,
                                             registration=registration)
        with self.regform.event.force_event_locale():
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
            with self.regform.event.force_event_locale(registration.user):
                template = get_template_module('events/registration/emails/custom_email.html',
                                               email_subject=email_subject, email_body=email_body)
                bcc = [session.user.email] if form.copy_for_sender.data else []
                ticket_template = self.regform.get_ticket_template()
                is_ticket_blocked = ticket_template.is_ticket and registration.is_ticket_blocked
                attach_ticket = (
                    'attach_ticket' in form and form.attach_ticket.data and not is_ticket_blocked
                )
                attachments = get_ticket_attachments(registration) if attach_ticket else None
                email = make_email(to_list=registration.email, cc_list=form.cc_addresses.data, bcc_list=bcc,
                                   from_address=form.from_address.data, template=template, html=True,
                                   attachments=attachments)
            signals.core.before_notification_send.send('registration-custom-email', email=email,
                                                       registration=registration, form=form)
            send_email(email, self.event, 'Registration', session.user,
                       log_metadata={'registration_id': registration.id})

    def _process(self):
        with self.regform.event.force_event_locale():
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
            flash(ngettext('The email was sent.',
                           '{num} emails were sent.', num_emails_sent).format(num=num_emails_sent), 'success')
            return jsonify_data()

        template_is_ticket = self.regform.get_ticket_template().is_ticket
        registrations_without_ticket = [r for r in self.registrations if template_is_ticket and r.is_ticket_blocked]
        return jsonify_template('events/registration/management/email.html', form=form, regform=self.regform,
                                all_registrations_count=len(self.registrations),
                                registrations_without_ticket_count=len(registrations_without_ticket))


class RHRegistrationDelete(RHRegistrationsActionBase):
    """Delete selected registrations."""

    def _process(self):
        for registration in self.registrations:
            registration.is_deleted = True
            signals.event.registration_deleted.send(registration, permanent=False)
            logger.info('Registration %s deleted by %s', registration, session.user)
            registration.log(EventLogRealm.management, LogKind.negative, 'Registration',
                             f'Registration deleted: {registration.full_name}',
                             session.user, data={'Email': registration.email})
        num_reg_deleted = len(self.registrations)
        flash(ngettext('Registration was deleted.',
                       '{num} registrations were deleted.', num_reg_deleted).format(num=num_reg_deleted), 'success')
        return jsonify_data()


class RHRegistrationCreate(RHManageRegFormBase):
    """Create new registration (management area)."""

    @use_kwargs({
        'user': Principal(allow_external_users=True, load_default=None),
    }, location='query')
    def _get_user_data(self, user):
        return get_user_data(self.regform, user)

    def _process_POST(self):
        if self.regform.is_purged:
            raise Forbidden(_('Registration is disabled due to an expired retention period'))
        override_required = request.json.get('override_required', False)
        schema = make_registration_schema(self.regform, management=True, override_required=override_required)()
        form = parser.parse(schema)
        session['registration_notify_user_default'] = notify_user = form.pop('notify_user', False)
        create_registration(self.regform, form, management=True, notify_user=notify_user)
        flash(_('The registration was created.'), 'success')
        return jsonify({'redirect': url_for('event_registration.manage_reglist', self.regform)})

    def _process_GET(self):
        user_data = self._get_user_data()
        initial_values = get_initial_form_values(self.regform, management=True) | user_data
        form_data = get_flat_section_submission_data(self.regform, management=True)
        return WPManageRegistration.render_template('display/regform_display.html', self.event,
                                                    regform=self.regform,
                                                    form_data=form_data,
                                                    initial_values=initial_values,
                                                    invitation=None,
                                                    registration=None,
                                                    management=True,
                                                    login_required=False,
                                                    is_restricted_access=False,
                                                    captcha_required=False)


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
            if self.regform.is_purged:
                raise Forbidden(_('Registration is disabled due to an expired retention period'))
            session['registration_notify_user_default'] = form.notify_users.data
            for user in form.user_principals.data:
                self._register_user(user, form.notify_users.data)
            return jsonify_data(**self.list_generator.render_list())

        return jsonify_template('events/registration/management/registration_create_multiple.html', form=form)


class RHRegistrationCheckEmail(CheckEmailMixin, RHManageRegFormBase):
    """Check how an email will affect the registration."""

    def _process_args(self):
        RHManageRegFormBase._process_args(self)
        CheckEmailMixin._process_args(self)

    def _process(self):
        return self._check_email(management=True)


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
            raise NoReportError(_('Text too large to generate a PDF with table style. '
                                  'Please try again generating with book style.'))
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
            if self.regform.is_purged:
                raise Forbidden(_('Registration is disabled due to an expired retention period'))
            skip_moderation = self.regform.moderation_enabled and form.skip_moderation.data
            registrations = import_registrations_from_csv(self.regform, form.source_file.data,
                                                          skip_moderation=skip_moderation,
                                                          notify_users=form.notify_users.data)
            flash(ngettext('{} registration has been imported.',
                           '{} registrations have been imported.',
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

        # Check that template belongs to this event or a category that is a parent
        if self.template.owner == self.event:
            return
        valid_category_ids = self.event.category_chain or [Category.get_root().id]
        if self.template.owner.id not in valid_category_ids:
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
        pdf = pdf_class(self.template, config_params, self.event, registrations,
                        self.regform.tickets_for_accompanying_persons)
        return send_file(f'Badges-{self.event.id}.pdf', pdf.get_pdf(), 'application/pdf')


class RHRegistrationsConfigBadges(RHRegistrationsActionBase):
    """Print badges for the selected registrations."""

    ALLOW_LOCKED = True
    TICKET_BADGES = False

    def _process_args(self):
        RHManageRegFormBase._process_args(self)
        ids = set(request.form.getlist('registration_id'))
        self.registrations = (Registration.query.with_parent(self.regform)
                              .filter(Registration.id.in_(ids),
                                      ~Registration.is_deleted)
                              .order_by(*Registration.order_by_name)
                              .all()) if ids else []
        self.template_id = request.args.get('template_id', self._default_template_id)

    @property
    def _default_template_id(self):
        return None

    def _filter_registrations(self, registrations):
        return registrations

    def _get_event_badge_settings(self, event):
        return event_badge_settings.get_all(event.id)

    def _process(self):
        all_templates = set(self.event.designer_templates) | get_inherited_templates(self.event)
        badge_templates = {tpl.id: {
            'data': tpl.data,
            'backside_tpl_id': tpl.backside_template_id,
            'orientation': 'landscape' if tpl.data['width'] > tpl.data['height'] else 'portrait',
            'format': get_badge_format(tpl)
        } for tpl in all_templates if tpl.type.name == 'badge'}
        settings = self._get_event_badge_settings(self.event)
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

            key = str(uuid.uuid4())
            badge_cache.set(key, data, timeout=1800)
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
        return str(self.regform.ticket_template_id) if self.regform.ticket_template_id else None

    def _filter_registrations(self, registrations):
        return [r for r in registrations if not r.is_ticket_blocked]


class RHRegistrationTogglePayment(RHManageRegistrationBase):
    """Modify the payment status of a registration."""

    def _process(self):
        pay = request.form.get('pay') == '1'
        if pay != self.registration.is_paid:
            toggle_registration_payment(self.registration, paid=pay)
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationUploadFile(UploadRegistrationFileMixin, RHManageRegFormBase):
    """Upload a file from a registration form."""


class RHRegistrationUploadPicture(UploadRegistrationPictureMixin, RHRegistrationUploadFile):
    """Upload a picture from a registration form."""


def _modify_registration_status(registration, approve, rejection_reason='', attach_rejection_reason=False):
    if registration.state != RegistrationState.pending:
        return
    if approve:
        registration.update_state(approved=True)
    else:
        registration.rejection_reason = rejection_reason
        registration.update_state(rejected=True)
    db.session.flush()
    notify_registration_state_update(registration, attach_rejection_reason=attach_rejection_reason,
                                     from_management=True)
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
        message = _('Rejecting this registration will trigger a notification email.')
        if form.validate_on_submit():
            _modify_registration_status(self.registration, approve=False, rejection_reason=form.rejection_reason.data,
                                        attach_rejection_reason=form.attach_rejection_reason.data)
            return jsonify_data(html=_render_registration_details(self.registration))
        return jsonify_form(form, disabled_until_change=False, submit=_('Reject'), message=message)


class RHRegistrationReset(RHManageRegistrationBase):
    """Reset a registration back to a non-approved status."""

    def _process(self):
        if self.registration.has_conflict():
            raise NoReportError(_('Cannot reset this registration since there is another valid registration for the '
                                  'same user or email.'))
        if self.registration.state in (RegistrationState.complete, RegistrationState.unpaid):
            self.registration.update_state(approved=False)
        elif self.registration.state == RegistrationState.rejected:
            self.registration.rejection_reason = ''
            self.registration.update_state(rejected=False)
        elif self.registration.state == RegistrationState.withdrawn:
            self.registration.update_state(withdrawn=False)
            notify_registration_state_update(self.registration, from_management=True)
        else:
            raise BadRequest(_('The registration cannot be reset in its current state.'))
        self.registration.checked_in = False
        logger.info('Registration %r was reset by %r', self.registration, session.user)
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationHide(RHManageRegistrationBase):
    """Hide a registration from the participants lists."""

    def _log_changes(self):
        regform = self.registration.registration_form
        if self.registration.participant_hidden:
            self.registration.log(
                EventLogRealm.management, LogKind.negative, 'Privacy',
                f'Participant hidden in "{regform.title}": {self.registration.full_name}',
                session.user, data={'Email': self.registration.email}
            )
        else:
            self.registration.log(
                EventLogRealm.management, LogKind.positive, 'Privacy',
                f'Participant visibility restored in "{regform.title}": {self.registration.full_name}',
                session.user, data={'Email': self.registration.email}
            )

    def _process(self):
        self.registration.participant_hidden = not self.registration.participant_hidden
        self._log_changes()
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationManageWithdraw(RHManageRegistrationBase):
    """Let a manager withdraw a registration."""

    def _process(self):
        if self.registration.state in (RegistrationState.withdrawn, RegistrationState.rejected):
            raise BadRequest(_('The registration cannot be withdrawn in its current state.'))
        self.registration.update_state(withdrawn=True)
        flash(_('The registration has been withdrawn.'), 'success')
        logger.info('Registration %r was withdrawn by %r', self.registration, session.user)
        notify_registration_state_update(self.registration, from_management=True)
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationScheduleModification(RHManageRegistrationBase):
    """Let a manager schedule the registration modification deadline."""

    def _process(self):
        default_modification_end_dt = now_utc() + relativedelta(weeks=1)
        modification_form_defaults = FormDefaults(modification_end_dt=default_modification_end_dt)
        form = RegistrationExceptionalModificationForm(regform=self.regform, obj=modification_form_defaults)

        if form.validate_on_submit():
            self.registration.modification_end_dt = form.modification_end_dt.data
            flash(_('Deadline for registration modification has been scheduled'), 'success')
            self.registration.log(EventLogRealm.management, LogKind.change, 'Registration',
                                  f'Modification deadline updated for {self.registration.full_name}',
                                  session.user, data={'Deadline': self.registration.modification_end_dt.isoformat()})
            return jsonify_data(html=_render_registration_details(self.registration))
        return jsonify_form(form, disabled_until_change=False)


class RHRegistrationRemoveModification(RHManageRegistrationBase):
    """Let a manager close modification for a registration."""

    def _process(self):
        self.registration.modification_end_dt = None
        self.registration.log(EventLogRealm.management, LogKind.change, 'Registration',
                              f'Modification closed for {self.registration.full_name}', session.user)
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
        flash(_('Selected registrations marked as {} successfully.').format(msg), 'success')
        return jsonify_data(**self.list_generator.render_list())


class RHRegistrationsApprove(RHRegistrationsActionBase):
    """Accept selected registrations from registration list."""

    def _process(self):
        for registration in self.registrations:
            _modify_registration_status(registration, approve=True)
        flash(_('The selected registrations were successfully approved.'), 'success')
        return jsonify_data(**self.list_generator.render_list())


class RHRegistrationsReject(RHRegistrationsActionBase):
    """Reject selected registrations from registration list."""

    def _process(self):
        form = RejectRegistrantsForm(registration_id=[r.id for r in self.registrations])
        message = _('Rejecting these registrations will trigger a notification email for each registrant.')
        if form.validate_on_submit():
            for registration in self.registrations:
                _modify_registration_status(registration, approve=False, rejection_reason=form.rejection_reason.data,
                                            attach_rejection_reason=form.attach_rejection_reason.data)
            flash(_('The selected registrations were successfully rejected.'), 'success')
            return jsonify_data(**self.list_generator.render_list())
        return jsonify_form(form, disabled_until_change=False, submit=_('Reject'), message=message)


class RHRegistrationsBasePrice(RHRegistrationsActionBase):
    """Edit the base price of the selected registrations."""

    def _process(self):
        form = RegistrationBasePriceForm(base_price=self.regform.base_price, currency=self.regform.currency,
                                         registration_id=[reg.id for reg in self.registrations])
        if form.validate_on_submit():
            log_fields = {
                'base_price': {'title': 'Registration Fee', 'type': 'string'},
                'state': 'State'
            }
            num_skipped = 0
            num_updates = 0
            for reg in self.registrations:
                prev_state = reg.state
                if form.apply_complete.data and reg.state == RegistrationState.complete and not reg.base_price:
                    reg.state = RegistrationState.unpaid
                elif reg.state != RegistrationState.unpaid:
                    num_skipped += 1
                    continue
                new_price = {
                    'remove': 0,
                    'default': self.regform.base_price,
                    'custom': form.base_price.data
                }[form.action.data]
                changes = {}
                if reg.base_price != new_price or reg.currency != self.regform.currency:
                    changes['base_price'] = (format_currency(reg.base_price, reg.currency, locale='en_GB'),
                                             format_currency(new_price, self.regform.currency, locale='en_GB'))
                    reg.base_price = new_price
                    reg.currency = self.regform.currency
                if not reg.price:
                    reg.state = RegistrationState.complete
                if prev_state != reg.state:
                    changes['state'] = (prev_state, reg.state)
                    signals.event.registration_state_updated.send(reg, previous_state=prev_state, silent=True)
                    notify_registration_state_update(reg, from_management=True)
                if changes:
                    reg.log(EventLogRealm.management, LogKind.change, 'Registration',
                            f'Registration fee updated: {reg.full_name}',
                            session.user, data={'Changes': make_diff_log(changes, log_fields)})
                    num_updates += 1
            db.session.flush()
            # we count an update as a success even if nothing has changed
            num_successes = len(self.registrations) - num_skipped
            if num_successes:
                flash(ngettext('Registration fee has been updated for {} registration.',
                               'Registration fee has been updated for {} registrations.',
                               num_successes).format(num_successes), 'success')
            if num_updates:
                logger.info('%r registrations had their fee changed by %r', num_updates, session.user)
            if num_skipped:
                if form.apply_complete.data:
                    msg = ngettext('{} registration was skipped because its fee is not zero or it is in an invalid '
                                   'state.', '{} registrations were skipped because their fees are not zero or they '
                                   'are in an invalid state.', num_skipped)
                else:
                    msg = ngettext('{} registration was skipped because it is not in the unpaid state.',
                                   '{} registrations were skipped because they are not in the unpaid state.',
                                   num_skipped)
                flash(msg.format(num_skipped), 'warning')
            return jsonify_data(flash=False)
        return jsonify_form(form, disabled_until_change=False)


class RHRegistrationsExportAttachments(ZipGeneratorMixin, RHRegistrationsExportBase):
    """Export registration attachments in a zip file."""

    def _prepare_folder_structure(self, attachment):
        registration = attachment.registration
        regform_title = secure_filename(attachment.registration.registration_form.title, 'registration_form')
        registrant_name = secure_filename(f'{registration.get_full_name()}_{registration.friendly_id!s}',
                                          registration.friendly_id)
        file_name = secure_filename(
            f'{attachment.field_data.field.title}_{attachment.field_data.field_id}_{attachment.filename}',
            attachment.filename
        )
        return os.path.join(*self._adjust_path_length([regform_title, registrant_name, file_name]))

    def _iter_items(self, attachments):
        for reg_attachments in attachments.values():
            yield from reg_attachments

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


@dataclasses.dataclass
class _FileWrapper:
    content: BytesIO
    filename: str


# TODO: Try to merge this with RHExportReceipts (and maybe use a nice react dialog
# to choose what to export). This would allow to get rid of all the ugly hacks to
# merge the PDFs and then feed them to the with the ZIP generator.
# It would also allow users to actually choose receipts from which template they
# want to export instead of always exporting everything, and maybe even an option
# to filter based on the 'published' flag.
class RHRegistrationsExportReceipts(ZipGeneratorMixin, RHRegistrationsActionBase):
    """Export registration receipts in a zip file."""

    ALLOW_LOCKED = True

    def _prepare_folder_structure(self, data):
        if isinstance(data, _FileWrapper):
            return os.path.join(*self._adjust_path_length([data.filename]))
        else:
            template_prefixes, file = data
            reg = file.receipt_file.registration
            registrant_name = f'{reg.get_full_name()}_{reg.friendly_id}'
            file_name = secure_filename(f'{registrant_name}_{file.id}_{file.filename}', f'{file.id}_document.pdf')
            return os.path.join(*self._adjust_path_length([*template_prefixes, file_name]))

    def _iter_items(self, receipts_by_template):
        for template, receipts in receipts_by_template.items():
            if not self.combined:
                for receipt in receipts:
                    yield [f'{template.title}-{template.id}'], receipt.file
                continue
            output = PdfWriter()
            for receipt in receipts:
                with receipt.file.open() as fd:
                    output.append(fd)
            outputbuf = BytesIO()
            output.write(outputbuf)
            outputbuf.seek(0)
            yield _FileWrapper(outputbuf, f'{template.title}-{template.id}.pdf')

    @contextmanager
    def _get_item_path(self, item):
        if isinstance(item, _FileWrapper):
            yield item.content
            return

        with item[1].get_local_path() as path:
            yield path

    @use_kwargs({
        'combined': fields.Bool(load_default=False),
    }, location='query')
    def _process_args(self, combined):
        RHRegistrationsExportBase._process_args(self)
        self.combined = combined
        receipts = (ReceiptFile.query
                    .filter(~ReceiptFile.is_deleted,
                            ReceiptFile.registration_id.in_(r.id for r in self.registrations))
                    .order_by(ReceiptFile.template_id,
                              ReceiptFile.registration_id,
                              ReceiptFile.file_id)
                    .all())
        self.receipts_by_template = defaultdict(list)
        for receipt in receipts:
            self.receipts_by_template[receipt.template].append(receipt)

    def _process(self):
        if self.combined and len(self.receipts_by_template) == 1:
            receipts = next(iter(self.receipts_by_template.values()))
            output = PdfWriter()
            for receipt in receipts:
                with receipt.file.open() as fd:
                    output.append(fd)
            outputbuf = BytesIO()
            output.write(outputbuf)
            outputbuf.seek(0)
            return send_file('documents.pdf', outputbuf, 'application/pdf')

        return self._generate_zip_file(self.receipts_by_template, 'documents')


class RHManageReceiptBase(RHManageRegistrationBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.receipt_file
        }
    }

    def _process_args(self):
        RHManageRegistrationBase._process_args(self)
        self.receipt_file = (ReceiptFile.query
                             .with_parent(self.registration)
                             .filter_by(file_id=request.view_args['file_id'])
                             .first_or_404())

    def _render_receipts_list(self):
        tpl_summary = get_template_module('events/registration/display/_registration_summary_blocks.html')
        return tpl_summary.render_receipts_list(self.registration, from_management=True)


class RHDownloadReceipt(RHManageReceiptBase):
    """Download a receipt file from a registration."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.receipt_file.locator.filename
        }
    }

    def _process(self):
        return self.receipt_file.file.send()


class RHPublishReceipt(RHManageReceiptBase):
    """Publish a receipt to a registration."""

    def _process(self):
        if self.receipt_file.is_published:
            return jsonify_data()
        form = PublishReceiptForm()
        if form.validate_on_submit():
            self.receipt_file.is_published = True
            flash(_("Document '{}' successfully published").format(self.receipt_file.file.filename), 'success')
            logger.info('Document %r from registration %r was published by %r', self.receipt_file.file.filename,
                        self.registration, session.user)
            notify_registration_receipt_created(self.registration, self.receipt_file,
                                                notify_user=form.notify_user.data)
            self.registration.log(EventLogRealm.management, LogKind.change, 'Documents',
                                  f'Document "{self.receipt_file.file.filename}" published', session.user,
                                  data={'Notified': form.notify_user.data})
            return jsonify_data(html=self._render_receipts_list())
        return jsonify_form(form, submit=_('Publish'), back=_('Cancel'), footer_align_right=True,
                            disabled_until_change=False)


class RHUnpublishReceipt(RHManageReceiptBase):
    """Unpublish a receipt from a registration."""

    def _process(self):
        if not self.receipt_file.is_published:
            return jsonify_data()
        self.receipt_file.is_published = False
        flash(_("Document '{}' successfully unpublished").format(self.receipt_file.file.filename), 'success')
        logger.info('Document %r from registration %r was unpublished by %r', self.receipt_file.file.filename,
                    self.registration, session.user)
        self.registration.log(EventLogRealm.management, LogKind.change, 'Documents',
                              f'Document "{self.receipt_file.file.filename}" unpublished', session.user)
        return jsonify_data(html=self._render_receipts_list())


class RHDeleteReceipt(RHManageReceiptBase):
    """Delete a receipt from a registration."""

    def _process(self):
        self.receipt_file.is_deleted = True
        db.session.flush()
        logger.info('Document file %s deleted by %s', self.receipt_file, session.user)
        self.registration.log(EventLogRealm.management, LogKind.negative, 'Documents',
                              f'Document "{self.receipt_file.file.filename}" deleted', session.user)
        flash(_("Document '{}' successfully deleted").format(self.receipt_file.file.filename), 'success')
        return jsonify_data(html=self._render_receipts_list())
