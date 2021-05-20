# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import clone_principals
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.events.cloning import EventCloner
from indico.modules.events.models.events import EventType
from indico.modules.events.models.persons import EventPerson, EventPersonLink
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.sessions import session_settings
from indico.modules.events.surveys.models.items import SurveyItem
from indico.modules.events.surveys.models.surveys import Survey
from indico.modules.events.util import track_location_changes
from indico.util.i18n import _


class EventLocationCloner(EventCloner):
    name = 'event_location'
    friendly_name = _('Venue/Room')
    is_default = True

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    def has_conflicts(self, target_event):
        return self._has_content(target_event)

    def run(self, new_event, cloners, shared_data, event_exists=False):
        with db.session.no_autoflush:
            self._clone_location(new_event)
        db.session.flush()

    def _has_content(self, event):
        return event.has_location_info

    def _clone_location(self, new_event):
        with track_location_changes():
            new_event.location_data = self.old_event.location_data


class EventPersonCloner(EventCloner):
    name = 'event_persons'
    friendly_name = _('Persons')
    is_internal = True
    is_default = True

    # We do not override `is_available` as we have cloners depending
    # on this internal cloner even if it won't clone anything.

    def has_conflicts(self, target_event):
        return target_event.persons.has_rows()

    def run(self, new_event, cloners, shared_data, event_exists=False):
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
        return self._has_content(self.old_event)

    def has_conflicts(self, target_event):
        return self._has_content(target_event)

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._person_map = shared_data['event_persons']['person_map']
        with db.session.no_autoflush:
            self._clone_person_links(new_event)
        db.session.flush()

    def _has_content(self, event):
        return bool(event.person_links)

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
    uses = {'event_roles', 'registration_forms'}

    def has_conflicts(self, target_event):
        if target_event.access_key != '':
            return True
        entries = list(target_event.acl_entries)
        return len(entries) != 1 or entries[0].user != target_event.creator

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._event_role_map = shared_data['event_roles']['event_role_map'] if 'event_roles' in cloners else None
        self._regform_map = shared_data['registration_forms']['form_map'] if 'registration_forms' in cloners else None
        with db.session.no_autoflush:
            self._clone_protection(new_event)
            self._clone_session_coordinator_privs(new_event)
            self._clone_acl(new_event, event_exists)
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

    def _clone_acl(self, new_event, event_exists):
        if event_exists:
            acl_entries = {principal for principal in self.old_event.acl_entries if principal.user != new_event.creator}
            new_event.acl_entries = clone_principals(EventPrincipal, acl_entries,
                                                     self._event_role_map, self._regform_map)
            db.session.flush()
            new_event.update_principal(new_event.creator, full_access=True)
        else:
            new_event.acl_entries = clone_principals(EventPrincipal, self.old_event.acl_entries,
                                                     self._event_role_map, self._regform_map)


class EventSurveyCloner(EventCloner):
    name = 'event_survey'
    friendly_name = _('Surveys')
    is_default = False

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    def has_conflicts(self, target_event):
        return self._has_content(target_event)

    def run(self, new_event, cloners, shared_data, event_exists=False):
        with db.session.no_autoflush:
            self._clone_surveys(new_event)
        db.session.flush()

    def _has_content(self, event):
        return len([survey for survey in event.surveys if not survey.is_deleted])

    def _clone_surveys(self, new_event):
        survey_attrs = get_simple_column_attrs(Survey) - {'uuid', 'start_dt', 'end_dt', '_last_friendly_submission_id'}
        for old_survey in self.old_event.surveys:
            survey = Survey()
            survey.populate_from_attrs(old_survey, survey_attrs)
            item_map = {}
            for old_item in old_survey.items:
                item = self._clone_item(old_item)
                if old_item.parent:
                    assert old_item.parent != old_item
                    if not item_map.get(old_item.parent):
                        item_map[old_item.parent] = self._clone_item(old_item.parent)
                    item.parent = item_map[old_item.parent]
                item_map[old_item] = item
            survey.items.extend(item_map.values())
            new_event.surveys.append(survey)

    def _clone_item(self, old_item):
        item = SurveyItem()
        item.populate_from_attrs(old_item, get_simple_column_attrs(SurveyItem))
        return item
