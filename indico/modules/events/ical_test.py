# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.ical import generate_event_component


def test_export_includes_event_category_path(create_event, create_category):
    physics = create_category(title='Physics')
    category = create_category(title='Seminars', parent=physics)
    event = create_event(category=category)

    exported = generate_event_component(event).to_ical()

    assert b'CATEGORIES:Physics / Seminars' in exported.splitlines()


def test_export_skips_category_for_unlisted_event(dummy_event):
    dummy_event.category = None
    component = generate_event_component(dummy_event)
    assert 'CATEGORIES' not in component
