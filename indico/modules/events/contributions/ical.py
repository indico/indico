# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from urllib.parse import urlsplit

import icalendar

from indico.core.config import config
from indico.modules.events.ical import generate_basic_component
from indico.web.flask.util import url_for


def generate_contribution_component(contribution, related_to_uid=None, organizer=None):
    """Generate an Event icalendar component from an Indico Contribution.

    :param contribution: The Indico Contribution to use
    :param related_to_uid: Indico uid used in RELATED-TO field
    :return: an icalendar Event
    """
    uid = f'indico-contribution-{contribution.id}@{urlsplit(config.BASE_URL).hostname}'
    url = url_for('contributions.display_contribution', contribution, _external=True)
    component = generate_basic_component(contribution, uid, url, organizer=organizer)

    if related_to_uid:
        component.add('related-to', related_to_uid)

    return component


def contribution_to_ical(contribution):
    """Serialize a contribution into an ical.

    :param contribution: The contribution to serialize
    """
    calendar = icalendar.Calendar()
    calendar.add('version', '2.0')
    calendar.add('prodid', '-//CERN//INDICO//EN')

    related_event_uid = f'indico-event-{contribution.event.id}@{urlsplit(config.BASE_URL).hostname}'
    component = generate_contribution_component(contribution, related_event_uid)
    calendar.add_component(component)

    return calendar.to_ical()
