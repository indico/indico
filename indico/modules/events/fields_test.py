# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.fields import EventPersonLinkListField
from indico.modules.events.models.persons import EventPerson
from indico.web.forms.base import IndicoForm


class MockForm(IndicoForm):
    person_link_data = EventPersonLinkListField('Test')

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event')
        super().__init__(*args, **kwargs)


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
    result = form.person_link_data._value()
    assert result[0].get('phone') == ''
    assert result[0].get('address') == ''
    assert result[0].get('affiliation') == 'Test'
