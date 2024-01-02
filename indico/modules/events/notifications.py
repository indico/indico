# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import itertools
from operator import attrgetter

from sqlalchemy.orm import joinedload

from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.notifications import make_email, send_email
from indico.modules.categories.models.categories import Category
from indico.util.i18n import force_locale
from indico.web.flask.templating import get_template_module


def _get_emails_from_category(category, ignore_notify_managers=False):
    emails = set(category.event_creation_notification_emails)

    if category.notify_managers or ignore_notify_managers:
        for manager in category.get_manager_list():
            if manager.principal_type in (PrincipalType.user, PrincipalType.email):
                emails.add(manager.email)
            elif manager.principal_type in (PrincipalType.local_group, PrincipalType.multipass_group):
                emails.update(x.email for x in manager.get_members())

    return emails


def notify_event_creation(event, occurrences=None):
    """Send email notifications when a new Event is created.

    :param event: The `Event` that has been created.
    :param occurrences: A list of event occurrences in case of a
                        series of events.  If specified, the links
                        and dates/times are only taken from the
                        events in this list.
    """
    if not event.category:
        return

    emails = set()
    query = (event.category.chain_query.
             filter(Category.notify_managers | (Category.event_creation_notification_emails != []))
             .options(joinedload('acl_entries')))
    for cat in query:
        emails.update(_get_emails_from_category(cat))

    if emails:
        with force_locale(None):
            template = get_template_module('events/emails/event_creation.txt', event=event, occurrences=occurrences)
            email = make_email(bcc_list=emails, template=template)
        send_email(email)


def notify_move_request_creation(events, target_category, comment=''):
    """Send email notifications when a move request is created.

    :param events: List of events requested to move.
    :param target_category: The category to move the events into.
    :param comment: Optional requestor's comment.
    """
    emails = set()
    query = (target_category.chain_query
             .filter(Category.notify_managers | (Category.event_creation_notification_emails != []))
             .options(joinedload('acl_entries')))

    # Walk up the category chain
    for cat in reversed(query.all()):
        emails.update(_get_emails_from_category(cat, ignore_notify_managers=True))

        if emails:
            with force_locale(None):
                template = get_template_module('events/emails/move_request_creation.txt',
                                               events=events, target_category=target_category, comment=comment)
                email = make_email(bcc_list=emails, template=template)
            send_email(email)
            break


def notify_move_request_closure(move_requests, accept, reason=''):
    """Send email notifications when a move request is accepted/rejected.

    :param move_requests: List of `EventMoveRequest` that were accepted/rejected.
    :param accept: Whether the requests were accepted.
    :param reason: Optional reason for rejection.
    """
    move_requests = sorted(move_requests, key=attrgetter('requestor.id', 'category.id'))
    for (requestor, category), requests in itertools.groupby(move_requests, attrgetter('requestor', 'category')):
        events = [rq.event for rq in requests]
        with requestor.force_user_locale():
            template = get_template_module('events/emails/move_request_closure.txt',
                                           events=events, target_category=category, accept=accept, reason=reason)
            email = make_email(to_list=requestor.email, template=template)
        send_email(email)
