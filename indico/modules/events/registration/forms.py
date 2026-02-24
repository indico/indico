# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import time
from decimal import Decimal
from operator import itemgetter

import jsonschema
from flask import request, session
from wtforms.fields import BooleanField, DecimalField, FloatField, HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, Optional, ValidationError
from wtforms.widgets import NumberInput

from indico.core import signals
from indico.core.db import db
from indico.modules.designer import PageLayout, PageOrientation, PageSize, TemplateType
from indico.modules.designer.util import get_inherited_templates
from indico.modules.events.registration.models.tags import RegistrationTag
from indico.util.date_time import format_currency
from indico.util.i18n import _
from indico.util.placeholders import get_missing_placeholders, render_placeholder_info
from indico.util.spreadsheets import CSVFieldDelimiter
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (EmailListField, FileField, IndicoDateTimeField, IndicoEnumSelectField,
                                     IndicoMarkdownField, JSONField)
from indico.web.forms.fields.colors import SUIColorPickerField
from indico.web.forms.fields.principals import PrincipalListField
from indico.web.forms.fields.simple import HiddenFieldList, IndicoEmailRecipientsField
from indico.web.forms.fields.sqlalchemy import IndicoQuerySelectMultipleTagField
from indico.web.forms.validators import HiddenUnless, LinkedDateTime, NoEndpointLinks, NoRelativeURLs
from indico.web.forms.widgets import SwitchWidget, TinyMCEWidget


class RegistrationFormCloneForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()], description=_('The title of the registration form'))


class RegistrationFormScheduleForm(IndicoForm):
    start_dt = IndicoDateTimeField(_('Start'), [Optional()], default_time=time(0, 0),
                                   description=_('Moment when registrations will be open'))
    end_dt = IndicoDateTimeField(_('End'), [Optional(), LinkedDateTime('start_dt')], default_time=time(23, 59),
                                 description=_('Moment when registrations will be closed'))
    modification_end_dt = IndicoDateTimeField(_('Modification deadline'), [Optional(), LinkedDateTime('end_dt')],
                                              default_time=time(23, 59),
                                              description=_('Deadline until which registration information can be '
                                                            'modified (defaults to the end date if empty)'))

    def __init__(self, *args, **kwargs):
        regform = kwargs.pop('regform')
        self.timezone = regform.event.timezone
        super().__init__(*args, **kwargs)


class RegistrationExceptionalModificationForm(IndicoForm):
    modification_end_dt = IndicoDateTimeField(_('Modification deadline'), [DataRequired()], default_time=time(23, 59),
                                              description=_('Deadline until which registration information can be '
                                                            'modified'))

    def __init__(self, *args, regform, **kwargs):
        self.timezone = regform.event.timezone
        super().__init__(*args, **kwargs)


class EmailRegistrantsForm(IndicoForm):
    sender_address = SelectField(_('Sender'), [DataRequired()])
    cc_addresses = EmailListField(_('CC'),
                                  description=_('Beware, addresses in this field will receive one mail per '
                                                'registrant.'))
    subject = StringField(_('Subject'), [DataRequired(), Length(max=200)])
    body = TextAreaField(
        _('Email body'),
        [DataRequired(), NoRelativeURLs(), NoEndpointLinks('event_registration.display_regform', {'token'})],
        widget=TinyMCEWidget(absolute_urls=True),
    )
    recipients = IndicoEmailRecipientsField(_('Recipients'))
    copy_for_sender = BooleanField(_('Send copy to me'), widget=SwitchWidget(),
                                   description=_('Send a copy of each email to my mailbox'))
    attach_ticket = BooleanField(_('Attach ticket'), widget=SwitchWidget(),
                                 description=_('Attach tickets to emails'))
    registration_id = HiddenFieldList()
    submitted = HiddenField()

    def __init__(self, *args, **kwargs):
        self.regform = kwargs.pop('regform')
        event = self.regform.event
        super().__init__(*args, **kwargs)
        self.sender_address.choices = list(event.get_allowed_sender_emails().items())
        self.body.description = render_placeholder_info('registration-email', regform=self.regform, registration=None)

    def validate_body(self, field):
        missing = get_missing_placeholders('registration-email', field.data, regform=self.regform, registration=None)
        if missing:
            raise ValidationError(_('Missing placeholders: {}').format(', '.join(missing)))

    def is_submitted(self):
        return super().is_submitted() and 'submitted' in request.form


