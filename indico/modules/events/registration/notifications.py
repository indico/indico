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

from flask import session

from indico.core.notifications import make_email, send_email
from indico.util.placeholders import replace_placeholders
from indico.web.flask.templating import get_template_module


def notify_invitation(invitation, email_body, from_address):
    """Send a notification about a new registration invitation."""
    email_body = replace_placeholders('registration-invitation-email', email_body, invitation=invitation)
    template = get_template_module('events/registration/emails/invitation.html', email_body=email_body)
    email = make_email(invitation.email, from_address=from_address, template=template, html=True)
    send_email(email, invitation.registration_form.event_new, 'Registration', session.user)


def notify_registration(registration):
    template = get_template_module('events/registration/emails/registration_confirmation_registrant.html',
                                   registration=registration, event=registration.registration_form.event)
    email = make_email(to_list=registration.email, template=template, html=True)
    send_email(email, event=registration.registration_form.event, module='Registration', user=session.user)
