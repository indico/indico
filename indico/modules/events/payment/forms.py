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

from wtforms.fields.core import SelectField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, ValidationError

from indico.modules.events.payment import payment_settings
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import MultipleItemsField


CURRENCY_CODE_LINK = 'http://en.wikipedia.org/wiki/ISO_4217#Active_codes'
CONDITIONS_DESC = _('The registrant must agree to these conditions before paying. When left empty, no confirmation '
                    'prompt is shown to the user.')


class AdminSettingsForm(IndicoForm):
    currencies = MultipleItemsField(_('Currencies'), [DataRequired()],
                                    fields=[{'id': 'code', 'caption': _('Code')},
                                            {'id': 'name', 'caption': _('Name')}],
                                    unique_field='code',
                                    description=_("List of currencies that can be selected for an event. When deleting "
                                                  "a currency, existing events will keep using it. The currency code "
                                                  "must be a valid <a href='{0}'>ISO-4217</a> code such "
                                                  "as 'EUR' or 'CHF'.").format(CURRENCY_CODE_LINK))
    currency = SelectField(_('Currency'), [DataRequired()],
                           description=_('The default currency for new events. If you add a new currency, you need to '
                                         'save the settings first for it to show up here.'))
    conditions = TextAreaField(_('Conditions'), description=CONDITIONS_DESC)

    def __init__(self, *args, **kwargs):
        super(AdminSettingsForm, self).__init__(*args, **kwargs)
        self._set_currencies()

    def _set_currencies(self):
        currencies = [(c['code'], '{0[code]} ({0[name]})'.format(c)) for c in payment_settings.get('currencies')]
        self.currency.choices = sorted(currencies, key=lambda x: x[1].lower())

    def validate_currency(self, field):
        if field.data not in {c['code'] for c in self.currencies.data}:
            raise ValidationError('Please select a different currency.')


class EventSettingsForm(IndicoForm):
    conditions = TextAreaField(_('Conditions'), description=CONDITIONS_DESC, render_kw={'rows': 10})
