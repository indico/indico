# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.orm import joinedload, subqueryload

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import clone_principals
from indico.modules.events.cloning import EventCloner, get_attrs_to_clone
from indico.modules.events.sessions import Session
from indico.modules.events.sessions.models.blocks import SessionBlock
from indico.modules.events.sessions.models.persons import SessionBlockPersonLink
from indico.modules.events.sessions.models.principals import SessionPrincipal
from indico.util.i18n import _


class SessionCloner(EventCloner):
    name = 'sessions'
    friendly_name = _('Sessions')
    requires = {'event_persons'}
    uses = {'event_roles', 'registration_forms'}
    is_internal = True

    # We do not override `is_available` as we have cloners depending
    # on this internal cloner even if it won't clone anything.

    def get_conflicts(self, target_event):
        if target_event.sessions:
            return [_('The target event already has sessions')]

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._event_role_map = shared_data['event_roles']['event_role_map'] if 'event_roles' in cloners else None
        self._regform_map = shared_data['registration_forms']['form_map'] if 'registration_forms' in cloners else None
        self._person_map = shared_data['event_persons']['person_map']
        self._new_event_persons = {}
        if event_exists:
            self._new_event_persons = {person.user_id: person for person in new_event.persons
                                       if person.user_id is not None}
        self._session_map = {}
        self._session_block_map = {}
        with db.session.no_autoflush:
            self._clone_sessions(new_event, event_exists=event_exists)
        self._synchronize_friendly_id(new_event)
        db.session.flush()
        return {'session_map': self._session_map, 'session_block_map': self._session_block_map}

    def _clone_sessions(self, new_event, event_exists=False):
        attrs = get_attrs_to_clone(Session, add={'own_room', 'own_venue'})
        query = (Session.query.with_parent(self.old_event)
                 .options(joinedload('blocks'),
                          joinedload('own_venue'),
                          joinedload('own_room').lazyload('*'),
                          subqueryload('acl_entries')))
        for old_sess in query:
            sess = Session()
            sess.populate_from_attrs(old_sess, attrs)
            sess.blocks = list(self._clone_session_blocks(old_sess.blocks, event_exists=event_exists))
            sess.acl_entries = clone_principals(SessionPrincipal, old_sess.acl_entries,
                                                self._event_role_map, self._regform_map)
            new_event.sessions.append(sess)
            self._session_map[old_sess] = sess

    def _clone_session_blocks(self, blocks, event_exists=False):
        attrs = get_attrs_to_clone(SessionBlock, add={'own_room', 'own_venue'})
        for old_block in blocks:
            block = SessionBlock()
            block.populate_from_attrs(old_block, attrs)
            block.person_links = list(self._clone_person_links(old_block.person_links,
                                                               event_exists=event_exists))
            self._session_block_map[old_block] = block
            yield block

    def _clone_person_links(self, person_links, event_exists=False):
        attrs = get_attrs_to_clone(SessionBlockPersonLink)
        for old_link in person_links:
            link = SessionBlockPersonLink()
            link.populate_from_attrs(old_link, attrs)
            current_person = self._person_map[old_link.person]
            if event_exists and current_person.user_id in self._new_event_persons:
                link.person = self._new_event_persons[current_person.user_id]
            else:
                link.person = current_person
            yield link

    def _synchronize_friendly_id(self, new_event):
        new_event._last_friendly_session_id = (
            db.session
            .query(db.func.max(Session.friendly_id))
            .filter(Session.event_id == new_event.id)
            .scalar() or 0
        )
