# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import render_template

from indico.core.notifications import email_sender, make_email


@email_sender
def notify_amount_inconsistency(registration, amount, currency):
    event = registration.registration_form.event
    to = event.creator.email
    body = render_template('events/payment/emails/payment_inconsistency_email_to_manager.txt',
                           event=event, registration=registration, amount=amount, currency=currency)
    return make_email(to, subject='Payment inconsistency', body=body)
