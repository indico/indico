# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import time, timedelta
from decimal import Decimal
from enum import auto
from operator import itemgetter

import jsonschema
from babel.numbers import format_currency
from flask import request, session
from wtforms.fields import (BooleanField, DecimalField, EmailField, FloatField, HiddenField, IntegerField, SelectField,
                            StringField, TextAreaField)
from wtforms.validators import DataRequired, Email, InputRequired, NumberRange, Optional, ValidationError
from wtforms.widgets import NumberInput

from indico.core import signals
from indico.core.config import config
from indico.core.db import db
from indico.modules.designer import PageLayout, PageOrientation, PageSize, TemplateType
from indico.modules.designer.util import get_inherited_templates
from indico.modules.events.features.util import is_feature_enabled
from indico.modules.events.payment import payment_settings
from indico.modules.events.registration.models.forms import ModificationMode
from indico.modules.events.registration.models.invitations import RegistrationInvitation
from indico.modules.events.registration.models.items import RegistrationFormItem
from indico.modules.events.registration.models.registrations import PublishRegistrationsMode, Registration
from indico.modules.events.registration.models.tags import RegistrationTag
from indico.modules.events.settings import data_retention_settings
from indico.util.enum import RichStrEnum
from indico.util.i18n import _, ngettext
from indico.util.placeholders import get_missing_placeholders, render_placeholder_info
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import EmailListField, FileField, IndicoDateTimeField, IndicoEnumSelectField, JSONField
from indico.web.forms.fields.colors import SUIColorPickerField
from indico.web.forms.fields.datetime import TimeDeltaField
from indico.web.forms.fields.principals import PrincipalListField
from indico.web.forms.fields.simple import (HiddenFieldList, IndicoEmailRecipientsField, IndicoMultipleTagSelectField,
                                            IndicoParticipantVisibilityField)
from indico.web.forms.util import inject_validators
from indico.web.forms.validators import (DataRetentionPeriodValidator, HiddenUnless, IndicoEmail, LinkedDateTime,
                                         NoRelativeURLs)
from indico.web.forms.widgets import SwitchWidget, TinyMCEWidget


def _check_if_payment_required(form, field):
    if not field.data:
        return
    if not is_feature_enabled(form.event, 'payment'):
        raise ValidationError(_('You have to enable the payment feature in order to set a registration fee.'))


