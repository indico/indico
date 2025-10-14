# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
from datetime import timedelta

from wtforms.fields import BooleanField, DecimalField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional, ValidationError
from wtforms.widgets import NumberInput, html_params

from indico.core.config import config
from indico.modules.events import Event
from indico.modules.events.features.util import is_feature_enabled
from indico.modules.events.payment import payment_settings
from indico.modules.events.registration.models.registrations import PublishRegistrationsMode, Registration
from indico.modules.events.settings import data_retention_settings
from indico.modules.formify.fields.regform import RegformField
from indico.modules.formify.models.forms import ModificationMode
from indico.modules.formify.models.items import RegistrationFormItem
from indico.util.i18n import _, ngettext
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.fields import EmailListField, IndicoEnumSelectField
from indico.web.forms.fields.datetime import TimeDeltaField
from indico.web.forms.fields.simple import IndicoParticipantVisibilityField
from indico.web.forms.util import inject_validators
from indico.web.forms.validators import DataRetentionPeriodValidator, HiddenUnless, IndicoEmail
from indico.web.forms.widgets import SwitchWidget


def _check_if_payment_required(form, field):
    if not field.data:
        return
    if not is_feature_enabled(form.event, 'payment'):
        raise ValidationError(_('You have to enable the payment feature in order to set a registration fee.'))


def _generate_preview_link(text, input_selector, state, url, title):
    inner = _('Preview')
    params = {
        'data-ajax-dialog': True,
        'data-href': url,
        'data-method': 'POST',
        'data-title': title,
        'data-params-selector': json.dumps({'message': input_selector}),
        'data-params': json.dumps({'state': state}),
    }
    return f'{text} <a {html_params(**params)}>{inner}</a>'


class RegistrationFormEditForm(IndicoForm):
    _price_fields = ('currency', 'base_price')
    _registrant_notification_fields = ('notification_sender_address', 'message_pending', 'message_unpaid',
                                       'message_complete', 'attach_ical')
    _organizer_notification_fields = ('organizer_notifications_enabled', 'organizer_notification_recipients')
    _special_fields = _price_fields + _registrant_notification_fields + _organizer_notification_fields

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
    message_pending = TextAreaField(_('Message for pending registrations'),
        description=_('Text included in emails sent to pending registrations (Markdown syntax).'))
    # TODO: come back to previewing the email when the registration form is not linked to an event
    # for now just adding the description
    message_unpaid = TextAreaField(_('Message for unpaid registrations'),
        description=_('Text included in emails sent to unpaid registrations (Markdown syntax).'))
    message_complete = TextAreaField(_('Message for complete registrations'),
        description=_('Text included in emails sent to complete registrations (Markdown syntax).'))
    attach_ical = BooleanField(
        _('Attach iCalendar file'),
        widget=SwitchWidget(),
        description=_('Attach an iCalendar file to the mail sent once a registration is complete')
    )
    organizer_notifications_enabled = BooleanField(
        _('Enabled'),
        widget=SwitchWidget(),
        description=_('Enable e-mail notifications about registrations to organizers'),
    )
    organizer_notification_recipients = EmailListField(
        _('List of recipients'),
        [HiddenUnless('organizer_notifications_enabled', preserve_data=True), DataRequired()],
        description=_('Email addresses that will receive notifications'),
    )

    def __init__(self, *args, **kwargs):
        target = kwargs.pop('target')
        self.event = target if isinstance(target, Event) else None
        self.regform = kwargs.pop('regform', None)
        super().__init__(*args, **kwargs)
        self._set_currencies()
        if self.event:
            self._set_links()
        self.notification_sender_address.description = _('Email address set as the sender of all '
                                                         'notifications sent to users. If empty, '
                                                         'then {email} is used.').format(email=config.NO_REPLY_EMAIL)

    def _set_currencies(self):
        currencies = [(c['code'], f'{c["code"]} ({c["name"]})') for c in payment_settings.get('currencies')]
        self.currency.choices = sorted(currencies, key=lambda x: x[1].lower())

    def _set_links(self):
        url = url_for('event_registration.notification_preview', self.regform)
        self.message_pending.description = _generate_preview_link(
            _('Text included in emails sent to pending registrations (Markdown syntax).'),
            '#message_pending', 'pending', url, _('Pending Registration Preview')
        )
        self.message_unpaid.description = _generate_preview_link(
            _('Text included in emails sent to unpaid registrations (Markdown syntax).'),
            '#message_unpaid', 'unpaid', url, _('Unpaid Registration Preview')
        )
        self.message_complete.description = _generate_preview_link(
            _('Text included in emails sent to complete registrations (Markdown syntax).'),
            '#message_complete', 'complete', url, _('Complete Registration Preview')
        )


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


class RegistrationFormCreateFromTemplateForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()], description=_('The title of the registration form'))
    create_from = RegformField(_('Registration form'), [DataRequired()],
                              description=_('Available template registration forms'),
                              ajax_endpoint='event_registration.regform_template_list')

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')  # Is used by the RegformField
        super().__init__(*args, **kwargs)
