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

from wtforms.fields import StringField, TextAreaField, BooleanField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Optional

from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoDateTimeField, EmailListField
from indico.web.forms.validators import HiddenUnless, DateTimeRange, LinkedDateTime
from indico.web.forms.widgets import SwitchWidget


class RegistrationFormForm(IndicoForm):
    _notification_fields = ('notifications_enabled', 'recipients_emails')

    title = StringField(_("Title"), [DataRequired()], description=_("The title of the registration form"))
    introduction = TextAreaField(_("Introduction"),
                                 description=_("Introduction to be displayed when filling out the registration form"))
    contact_info = StringField(_("Contact info"),
                               description=_("How registrants can get in touch with somebody for extra information"))
    moderation_enabled = BooleanField(_("Moderated"), widget=SwitchWidget(),
                                      description=_("If enabled, registrations require manager approval"))
    require_login = BooleanField(_("Only logged-in users"), widget=SwitchWidget(),
                                 description=_("Users must be logged in to register"))
    require_user = BooleanField(_("Registrant must have account"), widget=SwitchWidget(),
                                description=_("Registrations must be associated with an Indico account. "
                                              "This allows only email addresses associated with an account."))
    limit_registrations = BooleanField(_("Limit registrations"), widget=SwitchWidget(),
                                       description=_("Whether there is a limit of registrations"))
    registration_limit = IntegerField(_("Capacity"), [HiddenUnless('limit_registrations'), DataRequired(),
                                                      NumberRange(min=1)],
                                      description=_("Maximum number of registrations"))
    notifications_enabled = BooleanField(_('Enabled'), widget=SwitchWidget(),
                                         description=_('Send email notifications for events related to this '
                                                       'registration form.'))
    recipients_emails = EmailListField(_('List of recipients'),
                                       [HiddenUnless('notifications_enabled', preserve_data=True), DataRequired()],
                                       description=_('Email addresses to notify about events related to this '
                                                     'registration form.'))


class RegistrationFormScheduleForm(IndicoForm):
    start_dt = IndicoDateTimeField(_("Start"), [DataRequired(), DateTimeRange(earliest='now')],
                                   description=_("Moment when registrations will be open"))
    end_dt = IndicoDateTimeField(_("End"), [Optional(), LinkedDateTime('start_dt')],
                                 description=_("Moment when registrations will be closed"))

    def __init__(self, *args, **kwargs):
        regform = kwargs.pop('regform')
        self.timezone = regform.event.tz
        super(IndicoForm, self).__init__(*args, **kwargs)
