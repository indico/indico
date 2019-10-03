# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import clone_principals
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.events.cloning import EventCloner
from indico.modules.events.models.events import EventType
from indico.modules.events.models.persons import EventPerson, EventPersonLink
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.sessions import session_settings
from indico.util.i18n import _


class EventLocationCloner(EventCloner):
    name = 'event_location'
    friendly_name = _('Venue/Room')
    is_default = True

    @property
    def is_available(self):
        return self.old_event.has_location_info

    def run(self, new_event, cloners, shared_data):
        with db.session.no_autoflush:
            self._clone_location(new_event)
        db.session.flush()

    def _clone_location(self, new_event):
        new_event.location_data = self.old_event.location_data


class EventPersonCloner(EventCloner):
    name = 'event_persons'
    friendly_name = _('Persons')
    is_internal = True
    is_default = True

    # We do not override `is_available` as we have cloners depending
    # on this internal cloner even if it won't clone anything.

    def run(self, new_event, cloners, shared_data):
        self._person_map = {}
        with db.session.no_autoflush:
            self._clone_persons(new_event)
        db.session.flush()
        return {'person_map': self._person_map}

    def _clone_persons(self, new_event):
        attrs = get_simple_column_attrs(EventPerson) | {'user'}
        for old_person in self.old_event.persons:
            person = EventPerson(event=new_event)
            person.populate_from_attrs(old_person, attrs)
            assert person not in db.session
            self._person_map[old_person] = person


class EventPersonLinkCloner(EventCloner):
    name = 'event_person_links'
    requires = {'event_persons'}
    is_default = True

    @property
    def friendly_name(self):
        if self.old_event.type_ == EventType.lecture:
            return _('Speakers')
        else:
            return _('Chairpersons')

    @property
    def is_available(self):
        return bool(self.old_event.person_links)

    def run(self, new_event, cloners, shared_data):
        self._person_map = shared_data['event_persons']['person_map']
        with db.session.no_autoflush:
            self._clone_person_links(new_event)
        db.session.flush()

    def _clone_person_links(self, new_event):
        attrs = get_simple_column_attrs(EventPersonLink)
        for old_link in self.old_event.person_links:
            link = EventPersonLink()
            link.populate_from_attrs(old_link, attrs)
            link.person = self._person_map[old_link.person]
            new_event.person_links.append(link)


class EventProtectionCloner(EventCloner):
    name = 'event_protection'
    friendly_name = _('ACLs and protection settings')
    is_default = True
    uses = {'event_roles'}

    def run(self, new_event, cloners, shared_data):
        self._event_role_map = shared_data['event_roles']['event_role_map'] if 'event_roles' in cloners else None
        with db.session.no_autoflush:
            self._clone_protection(new_event)
            self._clone_session_coordinator_privs(new_event)
            self._clone_acl(new_event)
            self._clone_visibility(new_event)
        db.session.flush()

    def _clone_protection(self, new_event):
        new_event.protection_mode = self.old_event.protection_mode
        new_event.access_key = self.old_event.access_key

    def _clone_visibility(self, new_event):
        new_event.visibility = self.old_event.visibility if new_event.category == self.old_event.category else None

    def _clone_session_coordinator_privs(self, new_event):
        session_settings_data = session_settings.get_all(self.old_event)
        session_settings.set_multi(new_event, {
            'coordinators_manage_contributions': session_settings_data['coordinators_manage_contributions'],
            'coordinators_manage_blocks': session_settings_data['coordinators_manage_blocks']
        })

    def _clone_acl(self, new_event):
        new_event.acl_entries = clone_principals(EventPrincipal, self.old_event.acl_entries, self._event_role_map)