class RegistrationFormEditForm(IndicoForm):
    _price_fields = ('currency', 'base_price')
    _registrant_notification_fields = ('notification_sender_address', 'message_pending', 'message_unpaid',
                                       'message_complete', 'attach_ical')
    _manager_notification_fields = ('manager_notifications_enabled', 'manager_notification_recipients')
    _special_fields = _price_fields + _registrant_notification_fields + _manager_notification_fields

    title = StringField(_('Title'), [DataRequired()], description=_('The title of the registration form'))
    introduction = TextAreaField(_('Introduction'),
                                 description=_('Introduction to be displayed when filling out the registration form'))
    contact_info = StringField(_('Contact info'),
                               description=_('How registrants can get in touch with somebody for extra information'))
    moderation_enabled = BooleanField(_('Moderated'), widget=SwitchWidget(),
                                      description=_('If enabled, registrations require manager approval'))
    private = BooleanField(_('Private'), widget=SwitchWidget(),
                           description=_('The registration form will not be publicly displayed on the event page. '
                                         'Only people with the secret link or an invitation will be able to register.'))
    require_login = BooleanField(_('Only logged-in users'), widget=SwitchWidget(),
                                 description=_('Users must be logged in to register'))
    require_user = BooleanField(_('Registrant must have account'), widget=SwitchWidget(),
                                description=_('Registrations emails must be associated with an Indico account'))
    require_captcha = BooleanField(_('Require CAPTCHA'), widget=SwitchWidget(),
                                   description=_('When registering, users with no account have to answer a CAPTCHA'))
    limit_registrations = BooleanField(_('Limit registrations'), widget=SwitchWidget(),
                                       description=_('Whether there is a limit of registrations'))
    registration_limit = IntegerField(_('Capacity'), [HiddenUnless('limit_registrations'), DataRequired(),
                                                      NumberRange(min=1)],
                                      description=_('Maximum number of registrations'))
    modification_mode = IndicoEnumSelectField(_('Modification allowed'), enum=ModificationMode,
                                              description=_('Will users be able to modify their data? When?'))
    publish_registration_count = BooleanField(_('Publish number of registrations'), widget=SwitchWidget(),
                                              description=_('Number of registered participants will be displayed on '
                                                            'the event page'))
    publish_checkin_enabled = BooleanField(_('Publish check-in status'), widget=SwitchWidget(),
                                           description=_('Check-in status will be shown publicly on the event page'))
    base_price = DecimalField(_('Registration fee'), [NumberRange(min=0, max=999999999.99), Optional(),
                              _check_if_payment_required], filters=[lambda x: x if x is not None else 0],
                              widget=NumberInput(step='0.01'),
                              description=_('A fixed fee all users have to pay when registering.'))
    currency = SelectField(_('Currency'), [DataRequired()], description=_('The currency for new registrations'))
    notification_sender_address = StringField(_('Notification sender address'), [IndicoEmail()],
                                              filters=[lambda x: (x or None)])
    message_pending = TextAreaField(
        _('Message for pending registrations'),
        description=_('Text included in emails sent to pending registrations (Markdown syntax)')
    )
    message_unpaid = TextAreaField(
        _('Message for unpaid registrations'),
        description=_('Text included in emails sent to unpaid registrations (Markdown syntax)')
    )
    message_complete = TextAreaField(
        _('Message for complete registrations'),
        description=_('Text included in emails sent to complete registrations (Markdown syntax)')
    )
    attach_ical = BooleanField(
        _('Attach iCalendar file'),
        widget=SwitchWidget(),
        description=_('Attach an iCalendar file to the mail sent once a registration is complete')
    )
    manager_notifications_enabled = BooleanField(_('Enabled'), widget=SwitchWidget(),
                                                 description=_('Enable notifications to managers about registrations'))
    manager_notification_recipients = EmailListField(_('List of recipients'),
                                                     [HiddenUnless('manager_notifications_enabled',
                                                                   preserve_data=True), DataRequired()],
                                                     description=_('Email addresses that will receive notifications'))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        self.regform = kwargs.pop('regform', None)
        super().__init__(*args, **kwargs)
        self._set_currencies()
        self.notification_sender_address.description = _('Email address set as the sender of all '
                                                         'notifications sent to users. If empty, '
                                                         'then {email} is used.').format(email=config.NO_REPLY_EMAIL)

    def _set_currencies(self):
        currencies = [(c['code'], f'{c["code"]} ({c["name"]})') for c in payment_settings.get('currencies')]
        self.currency.choices = sorted(currencies, key=lambda x: x[1].lower())


