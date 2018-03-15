# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from indico.modules.events.models.persons import EventPerson
from indico.modules.users import User
from indico.modules.users.models.users import UserTitle
from indico.util.user import principal_from_fossil


def create_event_person(event, create_untrusted_persons=False, **data):
    """Create an event person from data passed as kwargs."""
    title = next((x.value for x in UserTitle if data.get('title') == x.title), None)
    return EventPerson(event=event, email=data.get('email', '').lower(), _title=title,
                       first_name=data.get('firstName'), last_name=data['familyName'],
                       affiliation=data.get('affiliation'), address=data.get('address'),
                       phone=data.get('phone'), is_untrusted=create_untrusted_persons)


def get_event_person_for_user(event, user, create_untrusted_persons=False):
    """Return the event person that links to a given User/Event (if any)."""
    return EventPerson.for_user(user, event, is_untrusted=create_untrusted_persons)


def get_event_person(event, data, create_untrusted_persons=False, allow_external=False, allow_emails=False,
                     allow_networks=False):
    """Get an EventPerson from dictionary data.

    If there is already an event person in the same event and for the same user,
    it will be returned. Matching is done with the e-mail.
    """
    person_type = data.get('_type')
    if person_type is None:
        if data.get('email'):
            email = data['email'].lower()
            user = User.find_first(~User.is_deleted, User.all_emails.contains(email))
            if user:
                return get_event_person_for_user(event, user, create_untrusted_persons=create_untrusted_persons)
            elif event:
                person = event.persons.filter_by(email=email).first()
                if person:
                    return person
        # We have no way to identify an existing event person with the provided information
        return create_event_person(event, create_untrusted_persons=create_untrusted_persons, **data)
    elif person_type == 'Avatar':
        # XXX: existing_data
        principal = principal_from_fossil(data, allow_pending=allow_external, allow_emails=allow_emails,
                                          allow_networks=allow_networks)
        return get_event_person_for_user(event, principal, create_untrusted_persons=create_untrusted_persons)
    elif person_type == 'EventPerson':
        return event.persons.filter_by(id=data['id']).one()
    elif person_type == 'PersonLink':
        return event.persons.filter_by(id=data['personId']).one()
    else:
        raise ValueError("Unknown person type '{}'".format(person_type))
