# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core import signals
from indico.core.db import db
from indico.modules.events.agreements.models.agreements import Agreement
from indico.modules.events.agreements.notifications import notify_agreement_new
from indico.util.signals import named_objects_from_signal


def get_agreement_definitions():
    return named_objects_from_signal(signals.agreements.get_definitions.send(), plugin_attr='plugin')


def send_new_agreements(event, name, people, email_body, cc_addresses, sender_address):
    """Create and send agreements for a list of people on a given event.

    :param event: The `Event` associated with the agreement
    :param name: The agreement type matcing a :class:`AgreementDefinition` name
    :param people: The list of people for whom agreements will be created
    :param email_body: The body of the email
    :param cc_addresses: Email addresses to send CCs to
    :param sender_address: Email address of the sender
    """
    agreements = []
    for person in people.values():
        agreement = Agreement.create_from_data(event=event, type_=name, person=person)
        db.session.add(agreement)
        agreements.append(agreement)
    db.session.flush()
    for agreement in agreements:
        notify_agreement_new(agreement, email_body, cc_addresses, sender_address)
    return agreements
