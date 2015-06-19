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

from flask import url_for

from indico.modules.users.models.users import User

from indico.core.notifications import send_email, make_email
from indico.web.flask.templating import get_template_module
from indico.util.signing import secure_serializer


def send_verification_email(email, template, salt, endpoint, data=None, url_args=None):
    token = secure_serializer.dumps(data or email, salt=salt)
    url = url_for(endpoint, email=email, token=token, _external=True, _secure=True)
    template = get_template_module(template, email=email, url=url)
    send_email(make_email(email, template=template))


def notify_of_registration_request_approval(email, endpoint):
    approval_token = secure_serializer.dumps(email)
    url = url_for(endpoint, _external=True, approval_token=approval_token, _secure=True)
    template = get_template_module('auth/emails/registration_request_approved.txt', url=url)
    send_email(make_email(email, template=template))


def send_notification_to_admins(template):
    admins = User.find_all(is_admin=True)
    for admin in admins:
        send_email(make_email(admin.email, template=template))
