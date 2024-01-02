# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.notifications import email_sender, make_email
from indico.web.flask.templating import get_template_module


@email_sender
def notify_amount_inconsistency(registration, amount, currency):
    event = registration.registration_form.event
    to = event.creator.email
    with event.creator.force_user_locale():
        tpl = get_template_module('events/payment/emails/payment_inconsistency_email_to_manager.txt',
                                  event=event, registration=registration, amount=amount, currency=currency)
        return make_email(to, template=tpl)
