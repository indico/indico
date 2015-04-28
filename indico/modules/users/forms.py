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

from operator import itemgetter

from flask import render_template, request
from pytz import all_timezones
from wtforms.fields.core import SelectField, BooleanField, StringField
from wtforms.fields.html5 import EmailField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, StopValidation, ValidationError
from wtforms.widgets import TextInput, TextArea
from wtforms.widgets.core import HTMLString

from indico.core.auth import multipass
from indico.modules.users import User
from indico.modules.users.models.emails import UserEmail
from indico.modules.users.models.users import UserTitle
from indico.util.i18n import _, get_all_locales
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoEnumSelectField
from indico.web.forms.widgets import SwitchWidget


class SyncedInputWidget(object):
    """Renders a text input with a sync button when needed."""

    @property
    def single_line(self):
        return not self.textarea

    def __init__(self, textarea=False):
        self.textarea = textarea
        self.default_widget = TextArea() if textarea else TextInput()

    def __call__(self, field, **kwargs):
        # Render a sync button for fields which can be synced, if the identity provider provides a value for the field.
        if field.short_name in multipass.synced_fields and field.synced_value is not None:
            return HTMLString(render_template('forms/synced_input_widget.html', field=field, textarea=self.textarea,
                                              kwargs=kwargs))
        else:
            return self.default_widget(field, **kwargs)


def _used_if_not_synced(form, field):
    """Validator to prevent validation error on synced inputs.

    Synced inputs are disabled in the form and don't send any value.
    In that case, we disable validation from the input.
    """
    if field.short_name in form.synced_fields:
        field.errors[:] = []
        raise StopValidation()


class UserDetailsForm(IndicoForm):
    title = IndicoEnumSelectField(_('Title'), enum=UserTitle)
    first_name = StringField(_('First Name'), [_used_if_not_synced, DataRequired()], widget=SyncedInputWidget())
    last_name = StringField(_('Family name'), [_used_if_not_synced, DataRequired()], widget=SyncedInputWidget())
    affiliation = StringField(_('Affiliation'), widget=SyncedInputWidget())
    address = TextAreaField(_('Address'), widget=SyncedInputWidget(textarea=True))
    phone = StringField(_('Phone number'), widget=SyncedInputWidget())

    def __init__(self, *args, **kwargs):
        synced_fields = kwargs.pop('synced_fields')
        synced_values = kwargs.pop('synced_values')
        super(UserDetailsForm, self).__init__(*args, **kwargs)
        if self.is_submitted():
            synced_fields = self.synced_fields
        provider = multipass.sync_provider
        provider_name = provider.title if provider is not None else 'unknown identity provider'
        for field in multipass.synced_fields:
            self[field].synced = self[field].short_name in synced_fields
            self[field].synced_value = synced_values.get(field)
            self[field].provider_name = provider_name

    @property
    def synced_fields(self):
        """The fields which are set as synced for the current request."""
        return set(request.form.getlist('synced_fields'))


class UserPreferencesForm(IndicoForm):
    lang = SelectField(_('Language'))
    timezone = SelectField(_('Timezone'))
    force_timezone = BooleanField(_('Use my timezone'),
                                  widget=SwitchWidget(),
                                  description='Always use my current timezone instead of an event\'s timezone.')
    show_past_events = BooleanField(_('Show past events'),
                                    widget=SwitchWidget(),
                                    description='Show past events by default.')

    def __init__(self, *args, **kwargs):
        super(UserPreferencesForm, self).__init__(*args, **kwargs)
        self.lang.choices = sorted(get_all_locales().items(), key=itemgetter(1))
        self.timezone.choices = zip(all_timezones, all_timezones)


class UserEmailsForm(IndicoForm):
    email = EmailField(_('Add new email address'), [DataRequired()], filters=[lambda x: x.lower() if x else x])

    def validate_email(self, field):
        if UserEmail.find(~User.is_pending, is_user_deleted=False, email=field.data, _join=User).count():
            raise ValidationError(_('This email address is already in use.'))


class SearchForm(IndicoForm):
    last_name = StringField(_('Family name'))
    first_name = StringField(_('First name'))
    email = EmailField(_('Email'), filters=[lambda x: x.lower() if x else x])
    affiliation = StringField(_('Affiliation'))
    exact = BooleanField(_('Exact match'))
    include_deleted = BooleanField(_('Include deleted'))
    include_pending = BooleanField(_('Include pending'))
    external = BooleanField(_('External'))
