# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask_pluginengine import current_plugin

from indico.core.notifications import email_sender, make_email
from indico.core.plugins import get_plugin_template_module
from indico.util.placeholders import replace_placeholders
from indico.web.flask.templating import get_template_module


def make_email_template(template, agreement, email_body=None):
    func = get_template_module if not current_plugin else get_plugin_template_module
    if not email_body:
        email_body = agreement.definition.get_email_body_template(agreement.event).get_body()
    email_body = replace_placeholders('agreement-email', email_body, definition=agreement.definition,
                                      agreement=agreement)
    return func(template, email_body=email_body)


@email_sender
def notify_agreement_new(agreement, email_body=None, cc_addresses=None, from_address=None):
    template = make_email_template('events/agreements/emails/agreement_new.html', agreement, email_body)
    return make_email(agreement.person_email, cc_list=cc_addresses, from_address=from_address,
                      template=template, html=True)


@email_sender
def notify_agreement_reminder(agreement, email_body=None, cc_addresses=None, from_address=None):
    template = make_email_template('events/agreements/emails/agreement_reminder.html', agreement, email_body)
    return make_email(agreement.person_email, cc_list=cc_addresses, from_address=from_address,
                      template=template, html=True)


@email_sender
def notify_new_signature_to_manager(agreement):
    template = get_template_module('events/agreements/emails/new_signature_email_to_manager.txt', agreement=agreement)
    return make_email(agreement.event.all_manager_emails, template=template)
