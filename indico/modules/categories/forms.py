# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import partial

from cryptography import hazmat, x509
from cryptography.exceptions import UnsupportedAlgorithm
from flask import request
from wtforms.fields import BooleanField, HiddenField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, Optional, ValidationError
from wtforms.widgets import TextArea

from indico.core.config import config
from indico.core.permissions import FULL_ACCESS_PERMISSION, READ_ACCESS_PERMISSION
from indico.modules.categories import logger
from indico.modules.categories.models.categories import (Category, EventCreationMode, EventMessageMode,
                                                         InheritableConfigMode)
from indico.modules.categories.models.roles import CategoryRole
from indico.modules.categories.util import get_image_data, get_visibility_options
from indico.modules.events import Event
from indico.modules.events.fields import IndicoThemeSelectField
from indico.modules.events.models.events import EventType
from indico.modules.events.registration.wallets.google import GoogleCredentialValidationResult, GoogleWalletManager
from indico.modules.networks import IPNetworkGroup
from indico.util.i18n import _
from indico.util.user import principal_from_identifier
from indico.web.forms.base import IndicoForm, generated_data
from indico.web.forms.colors import get_role_colors
from indico.web.forms.fields import (EditableFileField, EmailListField, HiddenFieldList, IndicoEnumSelectField,
                                     IndicoMarkdownField, IndicoPasswordField, IndicoProtectionField,
                                     IndicoSinglePalettePickerField, IndicoTimezoneSelectField, MultipleItemsField)
from indico.web.forms.fields.principals import PermissionsField
from indico.web.forms.fields.simple import JSONField
from indico.web.forms.validators import HiddenUnless
from indico.web.forms.widgets import HiddenCheckbox, SwitchWidget


