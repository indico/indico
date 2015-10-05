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

from indico.modules.payment.controllers import (RHPaymentAdminSettings, RHPaymentEventSettings,
                                                RHPaymentEventToggle, RHPaymentEventSettingsEdit,
                                                RHPaymentEventPluginEdit, RHPaymentEventCheckout, RHPaymentEventForm,
                                                RHPaymentAdminPluginSettings, RHPaymentEventConditions)
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('payment', __name__, template_folder='templates', virtual_template_folder='payment')

# Admin
_bp.add_url_rule('/admin/payment/', 'admin_settings', RHPaymentAdminSettings, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/payment/<plugin>/', 'admin_plugin_settings', RHPaymentAdminPluginSettings,
                 methods=('GET', 'POST'))

# Event management
_bp.add_url_rule('/event/<confId>/manage/registration/payment/', 'event_settings', RHPaymentEventSettings)
_bp.add_url_rule('/event/<confId>/manage/registration/payment/settings', 'event_settings_edit',
                 RHPaymentEventSettingsEdit, methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/manage/registration/payment/toggle', 'event_toggle', RHPaymentEventToggle,
                 methods=('POST',))
_bp.add_url_rule('/event/<confId>/manage/registration/payment/method/<method>', 'event_plugin_edit',
                 RHPaymentEventPluginEdit, methods=('GET', 'POST'))

# Event
_bp.add_url_rule('/event/<confId>/registration/payment/', 'event_payment', RHPaymentEventCheckout,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/registration/payment/form', 'event_payment_form', RHPaymentEventForm)
_bp.add_url_rule('/event/<confId>/registration/payment/conditions',
                 'event_payment_conditions', RHPaymentEventConditions)
