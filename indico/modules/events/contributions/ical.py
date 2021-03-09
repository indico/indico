# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from icalendar import Event
from lxml import html
from lxml.etree import ParserError
from werkzeug.urls import url_parse

from indico.core.config import config
from indico.util.date_time import now_utc


def generate_contribution_component(contribution):
    """Generates an Event icalendar component from an Indico Contribution.

    :param contribution: The Indico Contribution to use
    :returns: an icalendar Event
    """

    cal_contribution = Event()

    cal_contribution.add(
        'uid', 'indico-contribution-{}@{}'.format(contribution.id, url_parse(config.BASE_URL).host)
    )
    cal_contribution.add('dtstamp', now_utc(False))
    cal_contribution.add('dtstart', contribution.start_dt)
    cal_contribution.add('dtend', contribution.end_dt)
    cal_contribution.add('summary', contribution.title)

    location = (f'{contribution.room_name} ({contribution.venue_name})'
                if contribution.venue_name and contribution.room_name
                else (contribution.venue_name or contribution.room_name))
    if location:
        cal_contribution.add('location', location)

    description = []
    if contribution.person_links:
        speakers = [f'{x.full_name} ({x.affiliation})' if x.affiliation else x.full_name
                    for x in contribution.person_links]
        description.append('Speakers: {}'.format(', '.join(speakers)))
    if contribution.description:
        desc_text = str(contribution.description) or '<p/>'  # get rid of RichMarkup
        try:
            description.append(str(html.fromstring(desc_text).text_content()))
        except ParserError:
            # this happens if desc_text only contains a html comment
            pass
    cal_contribution.add('description', '\n'.join(description))

    return cal_contribution
