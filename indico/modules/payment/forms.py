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

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import MultipleItemsField


CURRENCY_CODE_LINK = 'http://en.wikipedia.org/wiki/ISO_4217#Active_codes'


class SettingsForm(IndicoForm):
    currencies = MultipleItemsField(_('Currencies'), fields=(('code', _('Code')), ('name', _('Name'))),
                                    description=_("List of currencies that can be selected for an event. When deleting "
                                                  "a currency, existing events will keep using it. The currency code "
                                                  "must be a valid <a href='{0}'>ISO-4217</a> code such "
                                                  "as 'EUR' or 'CHF'.").format(CURRENCY_CODE_LINK))