class TicketsForm(IndicoForm):
    tickets_enabled = BooleanField(_('Enable Tickets'), widget=SwitchWidget(),
                                   description=_('Create tickets for registrations using this registration form.'))
    ticket_google_wallet = BooleanField(_('Export to Google Wallet'), [HiddenUnless('tickets_enabled',
                                                                                    preserve_data=True)],
                                        widget=SwitchWidget(),
                                        description=_('Allow users to export their ticket to Google Wallet. '
                                                      'This currently does not support tickets for accompanying '
                                                      'persons.'))
    ticket_apple_wallet = BooleanField(_('Export to Apple Wallet'), [HiddenUnless('tickets_enabled',
                                                                                  preserve_data=True)],
                                       widget=SwitchWidget(),
                                       description=_('Allow users to export their ticket to Apple Wallet. This '
                                                     'currently does not support tickets for accompanying persons.'))
    ticket_on_email = BooleanField(_('Send with an e-mail'), [HiddenUnless('tickets_enabled',
                                                                           preserve_data=True)],
                                   widget=SwitchWidget(),
                                   description=_('Attach PDF ticket to the email sent to a user after completing '
                                                 'their registration.'))
    ticket_on_event_page = BooleanField(_('Download from event homepage'), [HiddenUnless('tickets_enabled',
                                                                                         preserve_data=True)],
                                        widget=SwitchWidget(),
                                        description=_('Allow users to download their ticket from the '
                                                      'conference homepage.'))
    ticket_on_summary_page = BooleanField(_('Download from summary page'), [HiddenUnless('tickets_enabled',
                                                                                         preserve_data=True)],
                                          widget=SwitchWidget(),
                                          description=_('Allow users to download their ticket from the registration '
                                                        'summary page.'))

    tickets_for_accompanying_persons = BooleanField(_('Tickets for accompanying persons'),
                                                    [HiddenUnless('tickets_enabled', preserve_data=True)],
                                                    widget=SwitchWidget(),
                                                    description=_("Create tickets for each of the user's accompanying "
                                                                  'persons.'))

    ticket_template_id = SelectField(_('Ticket template'), [HiddenUnless('tickets_enabled', preserve_data=True),
                                                            Optional()], coerce=int)

    def __init__(self, *args, event, regform, **kwargs):
        from indico.modules.designer.util import get_default_ticket_on_category, get_printable_event_templates
        super().__init__(*args, **kwargs)
        default_tpl = get_default_ticket_on_category(event.category)
        event_templates = get_printable_event_templates(regform)
        all_templates = set(event_templates) | get_inherited_templates(event)
        badge_templates = [(tpl.id, tpl.title) for tpl in all_templates
                           if tpl.type == TemplateType.badge and tpl != default_tpl]
        # Show the default template first
        badge_templates.insert(0, (default_tpl.id, '{} ({})'.format(default_tpl.title, _('Default category template'))))
        self.ticket_template_id.choices = badge_templates
        if not regform.is_google_wallet_configured:
            del self.ticket_google_wallet
        if not regform.is_apple_wallet_configured:
            del self.ticket_apple_wallet


class ParticipantsDisplayForm(IndicoForm):
    """Form to customize the display of the participant list."""

    json = JSONField()

    def __init__(self, *args, **kwargs):
        self.regforms = kwargs.pop('regforms')
        super().__init__(*args, **kwargs)

    def validate_json(self, field):
        schema = {
            'type': 'object',
            'properties': {
                'merge_forms': {'type': 'boolean'},
                'participant_list_forms': {
                    'type': 'array',
                    'items': {'type': 'integer'}
                },
                'participant_list_columns': {
                    'type': 'array',
                    'items': {'type': 'string'}
                }
            }
        }
        try:
            jsonschema.validate(field.data, schema)
        except jsonschema.ValidationError as exc:
            raise ValidationError(str(exc))


class ParticipantsDisplayFormColumnsForm(IndicoForm):
    """
    Form to customize the columns for a particular registration form
    on the participant list.
    """

    json = JSONField()

    def validate_json(self, field):
        schema = {
            'type': 'object',
            'properties': {
                'columns': {
                    'type': 'array',
                    'items': {'type': 'integer'}
                }
            }
        }
        try:
            jsonschema.validate(field.data, schema)
        except jsonschema.ValidationError as exc:
            raise ValidationError(str(exc))


