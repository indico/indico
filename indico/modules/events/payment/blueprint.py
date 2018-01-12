# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.modules.events.payment.controllers import (RHPaymentAdminPluginSettings, RHPaymentAdminSettings,
                                                       RHPaymentCheckout, RHPaymentConditions, RHPaymentForm,
                                                       RHPaymentPluginEdit, RHPaymentSettings, RHPaymentSettingsEdit)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('payment', __name__, template_folder='templates', virtual_template_folder='events/payment')

# Admin
_bp.add_url_rule('/admin/payment/', 'admin_settings', RHPaymentAdminSettings, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/payment/<plugin>/', 'admin_plugin_settings', RHPaymentAdminPluginSettings,
                 methods=('GET', 'POST'))

# Event management
_bp.add_url_rule('/event/<confId>/manage/payments/', 'event_settings', RHPaymentSettings)
_bp.add_url_rule('/event/<confId>/manage/payments/settings',
                 'event_settings_edit', RHPaymentSettingsEdit, methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/manage/payments/method/<method>',
                 'event_plugin_edit', RHPaymentPluginEdit, methods=('GET', 'POST'))

# Event
_bp.add_url_rule('/event/<confId>/registrations/<int:reg_form_id>/checkout/',
                 'event_payment', RHPaymentCheckout, methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/registrations/<int:reg_form_id>/checkout/form',
                 'event_payment_form', RHPaymentForm)
_bp.add_url_rule('/event/<confId>/payment/conditions', 'event_payment_conditions', RHPaymentConditions)