class RegistrationFormCreateForm(IndicoForm):
    _meeting_fields = ('visibility', 'retention_period')  # The meeting regform has a default title
    _conference_fields = ('title', 'visibility', 'retention_period')
    title = StringField(_('Title'), [DataRequired()], description=_('The title of the registration form'))
    visibility = IndicoParticipantVisibilityField(_('Participant list visibility'),
                                                  description=_('Specify under which conditions the participant list '
                                                                'will be visible to other participants and everyone '
                                                                'else who can access the event'))
    retention_period = TimeDeltaField(_('Retention period'), [DataRetentionPeriodValidator()], units=('weeks',),
                                      description=_('Specify for how many weeks the registration '
                                                    'data, including the participant list, should be stored. '
                                                    'Retention periods for individual fields can be set in the '
                                                    'registration form designer'),
                                      render_kw={'placeholder': _('Indefinite')})

    def __init__(self, *args, **kwargs):
        minimum_retention = data_retention_settings.get('minimum_data_retention') or timedelta(days=7)
        maximum_retention = data_retention_settings.get('maximum_data_retention')
        if maximum_retention:
            inject_validators(self, 'retention_period', [DataRequired()])
        super().__init__(*args, **kwargs)
        maximum_retention = maximum_retention or timedelta(days=3650)
        self.visibility.max_visibility_period = maximum_retention.days // 7
        self.retention_period.render_kw.update({'min': minimum_retention.days // 7,
                                                'max': maximum_retention.days // 7})

    def validate_visibility(self, field):
        participant_visibility, public_visibility = (PublishRegistrationsMode[v] for v in field.data[:-1])
        if participant_visibility.value < public_visibility.value:
            raise ValidationError(_('Participant visibility cannot be more restrictive for other participants than '
                                    'for the public'))
        if field.data[2] is not None:
            visibility_duration = timedelta(weeks=field.data[2])
            max_retention_period = data_retention_settings.get('maximum_data_retention') or timedelta(days=3650)
            if visibility_duration <= timedelta():
                raise ValidationError(_('The visibility duration cannot be zero.'))
            elif visibility_duration > max_retention_period:
                msg = ngettext('The visibility duration cannot be longer than {} week. Leave the field empty for '
                               'indefinite.',
                               'The visibility duration cannot be longer than {} weeks. Leave the field empty for '
                               'indefinite.', max_retention_period.days // 7)
                raise ValidationError(msg.format(max_retention_period.days // 7))

    def validate_retention_period(self, field):
        retention_period = field.data
        if retention_period is None:
            return
        visibility_duration = (timedelta(weeks=self.visibility.data[2]) if self.visibility.data[2] is not None
                               else None)
        if visibility_duration and visibility_duration > retention_period:
            raise ValidationError(_('The retention period cannot be lower than the visibility duration.'))


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


class InvitationFormBase(IndicoForm):
    _invitation_fields = ('skip_moderation', 'skip_access_check')
    _email_fields = ('email_from', 'email_subject', 'email_body')
    email_from = SelectField(_('From'), [DataRequired()])
    email_subject = StringField(_('Email subject'), [DataRequired()])
    email_body = TextAreaField(_('Email body'), [DataRequired(), NoRelativeURLs()],
                               widget=TinyMCEWidget(absolute_urls=True))
    skip_moderation = BooleanField(_('Skip moderation'), widget=SwitchWidget(),
                                   description=_("If enabled, the user's registration will be approved automatically."))
    skip_access_check = BooleanField(_('Skip access check'), widget=SwitchWidget(),
                                     description=_('If enabled, the user will be able to register even if the event '
                                                   'is access-restricted.'))

    def __init__(self, *args, **kwargs):
        self.regform = kwargs.pop('regform')
        event = self.regform.event
        super().__init__(*args, **kwargs)
        if not self.regform.moderation_enabled:
            del self.skip_moderation
        self.email_from.choices = list(event.get_allowed_sender_emails().items())
        self.email_body.description = render_placeholder_info('registration-invitation-email', invitation=None)

    def validate_email_body(self, field):
        missing = get_missing_placeholders('registration-invitation-email', field.data, invitation=None)
        if missing:
            raise ValidationError(_('Missing placeholders: {}').format(', '.join(missing)))


class InvitationFormNew(InvitationFormBase):
    _invitation_fields = ('first_name', 'last_name', 'email', 'affiliation', *InvitationFormBase._invitation_fields)
    first_name = StringField(_('First name'), [DataRequired()],
                             description=_('The first name of the user you are inviting.'))
    last_name = StringField(_('Last name'), [DataRequired()],
                            description=_('The last name of the user you are inviting.'))
    email = EmailField(_('Email'), [DataRequired(), Email()], filters=[lambda x: x.lower() if x else x],
                       description=_('The invitation will be sent to this address.'))
    affiliation = StringField(_('Affiliation'),
                              description=_('The affiliation of the user you are inviting.'))

    @generated_data
    def users(self):
        return [{'first_name': self.first_name.data,
                 'last_name': self.last_name.data,
                 'email': self.email.data,
                 'affiliation': self.affiliation.data}]

    def validate_email(self, field):
        if RegistrationInvitation.query.filter_by(email=field.data).with_parent(self.regform).has_rows():
            raise ValidationError(_('There is already an invitation with this email address.'))
        if Registration.query.filter_by(email=field.data, is_active=True).with_parent(self.regform).has_rows():
            raise ValidationError(_('There is already a registration with this email address.'))


class InvitationFormExisting(InvitationFormBase):
    _invitation_fields = ('users_field', *InvitationFormBase._invitation_fields)
    users_field = PrincipalListField(_('Users'), [DataRequired()], allow_external_users=True,
                                     description=_('Select the users to invite.'))

    @generated_data
    def users(self):
        return [{'first_name': x.first_name,
                 'last_name': x.last_name,
                 'email': x.email.lower(),
                 'affiliation': x.affiliation}
                for x in self.users_field.data]

    def validate_users_field(self, field):
        emails = {x.email.lower() for x in field.data}
        # invitations
        existing = {x.email for x in self.regform.invitations} & emails
        if existing:
            raise ValidationError(_('There are already invitations for the following email addresses: {emails}')
                                  .format(emails=', '.join(sorted(existing))))
        # registrations
        existing = {x.email for x in self.regform.registrations if x.is_active} & emails
        if existing:
            raise ValidationError(_('There are already registrations with the following email addresses: {emails}')
                                  .format(emails=', '.join(sorted(existing))))


class CSVFieldDelimiter(RichStrEnum):
    __titles__ = {
        'comma': _('Comma'),
        'semicolon': _('Semicolon'),
        'tab': _('Tab'),
        'space': _('Space')
    }
    __delimiters__ = {
        'comma': ',',
        'semicolon': ';',
        'tab': '\t',
        'space': ' ',
    }

    comma = auto()
    semicolon = auto()
    tab = auto()
    space = auto()

    @property
    def delimiter(self):
        return self.__delimiters__[self.name]


class ImportInvitationsForm(InvitationFormBase):
    _invitation_fields = ('source_file', 'delimiter', 'skip_existing', *InvitationFormBase._invitation_fields)
    source_file = FileField(_('Source File'), [DataRequired(_('You need to upload a CSV file.'))],
                            accepted_file_types='.csv')
    delimiter = IndicoEnumSelectField(_('CSV field delimiter'), enum=CSVFieldDelimiter,
                                      default=CSVFieldDelimiter.comma)
    skip_existing = BooleanField(_('Skip existing invitations'), widget=SwitchWidget(), default=False,
                                 description=_('If enabled, users with existing invitations will be ignored.'))


class EmailRegistrantsForm(IndicoForm):
    from_address = SelectField(_('From'), [DataRequired()])
    cc_addresses = EmailListField(_('CC'),
                                  description=_('Beware, addresses in this field will receive one mail per '
                                                'registrant.'))
    subject = StringField(_('Subject'), [DataRequired()])
    body = TextAreaField(_('Email body'), [DataRequired(), NoRelativeURLs()], widget=TinyMCEWidget(absolute_urls=True))
    recipients = IndicoEmailRecipientsField(_('Recipients'))
    copy_for_sender = BooleanField(_('Send copy to me'), widget=SwitchWidget(),
                                   description=_('Send copy of each email to my mailbox'))
    attach_ticket = BooleanField(_('Attach ticket'), widget=SwitchWidget(),
                                 description=_('Attach tickets to emails'))
    registration_id = HiddenFieldList()
    submitted = HiddenField()

    def __init__(self, *args, **kwargs):
        self.regform = kwargs.pop('regform')
        event = self.regform.event
        super().__init__(*args, **kwargs)
        self.from_address.choices = list(event.get_allowed_sender_emails().items())
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

    add = IndicoMultipleTagSelectField(_('Add'), description=_('Select tags to assign'))
    remove = IndicoMultipleTagSelectField(_('Remove'), description=_('Select tags to remove'))
    registration_id = HiddenFieldList()
    submitted = HiddenField()

    def validate_remove(self, field):
        if set(self.remove.data) & set(self.add.data):
            raise ValidationError(_('You cannot add and remove the same tag'))

    validate_add = validate_remove

    def is_submitted(self):
        return super().is_submitted() and 'submitted' in request.form


class RegistrationPrivacyForm(IndicoForm):
    """Form to set the privacy settings of a registration form."""

    visibility = IndicoParticipantVisibilityField(_('Participant list visibility'),
                                                  description=_('Specify under which conditions the participant list '
                                                                'will be visible to other participants and everyone '
                                                                'else who can access the event'))
    retention_period = TimeDeltaField(_('Retention period'), [DataRetentionPeriodValidator()], units=('weeks',),
                                      description=_('Specify for how many weeks the registration '
                                                    'data, including the participant list, should be stored. '
                                                    'Retention periods for individual fields can be set in the '
                                                    'registration form designer'),
                                      render_kw={'placeholder': _('Indefinite')})
    require_privacy_policy_agreement = BooleanField(_('Privacy policy'), widget=SwitchWidget(),
                                                    description=_('Specify whether users are required to agree to '
                                                                  "the event's privacy policy when registering"))

    def __init__(self, *args, regform, **kwargs):
        self.regform = regform
        minimum_retention = data_retention_settings.get('minimum_data_retention') or timedelta(days=7)
        maximum_retention = data_retention_settings.get('maximum_data_retention')
        if maximum_retention:
            inject_validators(self, 'retention_period', [DataRequired()])
        super().__init__(*args, **kwargs)
        maximum_retention = maximum_retention or timedelta(days=3650)
        self.visibility.max_visibility_period = maximum_retention.days // 7
        self.retention_period.render_kw.update({'min': minimum_retention.days // 7,
                                                'max': maximum_retention.days // 7})

    @generated_data
    def publish_registrations_participants(self):
        return PublishRegistrationsMode[self.visibility.data[0]]

    @generated_data
    def publish_registrations_public(self):
        return PublishRegistrationsMode[self.visibility.data[1]]

    @generated_data
    def publish_registrations_duration(self):
        return timedelta(weeks=self.visibility.data[2]) if self.visibility.data[2] is not None else None

    @property
    def data(self):
        data = super().data
        del data['visibility']
        return data

    def validate_visibility(self, field):
        participant_visibility, public_visibility = (PublishRegistrationsMode[v] for v in field.data[:-1])
        if participant_visibility.value < public_visibility.value:
            raise ValidationError(_('Participant visibility cannot be more restrictive for other participants than '
                                    'for the public'))
        participant_visibility_changed_to_show_all = (
            participant_visibility == PublishRegistrationsMode.show_all and
            self.regform.publish_registrations_participants != PublishRegistrationsMode.show_all
        )
        public_visibility_changed_to_show_all = (
            public_visibility == PublishRegistrationsMode.show_all and
            self.regform.publish_registrations_public != PublishRegistrationsMode.show_all
        )
        if (
            self.regform and
            (participant_visibility_changed_to_show_all or public_visibility_changed_to_show_all) and
            Registration.query.with_parent(self.regform).filter(~Registration.is_deleted,
                                                                ~Registration.created_by_manager).has_rows()
        ):
            raise ValidationError(_("'Show all participants' can only be set if there are no registered users."))
        if field.data[2] is not None:
            visibility_duration = timedelta(weeks=field.data[2])
            max_retention_period = data_retention_settings.get('maximum_data_retention') or timedelta(days=3650)
            if visibility_duration < timedelta():
                raise ValidationError(_('The visibility duration cannot be zero.'))
            elif visibility_duration > max_retention_period:
                raise ValidationError(ngettext('The visibility duration cannot be longer than {} week. Leave the '
                                               'field empty for indefinite.',
                                               'The visibility duration cannot be longer than {} weeks. Leave the '
                                               'field empty for indefinite.', max_retention_period.days // 7)
                                      .format(max_retention_period.days // 7))

    def validate_retention_period(self, field):
        retention_period = field.data
        if retention_period is None:
            return
        visibility_duration = (timedelta(weeks=self.visibility.data[2]) if self.visibility.data[2] is not None
                               else None)
        if visibility_duration and visibility_duration > retention_period:
            raise ValidationError(_('The retention period cannot be lower than the visibility duration.'))
        fields = (RegistrationFormItem.query
                  .with_parent(self.regform)
                  .filter(RegistrationFormItem.is_enabled,
                          ~RegistrationFormItem.is_deleted,
                          RegistrationFormItem.retention_period.isnot(None),
                          RegistrationFormItem.retention_period > retention_period)
                  .all())

        if fields:
            raise ValidationError(_('The retention period of the whole form cannot be lower than '
                                    'that of individual fields.'))


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