class RegistrationManagersForm(IndicoForm):
    """Form to manage users with privileges to modify registration-related items."""

    managers = PrincipalListField(_('Registration managers'), allow_groups=True, allow_event_roles=True,
                                  allow_category_roles=True, allow_emails=True, allow_external_users=True,
                                  description=_('List of users allowed to modify registrations'),
                                  event=lambda form: form.event)

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)


class CreateMultipleRegistrationsForm(IndicoForm):
    """Form to create multiple registrations of Indico users at the same time."""

    user_principals = PrincipalListField(_('Indico users'), [DataRequired()], allow_external_users=True)
    notify_users = BooleanField(_('Send e-mail notifications'),
                                default=True,
                                description=_('Notify the users about the registration.'),
                                widget=SwitchWidget())

    def __init__(self, *args, **kwargs):
        self._regform = kwargs.pop('regform')
        open_add_user_dialog = kwargs.pop('open_add_user_dialog', False)
        super().__init__(*args, **kwargs)
        self.user_principals.open_immediately = open_add_user_dialog

    def validate_user_principals(self, field):
        for user in field.data:
            if user in db.session and self._regform.get_registration(user=user):
                raise ValidationError(_('A registration for {} already exists.').format(user.full_name))
            elif self._regform.get_registration(email=user.email):
                raise ValidationError(_('A registration for {} already exists.').format(user.email))


class BadgeSettingsForm(IndicoForm):
    _fieldsets = (
        (None, ('template',)),
        (_('Page configuration'), ('save_values', 'dashed_border', 'page_size', 'page_orientation', 'page_layout'))
    )

    template = SelectField(_('Template'))
    save_values = BooleanField(_('Save values for next time'), widget=SwitchWidget(),
                               description=_('Save these values in the event settings'))
    dashed_border = BooleanField(_('Dashed border around each badge'), widget=SwitchWidget(),
                                 description=_('Display a dashed border around each badge'))
    page_size = IndicoEnumSelectField(_('Page size'), enum=PageSize, sorted=True)
    page_orientation = IndicoEnumSelectField(_('Page orientation'), enum=PageOrientation)
    page_layout = IndicoEnumSelectField(_('Page layout'), enum=PageLayout,
                                        description=_('The single sided (foldable) option is only available if the '
                                                      'template orientation is the same as the page orientation and '
                                                      'its width is exactly half of the page width'))

    top_margin = FloatField(_('Top margin'), [InputRequired()])
    left_margin = FloatField(_('Left margin'), [InputRequired()])
    right_margin = FloatField(_('Right margin'), [InputRequired()])
    bottom_margin = FloatField(_('Bottom margin'), [InputRequired()])
    margin_columns = FloatField(_('Margin between columns'), [InputRequired()])
    margin_rows = FloatField(_('Margin between rows'), [InputRequired()])

    submitted = HiddenField()

    def __init__(self, event, **kwargs):
        all_templates = set(event.designer_templates) | get_inherited_templates(event)
        badge_templates = [tpl for tpl in all_templates if tpl.type.name == 'badge']
        signals.event.filter_selectable_badges.send(type(self), badge_templates=badge_templates)
        tickets = kwargs.pop('tickets')
        super().__init__(**kwargs)
        self.template.choices = sorted(((str(tpl.id), tpl.title)
                                        for tpl in badge_templates
                                        if tpl.is_ticket == tickets),
                                       key=itemgetter(1))

    def is_submitted(self):
        return super().is_submitted() and 'submitted' in request.form


class ImportRegistrationsForm(IndicoForm):
    source_file = FileField(_('Source File'), [DataRequired(_('You need to upload a CSV file.'))],
                            accepted_file_types='.csv')
    skip_moderation = BooleanField(_('Skip Moderation'), widget=SwitchWidget(), default=True,
                                   description=_('If enabled, the registration will be immediately accepted'))
    skip_access_check = BooleanField(_('Skip access check'), widget=SwitchWidget(),
                                     description=_('If enabled, invited people will be able to register even if the '
                                                   'event is access-restricted.'))
    notify_users = BooleanField(_('E-mail users'), widget=SwitchWidget(),
                                description=_('Whether the imported users should receive an e-mail notification'))
    delimiter = IndicoEnumSelectField(_('CSV field delimiter'), enum=CSVFieldDelimiter,
                                      default=CSVFieldDelimiter.comma.name)

    def __init__(self, *args, **kwargs):
        self.regform = kwargs.pop('regform')
        super().__init__(*args, **kwargs)
        if not self.regform.moderation_enabled:
            del self.skip_moderation


