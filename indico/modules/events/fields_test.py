# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json

import pytest

from indico.modules.events.fields import EventPersonLinkListField
from indico.modules.events.models.persons import EventPerson, EventPersonLink
from indico.web.forms.base import IndicoForm


class MockForm(IndicoForm):
    person_link_data = EventPersonLinkListField('Test')

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)


@pytest.mark.usefixtures('request_context')
def test_serialize_principal(app, dummy_event, dummy_user):
    from indico.modules.events.persons.schemas import EventPersonSchema
    with app.test_request_context():
        form = MockForm(event=dummy_event)
    dummy_user.phone = '91'
    dummy_user.address = 'My street'
    dummy_user.affiliation = 'Test'
    person = EventPerson.create_from_user(dummy_user, dummy_event)
    persons = EventPersonSchema(only=EventPersonSchema.Meta.public_fields).dumps([person], many=True)
    form.person_link_data.process_formdata([persons])
    del form.person_link_data._submitted_data
    result = form.person_link_data._value()
    assert result[0].get('phone') == ''
    assert result[0].get('address') == ''
    assert result[0].get('affiliation') == 'Test'


@pytest.mark.usefixtures('request_context')
def test_submitter_permissions(app, db, dummy_event, dummy_user):
    from indico.modules.events.persons.schemas import PersonLinkSchema
    person = EventPerson.create_from_user(dummy_user, dummy_event)
    person_link = EventPersonLink(person=person)
    dummy_event.person_links = [person_link]
    dummy_event.update_principal(person_link.person.principal, add_permissions={'submit'})
    with app.test_request_context():
        form = MockForm(event=dummy_event)
    form.person_link_data.data = dummy_event.person_links
    # Remove all persons
    form.person_link_data.process_formdata(['[]'])
    dummy_event.person_link_data = form.person_link_data.data
    db.session.flush()
    assert person.has_role('submit', dummy_event) is False
    # Serialize a person_link with a submitter role
    input_person = PersonLinkSchema().dump(person_link)
    input_person['roles'] = ['submitter']
    form.person_link_data.process_formdata([json.dumps([input_person])])
    dummy_event.person_link_data = form.person_link_data.data
    db.session.flush()
    assert person.has_role('submit', dummy_event) is True
