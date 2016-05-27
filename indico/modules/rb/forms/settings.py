# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from wtforms.fields.core import IntegerField, BooleanField
from wtforms.validators import InputRequired, NumberRange

from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import EmailListField, PrincipalListField
from indico.util.i18n import _


class SettingsForm(IndicoForm):
    admin_principals = PrincipalListField(_(u'Administrators'), groups=True)
    authorized_principals = PrincipalListField(_(u'Authorized users/groups'), groups=True)
    assistance_emails = EmailListField(_(u'Assistance email addresses (one per line)'))
    notification_hour = IntegerField(_(u'Hour at which booking reminders should be sent'),
                                     [InputRequired(), NumberRange(0, 23)])
    notification_before_days = IntegerField(_(u'Send booking reminders X days before'),
                                            [InputRequired(), NumberRange(min=1, max=9)])
    notifications_enabled = BooleanField(_(u'Reminders enabled'))
    vc_support_emails = EmailListField(_(u'Videoconference support email addresses (one per line)'))
