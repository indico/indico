# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.orm import joinedload

from indico.core.config import Config
from indico.core.notifications import send_email, make_email
from indico.modules.categories.models.categories import Category
from indico.web.flask.templating import get_template_module


def notify_event_creation(event, following_events=None):
    """Send email notifications when a new Event is created

    :param event: The `Event` that has been created.
    :param following_events: A list of later event occurrences in case
                             of a lecture with more than one occurrence.
    """
    emails = set()

    for cat in event.category.chain_query.filter(Category.notify_managers).options(joinedload('acl_entries')):
        emails.update(cat.event_creation_notification_emails)
        for manager in cat.get_manager_list():
            if manager.is_single_person:
                emails.add(manager.email)
            elif manager.is_group:
                emails.update(x.email for x in manager.get_members())

    if emails:
        template = get_template_module('events/emails/event_creation.txt', event=event,
                                       following_events=following_events)
        send_email(make_email(bcc_list=emails, template=template, from_address=Config.getInstance().getSupportEmail()),
                   event.as_legacy, module='Events')
