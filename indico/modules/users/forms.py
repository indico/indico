# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from operator import itemgetter

from pytz import common_timezones, common_timezones_set
from wtforms.fields import BooleanField, EmailField, IntegerField, SelectField, StringField
from wtforms.validators import DataRequired, Email, NumberRange, Optional, ValidationError

from indico.core.auth import multipass
from indico.core.config import config
from indico.modules.auth.forms import LocalRegistrationForm, _check_existing_email
from indico.modules.core.settings import social_settings
from indico.modules.users import User
from indico.modules.users.models.emails import UserEmail
from indico.modules.users.models.users import NameFormat
from indico.util.i18n import _, get_all_locales
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import (IndicoEnumSelectField, IndicoSelectMultipleCheckboxField, MultiStringField,
                                     PrincipalField, PrincipalListField)
from indico.web.forms.util import inject_validators
from indico.web.forms.validators import HiddenUnless, MastodonServer
from indico.web.forms.widgets import SwitchWidget
from indico.web.util import strip_path_from_url


class UserPreferencesForm(IndicoForm):
    lang = SelectField(_('Language'))

    force_language = BooleanField(
        _('Use my language'),
        widget=SwitchWidget(),
        description=_("Always use my preferred language instead of an event's supported language."
                      ' This may result in a mix of two languages in some areas of an event.'))

    timezone = SelectField(_('Timezone'))

    force_timezone = BooleanField(
        _('Use my timezone'),
        widget=SwitchWidget(),
        description=_("Always use my current timezone instead of an event's timezone."))

    show_future_events = BooleanField(
        _('Show future events'),
        widget=SwitchWidget(),
        description=_('Show future events by default.'))

    show_past_events = BooleanField(
        _('Show past events'),
        widget=SwitchWidget(),
        description=_('Show past events by default.'))

    name_format = IndicoEnumSelectField(_('Name format'), enum=NameFormat,
                                        description=_('Default format in which names are displayed'))

    use_previewer_pdf = BooleanField(
        _('Use previewer for PDF files'),
        widget=SwitchWidget(),
        description=_('The previewer is used by default for image and text files, but not for PDF files.'))

    add_ical_alerts = BooleanField(
        _('Add alerts to iCal'),
        widget=SwitchWidget(),
        description=_('Add an event reminder to exported iCal files/URLs.'))

    add_ical_alerts_mins = IntegerField(
        _('iCal notification time'),
        [HiddenUnless('add_ical_alerts'), NumberRange(min=0)],
        description=_('Number of minutes to notify before an event.'))

    use_markdown_for_minutes = BooleanField(
        _('Markdown editor for minutes'),
        widget=SwitchWidget(),
        description=_('Use Markdown editor instead of HTML editor when editing the minutes of a meeting.'))

    mastodon_server_url = StringField(
        _('Preferred Mastodon server'),
        validators=[MastodonServer(), Optional()],
        filters=[lambda x: strip_path_from_url(x) if x else x],
        description=_('URL of the Mastodon server you prefer to use for sharing links to events/meetings '
                      '(e.g. https://mastodon.social).'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not social_settings.get('enabled'):
            del self.mastodon_server_url
        locales = [(code, f'{name} ({territory})' if territory else name)
                   for code, (name, territory, __) in get_all_locales().items()]
        self.lang.choices = sorted(locales, key=itemgetter(1))
        self.timezone.choices = list(zip(common_timezones, common_timezones, strict=True))
        if self.timezone.object_data and self.timezone.object_data not in common_timezones_set:
            self.timezone.choices.append((self.timezone.object_data, self.timezone.object_data))


class UserEmailsForm(IndicoForm):
    email = EmailField(_('Add new email address'), [DataRequired(), Email()], filters=[lambda x: x.lower() if x else x])

    def validate_email(self, field):
        conflict = (UserEmail.query
                    .filter(~User.is_pending,
                            ~UserEmail.is_user_deleted,
                            UserEmail.email == field.data)
                    .join(User)
                    .has_rows())
        if conflict:
            raise ValidationError(_('This email address is already in use.'))


class SearchForm(IndicoForm):
    last_name = StringField(_('Family name'))
    first_name = StringField(_('First name'))
    email = StringField(_('Email'), filters=[lambda x: x.lower() if x else x])
    affiliation = StringField(_('Affiliation'))
    exact = BooleanField(_('Exact match'))
    include_deleted = BooleanField(_('Include deleted'))
    include_pending = BooleanField(_('Include pending'))
    external = BooleanField(_('External'))


class MergeForm(IndicoForm):
    source_user = PrincipalField(_('Source user'), [DataRequired()],
                                 description=_('The user that will be merged into the target one'))
    target_user = PrincipalField(_('Target user'), [DataRequired()],
                                 description=_('The user that will remain active in the end'))


class AdminUserSettingsForm(IndicoForm):
    notify_account_creation = BooleanField(_('Registration notifications'), widget=SwitchWidget(),
                                           description=_('Send an email to all administrators whenever someone '
                                                         'registers a new local account.'))
    email_blacklist = MultiStringField(_('Email blacklist'), field=('email_blacklist', _('email')),
                                       unique=True, flat=True,
                                       description=_('Prevent users from creating Indico accounts with these email '
                                                     'addresses. Supports wildcards, e.g. *@gmail.com'))
    allow_personal_tokens = BooleanField(_('Personal API tokens'), widget=SwitchWidget(),
                                         description=_('Whether users are allowed to generate personal API tokens. '
                                                       'If disabled, only admins can create them, but users will '
                                                       'still be able to regenerate the tokens assigned to them.'))
    mandatory_fields_account_request = IndicoSelectMultipleCheckboxField(
        _('Mandatory fields in account request'),
        choices=[('affiliation', _('Affiliation')), ('comment', _('Comment'))],
        description=_('Fields a new user has to fill in when requesting an account')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not multipass.has_moderated_providers:
            del self.mandatory_fields_account_request


class AdminAccountRegistrationForm(LocalRegistrationForm):
    email = EmailField(_('Email address'), [DataRequired(), Email(), _check_existing_email],
                       filters=[lambda s: s.lower() if s else s])
    create_identity = BooleanField(_('Set login details'), widget=SwitchWidget(), default=True)

    def __init__(self, *args, **kwargs):
        if config.LOCAL_IDENTITIES:
            for field in ('username', 'password', 'confirm_password'):
                inject_validators(self, field, [HiddenUnless('create_identity')], early=True)
        super().__init__(*args, **kwargs)
        if not config.LOCAL_IDENTITIES:
            del self.username
            del self.password
            del self.confirm_password
            del self.create_identity


class AdminsForm(IndicoForm):
    admins = PrincipalListField(_('Admins'), [DataRequired()])
