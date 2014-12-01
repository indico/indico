# This file is part of Indico.
# Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

from wtforms.fields.core import SelectField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, ValidationError

from indico.modules.payment import settings
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import MultipleItemsField


CURRENCY_CODE_LINK = 'http://en.wikipedia.org/wiki/ISO_4217#Active_codes'
CONDITIONS_DESC = _('The registrant must agree to these conditions before paying. When left empty, no confirmation '
                    'prompt is shown to the user.')
SUMMARY_EMAIL_DESC = _('Custom message included in the payment summary email.')
SUCCESS_EMAIL_DESC = _('Custom message included in the email after successful payment.')
EMAIL_DISABLED_MSG = _('This email is currently <strong>disabled</strong>. You can enable it in the '
                       '<a href="{0}">registration form setup</a>.')
EMAIL_ENABLED_MSG = _('This email is currently <strong>enabled</strong>. You can disable it in the '
                      '<a href="{0}">registration form setup</a>.')


class AdminSettingsForm(IndicoForm):
    currencies = MultipleItemsField(_('Currencies'), [DataRequired()],
                                    fields=(('code', _('Code')), ('name', _('Name'))),
                                    description=_("List of currencies that can be selected for an event. When deleting "
                                                  "a currency, existing events will keep using it. The currency code "
                                                  "must be a valid <a href='{0}'>ISO-4217</a> code such "
                                                  "as 'EUR' or 'CHF'.").format(CURRENCY_CODE_LINK))
    currency = SelectField(_('Currency'), [DataRequired()],
                           description=_('The default currency for new events. If you add a new currency, you need to '
                                         'save the settings first for it to show up here.'))
    conditions = TextAreaField(_('Conditions'), description=CONDITIONS_DESC)
    summary_email = TextAreaField(_('Summary email message'), description=SUMMARY_EMAIL_DESC)
    success_email = TextAreaField(_('Success email message'), description=SUCCESS_EMAIL_DESC)

    def __init__(self, *args, **kwargs):
        super(AdminSettingsForm, self).__init__(*args, **kwargs)
        self._set_currencies()

    def _set_currencies(self):
        currencies = [(c['code'], '{0[code]} ({0[name]})'.format(c)) for c in settings.get('currencies')]
        self.currency.choices = sorted(currencies, key=lambda x: x[1].lower())

    def validate_currency(self, field):
        if field.data not in {c['code'] for c in self.currencies.data}:
            raise ValidationError('Please select a different currency.')


class EventSettingsForm(IndicoForm):
    currency = SelectField(_('Currency'), [DataRequired()])
    conditions = TextAreaField(_('Conditions'), description=CONDITIONS_DESC)
    summary_email = TextAreaField(_('Summary email message'), description=SUMMARY_EMAIL_DESC)
    success_email = TextAreaField(_('Success email message'), description=SUCCESS_EMAIL_DESC)

    def __init__(self, *args, **kwargs):
        self._event = kwargs.pop('event')
        super(EventSettingsForm, self).__init__(*args, **kwargs)
        self._include_email_status()
        self._set_currencies()

    def _include_email_status(self):
        regform = self._event.getRegistrationForm()
        regform_setup_url = url_for('event_mgmt.confModifRegistrationForm-dataModif', self._event)
        summary_status = (EMAIL_ENABLED_MSG if regform.isSendReceiptEmail()
                          else EMAIL_DISABLED_MSG).format(regform_setup_url)
        success_status = (EMAIL_ENABLED_MSG if regform.isSendPaidEmail()
                          else EMAIL_DISABLED_MSG).format(regform_setup_url)
        self.summary_email.description += '<br>' + summary_status
        self.success_email.description += '<br>' + success_status

    def _set_currencies(self):
        currencies = [(c['code'], '{0[code]} ({0[name]})'.format(c)) for c in settings.get('currencies')]
        # In case the event's currency was deleted, we keep it here anyway.
        event_currency = self.currency.object_data
        if event_currency and not any(x[0] == event_currency for x in currencies):
            currencies.append((event_currency, event_currency))
        self.currency.choices = sorted(currencies, key=lambda x: x[1].lower())
