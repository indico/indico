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

from flask_pluginengine import current_plugin
from markupsafe import Markup

from indico.core.notifications import email_sender, make_email
from indico.core.plugins import get_plugin_template_module
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for


def make_email_template(template, agreement, email_body=None):
    func = get_template_module if not current_plugin else get_plugin_template_module
    link = Markup('<a href="{0}">{0}</a>'.format(url_for('agreements.agreement_form', agreement,
                                                 uuid=agreement.uuid, _external=True)))
    if not email_body:
        email_body = func('events/agreements/emails/agreement_default_body.html', event=agreement.event).get_body()
    email_body = email_body.format(person_name=agreement.person_name, agreement_link=link)
    return func(template, email_body=email_body)


@email_sender
def notify_agreement_new(agreement, email_body=None):
    template = make_email_template('events/agreements/emails/agreement_new.html', agreement, email_body)
    return make_email(agreement.person_email, template=template, html=True)


@email_sender
def notify_agreement_reminder(agreement, email_body=None):
    template = make_email_template('events/agreements/emails/agreement_reminder.html', agreement, email_body)
    return make_email(agreement.person_email, template=template, html=True)
