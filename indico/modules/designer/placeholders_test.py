# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import itertools
from datetime import datetime
from operator import attrgetter
from pathlib import Path

import pytest
from PIL import Image

from indico.modules.designer import placeholders
from indico.modules.events.models.persons import EventPerson, EventPersonLink
from indico.modules.events.registration.util import modify_registration


pytest_plugins = ('indico.modules.events.registration.testing.fixtures', 'indico.modules.designer.testing.fixtures')


def _get_placeholders():
    """Get a list of all designer placeholders."""
    exports = [getattr(placeholders, name) for name in placeholders.__all__]
    phs = [obj for obj in exports if issubclass(obj, placeholders.DesignerPlaceholder)]
    return sorted(phs, key=attrgetter('group', 'name'))


text_placeholders = [ph for ph in _get_placeholders() if not ph.is_image]
image_placeholders = [ph for ph in _get_placeholders() if ph.is_image]


def _get_render_kwargs(ph, event, person, registration, item):
    if ph.group == 'registrant':
        if ph.data_source == 'person':
            return {'person': person}
        else:
            return {'registration': registration}
    elif ph.group == 'event':
        return {'event': event}
    elif ph.group == 'fixed':
        return {'item': item}


def _prepare_event_data(dummy_event, dummy_user):
    dummy_event.start_dt = datetime(2023, 1, 1, 10, 0)
    dummy_event.end_dt = datetime(2023, 1, 2, 15, 0)
    dummy_event.title = 'Dummy event title'
    dummy_event.description = 'Dummy event description'
    dummy_event.organizer_info = 'CERN'
    dummy_event.room_name = 'Dummy room'
    dummy_event.venue_name = 'Dummy venue'

    person = EventPerson.create_from_user(dummy_user, dummy_event)
    person_link = EventPersonLink(person=person)
    dummy_event.person_links = [person_link, person_link]


def _prepare_registration_data(dummy_reg):
    modify_registration(dummy_reg, {'email': '1337@example.test', 'first_name': 'Guinea', 'last_name': 'Pig',
                                    'affiliation': 'CERN', 'address': '1211 Geneva 23, Switzerland',
                                    'country': 'CH', 'phone': '+41227676000', 'position': 'Developer'},
                        notify_user=False)

    # Set the registration title
    for data in dummy_reg.data:
        field = data.field_data.field
        if field.personal_data_type and field.personal_data_type.name == 'title':
            uuid = list(data.field_data.field.data['captions'])[0]
            data.data = {uuid: 1}

    dummy_reg.base_price = 100


def _create_placeholder_template():
    template = ''
    for key, group in itertools.groupby(text_placeholders, key=attrgetter('group')):
        template += f"Group '{key}':\n"
        for ph in group:
            template += f'\t{ph.name}: {{{ph.name}}}\n'
    return template.strip()


@pytest.mark.usefixtures('request_context', 'dummy_accompanying_persons_field')
def test_replace_text_placeholders(snapshot, dummy_event, dummy_reg, dummy_user):
    # For 'event' placeholders
    _prepare_event_data(dummy_event, dummy_user)

    # For 'registrant' placeholders
    _prepare_registration_data(dummy_reg)

    # For fixed text placeholder
    dummy_item = {'text': 'Hello, world!'}

    # For 'person' data_source
    dummy_person = {'id': dummy_reg.id,
                    'first_name': dummy_reg.first_name,
                    'last_name': dummy_reg.last_name,
                    'registration': dummy_reg,
                    'is_accompanying': False}

    template = _create_placeholder_template()
    for ph in text_placeholders:
        kwargs = _get_render_kwargs(ph, dummy_event, dummy_person, dummy_reg, dummy_item)
        template = ph.replace(template, **kwargs)

    snapshot.snapshot_dir = Path(__file__).parent / 'tests'
    snapshot.assert_match(template, 'test_replace_text_placeholders.txt')


@pytest.mark.usefixtures('request_context', 'dummy_event_logo')
def test_render_image_placeholders(dummy_event, dummy_reg, dummy_designer_image_file):
    # For fixed image placeholder
    dummy_item = {'image_id': dummy_designer_image_file.id}
    # For 'person' data_source
    dummy_person = {'id': dummy_reg.id,
                    'first_name': dummy_reg.first_name,
                    'last_name': dummy_reg.last_name,
                    'registration': dummy_reg,
                    'is_accompanying': False}

    for ph in image_placeholders:
        kwargs = _get_render_kwargs(ph, dummy_event, dummy_person, dummy_reg, dummy_item)
        res = ph.render(**kwargs)
        assert isinstance(res, Image.Image) or res is None
