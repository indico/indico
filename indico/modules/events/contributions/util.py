# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from collections import defaultdict

from sqlalchemy.orm import load_only, contains_eager, noload

from indico.modules.events.models.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.util import serialize_event_person
from indico.modules.fulltextindexes.models.events import IndexedEvent


def get_events_with_linked_contributions(user, from_dt=None, to_dt=None):
    """Returns a dict with keys representing event_id and the values containing
    data about the user rights for contributions within the event

    :param user: A `User`
    :param from_dt: The earliest event start time to look for
    :param to_dt: The latest event start time to look for
    """
    event_date_filter = None
    if from_dt and to_dt:
        event_date_filter = IndexedEvent.start_date.between(from_dt, to_dt)
    elif from_dt:
        event_date_filter = IndexedEvent.start_date >= from_dt
    elif to_dt:
        event_date_filter = IndexedEvent.start_date <= to_dt

    query = (user.in_contribution_acls
             .options(load_only('contribution_id', 'roles', 'full_access', 'read_access'))
             .options(noload('*'))
             .options(contains_eager(ContributionPrincipal.contribution).load_only('event_id'))
             .join(Contribution)
             .join(Event, Event.id == Contribution.event_id)
             .filter(~Contribution.is_deleted, ~Event.is_deleted))
    if event_date_filter is not None:
        query = query.join(IndexedEvent, IndexedEvent.id == Contribution.event_id)
        query = query.filter(event_date_filter)
    data = defaultdict(set)
    for principal in query:
        roles = data[principal.contribution.event_id]
        if 'submit' in principal.roles:
            roles.add('contribution_submission')
        if principal.full_access:
            roles.add('contribution_manager')
        if principal.read_access:
            roles.add('contribution_access')


def serialize_contribution_person_link(person_link):
    """Serialize ContributionPersonLink to JSON-like object"""
    data = serialize_event_person(person_link.person)
    data['isSpeaker'] = person_link.is_speaker
    data['authorType'] = person_link.author_type.value
    return data
