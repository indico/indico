# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.models.persons import EventPerson, EventPersonLink


def test_dump_event(db, dummy_user, dummy_event):
    from indico.modules.search.schemas import EventSchema
    schema = EventSchema()
    dummy_event.description = 'A dummy event'
    dummy_event.keywords = ['foo', 'bar']
    person = EventPerson.create_from_user(dummy_user, dummy_event)
    person2 = EventPerson(event=dummy_event, first_name='Admin', last_name='Saurus', affiliation='Indico')
    dummy_event.person_links.append(EventPersonLink(person=person))
    dummy_event.person_links.append(EventPersonLink(person=person2))
    db.session.flush()
    category_id = dummy_event.category_id
    assert schema.dump(dummy_event) == {
        'description': 'A dummy event',
        'keywords': ['foo', 'bar'],
        'location': {'address': '', 'room_name': '', 'venue_name': ''},
        'persons': [{'affiliation': None, 'name': 'Guinea Pig'},
                    {'affiliation': 'Indico', 'name': 'Admin Saurus'}],
        'title': 'dummy#0',
        'category_id': category_id,
        'category_path': [
            {'id': 0, 'title': 'Home', 'url': '/'},
            {'id': category_id, 'title': 'dummy', 'url': f'/category/{category_id}/'},
        ],
        'end_dt': dummy_event.end_dt.isoformat(),
        'event_id': 0,
        'start_dt': dummy_event.start_dt.isoformat(),
        'type': 'event',
        'event_type': 'meeting',
        'url': '/event/0/',
    }