class RejectRegistrantsForm(IndicoForm):
    rejection_reason = TextAreaField(_('Reason'), description=_('You can provide a reason for the rejection here.'))
    attach_rejection_reason = BooleanField(_('Attach reason'), widget=SwitchWidget())
    registration_id = HiddenFieldList()
    submitted = HiddenField()

    def is_submitted(self):
        return super().is_submitted() and 'submitted' in request.form


class RegistrationTagForm(IndicoForm):
    """Form to create a new registration tag."""

    title = StringField(_('Title'), [DataRequired()])
    color = SUIColorPickerField(_('Color'), [DataRequired()])

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.tag = kwargs.pop('tag', None)
        super().__init__(*args, **kwargs)

    def validate_title(self, field):
        query = RegistrationTag.query.with_parent(self.event).filter(
            db.func.lower(RegistrationTag.title) == field.data.lower()
        )
        if self.tag:
            query = query.filter(RegistrationTag.id != self.tag.id)
        if query.has_rows():
            raise ValidationError(_('This title is already in use.'))


class RegistrationTagsAssignForm(IndicoForm):
    """Form to assign registration tags to registrations."""

    add = IndicoQuerySelectMultipleTagField(_('Add'), description=_('Select tags to assign'))
    remove = IndicoQuerySelectMultipleTagField(_('Remove'), description=_('Select tags to remove'))
    registration_id = HiddenFieldList()
    submitted = HiddenField()

    def __init__(self, *args, event, **kwargs):
        self.event = event  # used by IndicoQuerySelectMultipleTagField
        super().__init__(*args, **kwargs)

    def validate_remove(self, field):
        if set(self.remove.data) & set(self.add.data):
            raise ValidationError(_('You cannot add and remove the same tag'))

    validate_add = validate_remove

    def is_submitted(self):
        return super().is_submitted() and 'submitted' in request.form


class RegistrationBasePriceForm(IndicoForm):
    action = SelectField(_('Action'), [DataRequired()])
    base_price = DecimalField(_('Registration fee'),
                              [NumberRange(min=Decimal('0.01'), max=999999999.99), HiddenUnless('action', 'custom'),
                               DataRequired()],
                              filters=[lambda x: x if x is not None else 0], widget=NumberInput(step='0.01'))
    apply_complete = BooleanField(_('Apply to complete registrations'), [HiddenUnless('action', {'default', 'custom'})],
                                  widget=SwitchWidget(),
                                  description=_('If enabled, registrations in the "complete" state that had no fee '
                                                'before, will have the fee updated and changed to the "unpaid" state.'))
    registration_id = HiddenFieldList()
    submitted = HiddenField()

    def __init__(self, *args, currency, **kwargs):
        super().__init__(*args, **kwargs)
        self.action.choices = [
            ('remove', _('Remove fee for unpaid registrations')),
            ('default', (_("Set fee to the registration form's default ({})")
                         .format(format_currency(kwargs['base_price'], currency, locale=session.lang)))),
            ('custom', _('Change fee to custom value'))
        ]
        self.base_price.description = (_('A fixed fee (in {currency}) the selected users have to pay when registering.')
                                       .format(currency=currency))

    def is_submitted(self):
        return super().is_submitted() and 'submitted' in request.form


class PublishReceiptForm(IndicoForm):
    """Form to publish receipts for registrations."""

    notify_user = BooleanField(_('Notify users'), widget=SwitchWidget(),
                               description=_('Whether users should be notified about the published receipt'))


class MultiFormsAnnouncementForm(IndicoForm):
    message = IndicoMarkdownField('Message', render_kw={'rows': 10},
                                  description=_('You can enter an announcement text that is displayed when there are '
                                                'multiple registration forms for the user to choose from.'))
