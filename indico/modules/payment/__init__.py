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

from indico.core.models.settings import SettingsProxy, EventSettingsProxy
from indico.modules.payment.plugins import (PaymentPluginMixin, PaymentPluginSettingsFormBase,
                                            PaymentEventSettingsFormBase)
from indico.util.i18n import _


__all__ = ('settings', 'event_settings', 'PaymentPluginMixin', 'PaymentPluginSettingsFormBase',
           'PaymentEventSettingsFormBase')

CONDITIONS = ("CANCELLATION:\n"
              "All refunds requests must be in writing by mail to the Conference Secretary as soon as possible.\n"
              "The Conference committee reserves the right to refuse reimbursement of part or all of the fee in the"
              "case of late cancellation. However, each case of cancellation would be considered individually.")


settings = SettingsProxy('payment', {
    'currencies': [{'code': 'EUR', 'name': 'Euro'}, {'code': 'USD', 'name': 'US Dollar'}],
    'currency': 'EUR',
    'conditions': CONDITIONS,
    'summary_email': '',
    'success_email': ''
})

event_settings = EventSettingsProxy('payment', {
    'enabled': False,
    'currency': 'EUR',
    'conditions': '',
    'summary_email': '',
    'success_email': ''
})
