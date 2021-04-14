# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.orm import joinedload

from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.notifications import make_email, send_email
from indico.modules.categories.models.categories import Category
from indico.web.flask.templating import get_template_module


def notify_event_creation(event, occurrences=None):
    """Send email notifications when a new Event is created.

    :param event: The `Event` that has been created.
    :param occurrences: A list of event occurrences in case of a
                        series of events.  If specified, the links
                        and dates/times are only taken from the
                        events in this list.
    """
    emails = set()
    query = (event.category.chain_query.
             filter(Category.notify_managers | (Category.event_creation_notification_emails != []))
             .options(joinedload('acl_entries')))
    for cat in query:
        emails.update(cat.event_creation_notification_emails)
        if cat.notify_managers:
            for manager in cat.get_manager_list():
                if manager.principal_type in (PrincipalType.user, PrincipalType.email):
                    emails.add(manager.email)
                elif manager.principal_type in (PrincipalType.local_group, PrincipalType.multipass_group):
                    emails.update(x.email for x in manager.get_members())

    if emails:
        template = get_template_module('events/emails/event_creation.txt', event=event, occurrences=occurrences)
        send_email(make_email(bcc_list=emails, template=template))
