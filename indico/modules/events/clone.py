# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.principals import clone_principals
from indico.modules.attachments.settings import attachments_settings
from indico.modules.events.cloning import EventCloner, get_attrs_to_clone
from indico.modules.events.contributions import contribution_settings
from indico.modules.events.management.settings import privacy_settings
from indico.modules.events.models.events import EventType
from indico.modules.events.models.persons import EventPerson, EventPersonLink
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.sessions import session_settings
from indico.modules.events.util import track_location_changes
from indico.util.i18n import _


class EventLocationCloner(EventCloner):
    name = 'event_location'
    friendly_name = _('Venue/Room')
    is_default = True

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    def get_conflicts(self, target_event):
        if self._has_content(target_event):
            return [_('The target event already has a venue/room')]

    def run(self, new_event, cloners, shared_data, event_exists=False):
        with db.session.no_autoflush:
            self._clone_location(new_event)
        db.session.flush()

    def _has_content(self, event):
        return event.has_location_info

    def _clone_location(self, new_event):
        with track_location_changes():
            new_event.location_data = self.old_event.location_data
            db.session.flush()


class EventPersonCloner(EventCloner):
    name = 'event_persons'
    friendly_name = _('Persons')
    is_internal = True
    is_default = True

    # We do not override `is_available` as we have cloners depending
    # on this internal cloner even if it won't clone anything.

    def get_conflicts(self, target_event):
        if target_event.persons.has_rows():
            return [_('The target event already has persons')]

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._person_map = {}
        with db.session.no_autoflush:
            self._clone_persons(new_event)
        db.session.flush()
        return {'person_map': self._person_map}

    def _clone_persons(self, new_event):
        attrs = get_attrs_to_clone(EventPerson, add={'user'})
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

    def get_conflicts(self, target_event):
        if self._has_content(target_event):
            if self.old_event.type_ == EventType.lecture:
                return [_('The target event already has speakers')]
            else:
                return [_('The target event already has chairpersons')]

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._person_map = shared_data['event_persons']['person_map']
        with db.session.no_autoflush:
            self._clone_person_links(new_event)
        db.session.flush()

    def _has_content(self, event):
        return bool(event.person_links)

    def _clone_person_links(self, new_event):
        attrs = get_attrs_to_clone(EventPersonLink)
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

    def get_conflicts(self, target_event):
        conflicts = []

        if target_event.access_key:
            conflicts.append(_('The target event already has an access key'))

        entries = list(target_event.acl_entries)
        if len(entries) != 1 or entries[0].user != target_event.creator:
            conflicts.append(_('The target event already has a custom ACL'))

        return conflicts

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._event_role_map = shared_data['event_roles']['event_role_map'] if 'event_roles' in cloners else None
        self._regform_map = shared_data['registration_forms']['form_map'] if 'registration_forms' in cloners else None
        with db.session.no_autoflush:
            self._clone_protection(new_event)
            self._clone_session_coordinator_privs(new_event)
            self._clone_contrib_settings(new_event)
            self._clone_attachment_settings(new_event)
            self._clone_acl(new_event, event_exists)
            self._clone_visibility(new_event)
        db.session.flush()
        if event_exists:
            signals.acl.protection_changed.send(type(new_event), obj=new_event, mode=new_event.protection_mode,
                                                old_mode=None)

    def _clone_protection(self, new_event):
        new_event.protection_mode = self.old_event.protection_mode
        new_event.access_key = self.old_event.access_key
        new_event.own_no_access_contact = self.old_event.own_no_access_contact
        new_event.public_regform_access = self.old_event.public_regform_access
        new_event.subcontrib_speakers_can_submit = self.old_event.subcontrib_speakers_can_submit

    def _clone_visibility(self, new_event):
        new_event.visibility = self.old_event.visibility if new_event.category == self.old_event.category else None

    def _clone_session_coordinator_privs(self, new_event):
        session_settings_data = session_settings.get_all(self.old_event)
        session_settings.set_multi(new_event, {
            'coordinators_manage_contributions': session_settings_data['coordinators_manage_contributions'],
            'coordinators_manage_blocks': session_settings_data['coordinators_manage_blocks']
        })

    def _clone_contrib_settings(self, new_event):
        contribution_settings_data = contribution_settings.get_all(self.old_event)
        contribution_settings.set_multi(new_event, {
            'submitters_can_edit': contribution_settings_data['submitters_can_edit'],
            'submitters_can_edit_custom': contribution_settings_data['submitters_can_edit_custom']
        })

    def _clone_attachment_settings(self, new_event):
        attachment_settings_data = attachments_settings.get_all(self.old_event)
        attachments_settings.set_multi(new_event, {
            'managers_only': attachment_settings_data['managers_only'],
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


class EventSeriesCloner(EventCloner):
    name = 'event_series'
    friendly_name = _('Add to event series')
    new_event_only = True

    @property
    def is_default(self):
        return bool(self.old_event.series and self.old_event.series.event_title_pattern)

    @property
    def is_available(self):
        return bool(self.old_event.series)

    def run(self, new_event, cloners, shared_data, event_exists=False):
        series = self.old_event.series
        new_event.series = series
        if series.event_title_pattern:
            n = len(series.events)
            # XXX not using .format() here to avoid errors if someone adds other
            # placeholder-like stuff in the pattern
            new_event.title = series.event_title_pattern.replace('{n}', str(n))
        db.session.flush()


class EventPrivacyCloner(EventCloner):
    name = 'event_privacy'
    friendly_name = _('Privacy settings')
    is_default = True

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    def get_conflicts(self, target_event):
        if self._has_content(target_event):
            return [_('The target event already has privacy settings')]

    def _has_content(self, event):
        privacy_settings_data = privacy_settings.get_all(event, no_defaults=True)
        return any(privacy_settings_data.values())

    def run(self, new_event, cloners, shared_data, event_exists=False):
        with db.session.no_autoflush:
            self._clone_privacy_settings(new_event)
        db.session.flush()

    def _clone_privacy_settings(self, new_event):
        privacy_settings.set_multi(new_event, privacy_settings.get_all(self.old_event, no_defaults=True))
