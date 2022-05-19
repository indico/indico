# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import EXCLUDE

from indico.modules.events.models.persons import EventPerson
from indico.modules.users import User
from indico.util.user import principal_from_identifier


def create_event_person(event, create_untrusted_persons=False, **data):
    """Create an event person from data passed as kwargs."""
    from indico.modules.events.persons.schemas import EventPersonSchema
    event_person = EventPerson(event=event, is_untrusted=create_untrusted_persons)
    event_person.populate_from_dict(EventPersonSchema(unknown=EXCLUDE).load(data))
    return event_person


def get_event_person_for_user(event, user, create_untrusted_persons=False):
    """Return the event person that links to a given User/Event (if any)."""
    return EventPerson.for_user(user, event, is_untrusted=create_untrusted_persons)


def get_event_person(event, data, create_untrusted_persons=False, allow_external=False):
    """Get an EventPerson from dictionary data.

    If there is already an event person in the same event and for the same user,
    it will be returned. Matching is done with the e-mail.
    """
    person_type = data.get('type')
    if person_type is None:
        if data.get('email'):
            email = data['email'].lower()
            user = User.query.filter(~User.is_deleted, User.all_emails == email).first()
            if user:
                return get_event_person_for_user(event, user, create_untrusted_persons=create_untrusted_persons)
            elif event:
                person = event.persons.filter_by(email=email).first()
                if person:
                    return person
        # We have no way to identify an existing event person with the provided information
        return create_event_person(event, create_untrusted_persons=create_untrusted_persons, **data)
    elif person_type == 'Avatar':
        principal = principal_from_identifier(data['identifier'], allow_external_users=allow_external)
        return get_event_person_for_user(event, principal, create_untrusted_persons=create_untrusted_persons)
    elif person_type == 'EventPerson':
        return event.persons.filter_by(id=data['id']).one()
    elif person_type == 'PersonLink':
        return event.persons.filter_by(id=data['person_id']).one()
    else:
        raise ValueError(f"Unknown person type '{person_type}'")
