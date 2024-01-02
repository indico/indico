# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import EXCLUDE

from indico.modules.events.models.persons import EventPerson
from indico.modules.users import User
from indico.modules.users.util import get_user_by_email
from indico.util.string import validate_email_verbose


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
    # user = user from user search results, none = manually added user
    if person_type is None or person_type == 'user':
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
    elif person_type in ('event_person', 'person_link'):
        # event_person = event person from search results, person_link = existing person link
        return event.persons.filter_by(id=data['person_id']).one()
    else:
        raise ValueError(f"Unknown person type '{person_type}'")


def check_person_link_email(event, email):
    """Check whether an email can be used in a person link.

    :param event: The event
    :param email: The email address
    """
    from indico.modules.events.persons.schemas import EventPersonSchema
    from indico.modules.users.schemas import UserSchema
    email = email.lower().strip()
    person = event.persons.filter_by(email=email).first()
    user = get_user_by_email(email)
    # Do not return personal data
    user_schema = UserSchema(exclude=['phone'])
    event_person_schema = EventPersonSchema(exclude=['address', 'phone'])

    if user and person:
        return {'status': 'warning', 'conflict': 'user-and-person-already-exists',
                'event_person': event_person_schema.dump(person), 'user': user_schema.dump(user)}
    if person:
        return {'status': 'warning', 'conflict': 'person-already-exists',
                'event_person': event_person_schema.dump(person)}
    elif user:
        return {'status': 'warning', 'conflict': 'user-already-exists', 'user': user_schema.dump(user)}
    if email_err := validate_email_verbose(email):
        return {'status': 'error' if email_err != 'undeliverable' else 'warning', 'conflict': 'email-invalid',
                'email_error': email_err}
    else:
        return {'status': 'ok'}
