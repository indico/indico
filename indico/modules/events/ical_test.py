# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import icalendar

from indico.modules.events.ical import events_to_ical, generate_event_component


def test_export_includes_event_category_path(create_event, create_category):
    physics = create_category(title='Physics')
    category = create_category(title='Seminars', parent=physics)
    event = create_event(category=category)
    exported = generate_event_component(event).to_ical().decode()
    assert 'CATEGORIES:Physics » Seminars' in exported.splitlines()


def test_export_skips_category_for_unlisted_event(dummy_event):
    dummy_event.category = None
    component = generate_event_component(dummy_event)
    assert 'CATEGORIES' not in component


def test_calendar_subscription_name():
    title = 'Physics, Seminars'
    calendar = icalendar.Calendar.from_ical(events_to_ical([], calendar_name=title))
    assert calendar['NAME'] == calendar['X-WR-CALNAME'] == title

    unnamed = icalendar.Calendar.from_ical(events_to_ical([]))
    assert 'NAME' not in unnamed
    assert 'X-WR-CALNAME' not in unnamed