class CategorySettingsForm(IndicoForm):
    BASIC_FIELDS = ('title', 'description', 'timezone', 'lecture_theme', 'meeting_theme', 'visibility',
                    'suggestions_disabled', 'is_flat_view_enabled', 'show_future_months',
                    'event_creation_notification_emails', 'notify_managers')
    GOOGLE_WALLET_FIELDS = ('google_wallet_mode', 'google_wallet_credentials', 'google_wallet_issuer_name',
                            'google_wallet_issuer_id')
    GOOGLE_WALLET_JSON_FIELDS = ('google_wallet_credentials', 'google_wallet_issuer_name', 'google_wallet_issuer_id')
    APPLE_WALLET_FIELDS = ('apple_wallet_mode', 'apple_wallet_certificate', 'apple_wallet_key', 'apple_wallet_password')
    APPLE_WALLET_JSON_FIELDS = ('apple_wallet_certificate', 'apple_wallet_key', 'apple_wallet_password')

    EVENT_HEADER_FIELDS = ('event_message_mode', 'event_message')

    title = StringField(_('Title'), [DataRequired()])
    description = IndicoMarkdownField(_('Description'))
    timezone = IndicoTimezoneSelectField(_('Timezone'), [DataRequired()],
                                         description=_('Default timezone event lists will show up in. It will also be '
                                                       'used as a default for new events.'))
    lecture_theme = IndicoThemeSelectField(_('Theme for Lectures'), [DataRequired()], event_type=EventType.lecture,
                                           description=_('Default timetable theme used for lecture events'))
    meeting_theme = IndicoThemeSelectField(_('Theme for Meetings'), [DataRequired()], event_type=EventType.meeting,
                                           description=_('Default timetable theme used for meeting events'))
    suggestions_disabled = BooleanField(_('Disable Suggestions'), widget=SwitchWidget(),
                                        description=_("Enable this if you don't want Indico to suggest this category as"
                                                      " a possible addition to a user's favorites."))
    is_flat_view_enabled = BooleanField(_('Allow flat view'), widget=SwitchWidget(),
                                        description=_('Allow users to view all the events descending from this '
                                                      'category in one single page. This is not recommended on large '
                                                      'categories with thousands of events.'))
    show_future_months = IntegerField(_('Future months threshold'), [NumberRange(min=0)],
                                      description=_('Events past the threshold will be hidden by default to avoid '
                                                    'clutter, the user can click to expand them. If no events are '
                                                    'found within this threshold, it is extended to show the first '
                                                    'month with events.'))
    event_message_mode = IndicoEnumSelectField(_('Message Type'), enum=EventMessageMode,
                                               default=EventMessageMode.disabled,
                                               description=_('This message will show up at the top of every event page '
                                                             'in this category'))
    event_message = IndicoMarkdownField(_('Content'))
    notify_managers = BooleanField(_('Notify managers'), widget=SwitchWidget(),
                                   description=_('Whether to send email notifications to all managers of this category '
                                                 'when an event is created inside it or in any of its subcategories.'))
    event_creation_notification_emails = EmailListField(_('Notification E-mails'),
                                                        description=_('List of emails that will receive a notification '
                                                                      'every time a new event is created inside the '
                                                                      'category or one of its subcategories. '
                                                                      'One email address per line.'))
    google_wallet_mode = IndicoEnumSelectField(_('Configuration'), enum=InheritableConfigMode,
                                               description=_('The Google Wallet configuration is, by default, '
                                                             'inherited from the parent category. You can also '
                                                             'explicitly disable it or provide your own configuration '
                                                             'instead.'))
    google_wallet_credentials = JSONField(_('Google Credentials'),
                                          [HiddenUnless('google_wallet_mode', InheritableConfigMode.enabled,
                                                        preserve_data=True),
                                           DataRequired()],
                                          empty_if_null=True,
                                          widget=TextArea(),
                                          description=_('JSON key credentials for the Google Service Account'))
    google_wallet_issuer_name = StringField(_('Issuer Name'),
                                            [HiddenUnless('google_wallet_mode', InheritableConfigMode.enabled,
                                                          preserve_data=True),
                                             DataRequired()],
                                            description=_('Issuer name that will appear in the Google Wallet ticket '
                                                          'top header. Google recommends a maximum length of 20 chars '
                                                          'to ensure readability on all devices.'))
    google_wallet_issuer_id = StringField(_('Issuer ID'),
                                          [HiddenUnless('google_wallet_mode', InheritableConfigMode.enabled,
                                                        preserve_data=True),
                                           DataRequired()],
                                          description=_('Issuer ID assigned in the "Google Pay & Wallet" console. '
                                                        'The same Issuer ID must never be used on more than one '
                                                        'Indico server. Changing it will also break updates to '
                                                        'any existing tickets.'))
    apple_wallet_mode = IndicoEnumSelectField(_('Configuration'), enum=InheritableConfigMode,
                                              description=_('The Apple Wallet configuration is, by default, '
                                                            'inherited from the parent category. You can also '
                                                            'explicitly disable it or provide your own configuration '
                                                            'instead.'))
    apple_wallet_certificate = TextAreaField(_('Certificate'),
                                             [HiddenUnless('apple_wallet_mode', InheritableConfigMode.enabled,
                                                           preserve_data=True), DataRequired()],
                                             description=_('Your certificate in PEM format'))
    apple_wallet_key = TextAreaField(_('Private Key'), [HiddenUnless('apple_wallet_mode', InheritableConfigMode.enabled,
                                                                     preserve_data=True), DataRequired()],
                                     description=_('Your private key in PEM format'))
    apple_wallet_password = IndicoPasswordField(_('Passphrase'),
                                                [HiddenUnless('apple_wallet_mode', InheritableConfigMode.enabled,
                                                              preserve_data=False)],
                                                toggle=True,
                                                description=_('The passphrase used to decrypt the private key. Leave '
                                                              'this empty if the private key is not encrypted.'))

    def __init__(self, *args, category, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category
        self._set_google_wallet_fields()
        self._set_apple_wallet_fields()

    def _set_google_wallet_fields(self):
        if not config.ENABLE_GOOGLE_WALLET:
            for field in list(self):
                if field.name.startswith('google_wallet_'):
                    delattr(self, field.name)
        elif self.category.parent:
            parent_configured = self.category.parent.effective_google_wallet_config is not None
            self.google_wallet_mode.titles = InheritableConfigMode.get_form_field_titles(parent_configured)
        else:
            self.google_wallet_mode.skip = {InheritableConfigMode.inheriting}

    def _set_apple_wallet_fields(self):
        if not config.ENABLE_APPLE_WALLET:
            for field in list(self):
                if field.name.startswith('apple_wallet_'):
                    delattr(self, field.name)
        elif self.category.parent:
            parent_configured = self.category.parent.effective_apple_wallet_config is not None
            self.apple_wallet_mode.titles = InheritableConfigMode.get_form_field_titles(parent_configured)
        else:
            self.apple_wallet_mode.skip = {InheritableConfigMode.inheriting}

    def validate(self, extra_validators=None):
        form_valid = super().validate(extra_validators=extra_validators)
        if not config.ENABLE_GOOGLE_WALLET:
            return form_valid

        enabled = self.google_wallet_mode.data == InheritableConfigMode.enabled
        credentials = self.google_wallet_credentials.data
        issuer_id = self.google_wallet_issuer_id.data

        if (
            credentials and
            enabled and (
                self.category.google_wallet_settings.get('google_wallet_credentials') != credentials or
                self.category.google_wallet_settings.get('google_wallet_issuer_id') != issuer_id
            )
        ):
            res = GoogleWalletManager.verify_credentials(credentials, issuer_id)
            if res == GoogleCredentialValidationResult.invalid:
                self.google_wallet_credentials.errors.append(
                    _('The credentials could not be loaded.')
                )
                return False
            elif res == GoogleCredentialValidationResult.refused:
                self.google_wallet_credentials.errors.append(
                    _('The credentials are invalid or have no access to the Google Wallet API.')
                )
                return False
            elif res == GoogleCredentialValidationResult.failed:
                self.google_wallet_credentials.errors.append(
                    _('There was an error validating your credentials. Contact your Indico administrator for '
                      'details.')
                )
                return False
            elif res == GoogleCredentialValidationResult.bad_issuer:
                self.google_wallet_issuer_id.errors.append(
                    _('The Issuer ID is invalid or not linked to your credentials.')
                )
                return False

        return form_valid

    def validate_apple_wallet_certificate(self, field):
        try:
            x509.load_pem_x509_certificate(field.data.encode())
            return
        except ValueError:
            raise ValidationError(_('The provided certificate is malformed.'))

    def validate_apple_wallet_key(self, field):
        try:
            hazmat.primitives.serialization.load_pem_private_key(field.data.encode(), password=None)
        except ValueError:
            raise ValidationError(_('The private key is malformed.'))
        except UnsupportedAlgorithm as exc:
            logger.warning('Unsupported private key in category %d: %s', self.category.id, exc)
            raise ValidationError(_('The private key is invalid.'))
        except TypeError:
            # TypeError is raised when no password is provided for an encrypted key (or vice versa),
            # but for the check here we do not need to decrypt the key anyway
            pass

    def validate_apple_wallet_password(self, field):
        if self.apple_wallet_key.errors:
            return
        password = field.data.encode() or None
        try:
            hazmat.primitives.serialization.load_pem_private_key(self.apple_wallet_key.data.encode(),
                                                                 password=password)
        except TypeError:
            if password:
                raise ValidationError(_('The provided key is not encrypted, do not specify a password.'))
            else:
                raise ValidationError(_('The provided key is encrypted, you must specify the password to decrypt it.'))
        except ValueError:
            raise ValidationError(_('The provided password is incorrect.'))

    @generated_data
    def google_wallet_settings(self):
        if not config.ENABLE_GOOGLE_WALLET:
            return self.category.google_wallet_settings
        return {k: getattr(self, k).data for k in self.GOOGLE_WALLET_JSON_FIELDS}

    @generated_data
    def apple_wallet_settings(self):
        if not config.ENABLE_APPLE_WALLET:
            return self.category.apple_wallet_settings
        return {k: getattr(self, k).data for k in self.APPLE_WALLET_JSON_FIELDS}

    @property
    def data(self):
        return {k: v for k, v in super().data.items() if not (k in self.GOOGLE_WALLET_JSON_FIELDS or
                                                              k in self.APPLE_WALLET_JSON_FIELDS)}


class CategoryIconForm(IndicoForm):
    icon = EditableFileField('Icon', accepted_file_types='image/jpeg,image/jpg,image/png,image/gif',
                             add_remove_links=False, handle_flashes=True, get_metadata=partial(get_image_data, 'icon'),
                             description=_('Small icon that will show up next to category names in overview pages. '
                                           'Will be automatically resized to 16x16 pixels. This may involve loss of '
                                           'image quality, so try to upload images as close as possible to those '
                                           'dimensions.'))


class CategoryLogoForm(IndicoForm):
    logo = EditableFileField('Logo', accepted_file_types='image/jpeg,image/jpg,image/png,image/gif',
                             add_remove_links=False, handle_flashes=True, get_metadata=partial(get_image_data, 'logo'),
                             description=_('Logo that will show up next to the category description. Will be '
                                           'automatically resized to at most 200x200 pixels.'))


class CategoryProtectionForm(IndicoForm):
    permissions = PermissionsField(_('Permissions'), object_type='category')
    protection_mode = IndicoProtectionField(_('Protection mode'), protected_object=lambda form: form.protected_object)
    own_no_access_contact = StringField(_('No access contact'),
                                        description=_('Contact information shown when someone lacks access to the '
                                                      'category'))
    visibility = SelectField(_('Event visibility'),
                             [Optional()], coerce=lambda x: None if x == '' else int(x),  # noqa: PLC1901
                             description=_('''From which point in the category tree contents will be visible from '''
                                           '''(number of categories upwards). Applies to "Today's events" and '''
                                           '''Calendar. If the category is moved, this number will be preserved.'''))
    event_creation_mode = IndicoEnumSelectField(_('Event creation mode'), enum=EventCreationMode,
                                                default=EventCreationMode.restricted,
                                                description=_('Specify who can create events in the category and '
                                                              'whether they need to be approved. Regardless of this '
                                                              'setting, users cannot create/propose events unless they '
                                                              'have at least read access to the category.'))

    def __init__(self, *args, **kwargs):
        self.protected_object = self.category = kwargs.pop('category')
        super().__init__(*args, **kwargs)
        self._init_visibility()

    def _init_visibility(self):
        self.visibility.choices = get_visibility_options(self.category, allow_invisible=False)
        # Check if category visibility would be affected by any of the parents
        real_horizon = self.category.real_visibility_horizon
        own_horizon = self.category.own_visibility_horizon
        if real_horizon and real_horizon.is_descendant_of(own_horizon):
            self.visibility.warning = _("This category's visibility is currently limited by that of '{}'.").format(
                real_horizon.title)

    def validate_permissions(self, field):
        for principal_fossil, permissions in field.data:
            principal = principal_from_identifier(principal_fossil['identifier'],
                                                  allow_external_users=True,
                                                  allow_groups=True,
                                                  allow_networks=True,
                                                  allow_category_roles=True,
                                                  category_id=self.category.id)
            if isinstance(principal, IPNetworkGroup) and set(permissions) - {READ_ACCESS_PERMISSION}:
                msg = _('IP networks cannot have management permissions: {}').format(principal.name)
                raise ValidationError(msg)
            if FULL_ACCESS_PERMISSION in permissions and len(permissions) != 1:
                # when full access permission is set, discard rest of permissions
                permissions[:] = [FULL_ACCESS_PERMISSION]


class CreateCategoryForm(IndicoForm):
    """Form to create a new Category."""

    title = StringField(_('Title'), [DataRequired()])
    description = IndicoMarkdownField(_('Description'))


class SplitCategoryForm(IndicoForm):
    first_category = StringField(_('Category name #1'), [DataRequired()],
                                 description=_('Selected events will be moved into a new sub-category with this '
                                               'title.'))
    second_category = StringField(_('Category name #2'),
                                  description=_('Events that were not selected will be moved into a new sub-category '
                                                'with this title. If omitted, those events will remain in the current '
                                                'category.'))
    event_id = HiddenFieldList()
    all_selected = BooleanField(widget=HiddenCheckbox())
    submitted = HiddenField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.all_selected.data:
            self.event_id.data = []
            self.first_category.label.text = _('Category name')
            self.first_category.description = _('The events will be moved into a new sub-category with this title.')
            del self.second_category

    def is_submitted(self):
        return super().is_submitted() and 'submitted' in request.form


class UpcomingEventsForm(IndicoForm):
    max_entries = IntegerField(_('Max. events'), [InputRequired(), NumberRange(min=0)],
                               description=_('The maximum number of upcoming events to show. Events are sorted by '
                                             'weight so events with a lower weight are more likely to be omitted if '
                                             'there are too many events to show.'))
    entries = MultipleItemsField(_('Upcoming events'),
                                 fields=[{'id': 'type', 'caption': _('Type'), 'required': True, 'type': 'select'},
                                         {'id': 'id', 'caption': _('ID'), 'required': True, 'type': 'number',
                                          'step': 1, 'coerce': int},
                                         {'id': 'days', 'caption': _('Days'), 'required': True, 'type': 'number',
                                          'step': 1, 'coerce': int},
                                         {'id': 'weight', 'caption': _('Weight'), 'required': True, 'type': 'number',
                                          'coerce': float}],
                                 choices={'type': {'category': _('Category'),
                                                   'category_tree': _('Category & Subcategories'),
                                                   'event': _('Event')}},
                                 description=_("Specify categories/events shown in the 'upcoming events' list on the "
                                               'home page.'))

    def validate_entries(self, field):
        if field.errors:
            return
        for entry in field.data:
            if entry['days'] < 0:
                raise ValidationError(_("'Days' must be a positive integer"))
            if entry['type'] not in {'category', 'category_tree', 'event'}:
                raise ValidationError(_('Invalid type'))
            if entry['type'] in {'category', 'category_tree'} and not Category.get(entry['id'], is_deleted=False):
                raise ValidationError(_('Invalid category: {}').format(entry['id']))
            if entry['type'] == 'event' and not Event.get(entry['id'], is_deleted=False):
                raise ValidationError(_('Invalid event: {}').format(entry['id']))


class CategoryRoleForm(IndicoForm):
    name = StringField(_('Name'), [DataRequired()],
                       description=_('The full name of the role'))
    code = StringField(_('Code'), [DataRequired(), Length(max=3)], filters=[lambda x: x.upper() if x else ''],
                       render_kw={'style': 'width:60px; text-align:center; text-transform:uppercase;'},
                       description=_('A shortcut (max. 3 characters) for the role'))
    color = IndicoSinglePalettePickerField(_('Color'), color_list=get_role_colors(), text_color='ffffff',
                                           description=_('The color used when displaying the role'))

    def __init__(self, *args, **kwargs):
        self.role = kwargs.get('obj')
        self.category = kwargs.pop('category')
        super().__init__(*args, **kwargs)

    def validate_code(self, field):
        query = CategoryRole.query.with_parent(self.category).filter_by(code=field.data)
        if self.role is not None:
            query = query.filter(CategoryRole.id != self.role.id)
        if query.has_rows():
            raise ValidationError(_('A role with this code already exists.'))
