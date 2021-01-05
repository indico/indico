# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from copy import deepcopy

from sqlalchemy.orm import joinedload, subqueryload, undefer

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import clone_principals
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.cloning import EventCloner
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.fields import ContributionField, ContributionFieldValue
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.contributions.models.references import ContributionReference, SubContributionReference
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.contributions.models.types import ContributionType
from indico.modules.events.timetable.operations import schedule_contribution
from indico.util.i18n import _


class ContributionTypeCloner(EventCloner):
    name = 'contribution_types'
    friendly_name = _('Contribution types')
    is_internal = True

    # We do not override `is_available` as we have cloners depending
    # on this internal cloner even if it won't clone anything.

    def has_conflicts(self, target_event):
        return target_event.contribution_types.has_rows()

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._contrib_type_map = {}
        self._clone_contrib_types(new_event)
        db.session.flush()
        return {'contrib_type_map': self._contrib_type_map}

    def _clone_contrib_types(self, new_event):
        attrs = get_simple_column_attrs(ContributionType)
        for old_contrib_type in self.old_event.contribution_types:
            contrib_type = ContributionType()
            contrib_type.populate_from_attrs(old_contrib_type, attrs)
            new_event.contribution_types.append(contrib_type)
            self._contrib_type_map[old_contrib_type] = contrib_type


class ContributionFieldCloner(EventCloner):
    name = 'contribution_fields'
    friendly_name = _('Contribution fields')
    is_internal = True  # XXX: does it make sense to expose this cloner?

    # We do not override `is_available` as we have cloners depending
    # on this internal cloner even if it won't clone anything.

    def has_conflicts(self, target_event):
        return target_event.contribution_fields.has_rows()

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._contrib_field_map = {}
        self._clone_contrib_fields(new_event)
        db.session.flush()
        return {'contrib_field_map': self._contrib_field_map}

    def _clone_contrib_fields(self, new_event):
        attrs = get_simple_column_attrs(ContributionField) - {'field_data'}
        for old_contrib_field in self.old_event.contribution_fields:
            contrib_field = ContributionField()
            contrib_field.populate_from_attrs(old_contrib_field, attrs)
            contrib_field.field_data = deepcopy(old_contrib_field.field_data)
            new_event.contribution_fields.append(contrib_field)
            self._contrib_field_map[old_contrib_field] = contrib_field


class ContributionCloner(EventCloner):
    name = 'contributions'
    friendly_name = _('Contributions')
    requires = {'event_persons', 'sessions', 'contribution_types', 'contribution_fields'}
    uses = {'event_roles'}
    is_internal = True

    # We do not override `is_available` as we have cloners depending
    # on this internal cloner even if it won't clone anything.

    def has_conflicts(self, target_event):
        return bool(target_event.contributions)

    @classmethod
    @no_autoflush
    def clone_single_contribution(cls, contribution, preserve_session=False):
        """Clone a single contribution within the same event.

        :param contribution: The `Contribution` to clone
        :param preserve_session: Whether to assign and schedule
        :return: The newly created contribution
        """
        event = contribution.event
        cloner = cls(event)
        cloner._event_role_map = dict(zip(event.roles, event.roles))
        cloner._person_map = dict(zip(event.persons, event.persons))
        cloner._session_map = {contribution.session: contribution.session}
        cloner._session_block_map = {contribution.session_block: contribution.session_block}
        cloner._contrib_type_map = {contribution.type: contribution.type}
        cloner._contrib_field_map = dict(zip(event.contribution_fields, event.contribution_fields))
        cloner._contrib_map = {}
        cloner._subcontrib_map = {}
        new_contribution = cloner._create_new_contribution(event, contribution,
                                                           preserve_session=preserve_session,
                                                           excluded_attrs={'friendly_id'})
        if preserve_session:
            entry = schedule_contribution(new_contribution, contribution.timetable_entry.start_dt,
                                          session_block=new_contribution.session_block)
            event.timetable_entries.append(entry)
        db.session.flush()
        return new_contribution

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._event_role_map = shared_data['event_roles']['event_role_map'] if 'event_roles' in cloners else None
        self._person_map = shared_data['event_persons']['person_map']
        self._session_map = shared_data['sessions']['session_map']
        self._session_block_map = shared_data['sessions']['session_block_map']
        self._contrib_type_map = shared_data['contribution_types']['contrib_type_map']
        self._contrib_field_map = shared_data['contribution_fields']['contrib_field_map']
        self._new_event_persons = {}
        if event_exists:
            self._new_event_persons = {person.user_id: person for person in new_event.persons
                                       if person.user_id is not None}
        self._contrib_map = {}
        self._subcontrib_map = {}
        with db.session.no_autoflush:
            self._clone_contribs(new_event, event_exists=event_exists)
        self._synchronize_friendly_id(new_event)
        db.session.flush()
        return {'contrib_map': self._contrib_map, 'subcontrib_map': self._subcontrib_map}

    def _create_new_contribution(self, event, old_contrib, preserve_session=True, excluded_attrs=None,
                                 event_exists=False):
        attrs = (get_simple_column_attrs(Contribution) | {'own_room', 'own_venue'}) - {'abstract_id'}
        if excluded_attrs is not None:
            attrs -= excluded_attrs
        new_contrib = Contribution()
        new_contrib.populate_from_attrs(old_contrib, attrs)
        new_contrib.subcontributions = list(self._clone_subcontribs(old_contrib.subcontributions,
                                                                    event_exists=event_exists))
        new_contrib.acl_entries = clone_principals(ContributionPrincipal, old_contrib.acl_entries, self._event_role_map)
        new_contrib.references = list(self._clone_references(ContributionReference, old_contrib.references))
        new_contrib.person_links = list(self._clone_person_links(ContributionPersonLink, old_contrib.person_links,
                                                                 event_exists=event_exists))
        new_contrib.field_values = list(self._clone_fields(old_contrib.field_values))
        if old_contrib.type is not None:
            new_contrib.type = self._contrib_type_map[old_contrib.type]
        if preserve_session:
            if old_contrib.session is not None:
                new_contrib.session = self._session_map[old_contrib.session]
            if old_contrib.session_block is not None:
                new_contrib.session_block = self._session_block_map[old_contrib.session_block]
        event.contributions.append(new_contrib)
        return new_contrib

    def _clone_contribs(self, new_event, event_exists=False):
        query = (Contribution.query.with_parent(self.old_event)
                 .options(undefer('_last_friendly_subcontribution_id'),
                          joinedload('own_venue'),
                          joinedload('own_room').lazyload('*'),
                          joinedload('session'),
                          joinedload('session_block').lazyload('session'),
                          joinedload('type'),
                          subqueryload('acl_entries'),
                          subqueryload('subcontributions').joinedload('references'),
                          subqueryload('references'),
                          subqueryload('person_links'),
                          subqueryload('field_values')))
        for old_contrib in query:
            self._contrib_map[old_contrib] = self._create_new_contribution(new_event, old_contrib,
                                                                           event_exists=event_exists)

    def _clone_subcontribs(self, subcontribs, event_exists=False):
        attrs = get_simple_column_attrs(SubContribution)
        for old_subcontrib in subcontribs:
            subcontrib = SubContribution()
            subcontrib.populate_from_attrs(old_subcontrib, attrs)
            subcontrib.references = list(self._clone_references(SubContributionReference, old_subcontrib.references))
            subcontrib.person_links = list(self._clone_person_links(SubContributionPersonLink,
                                                                    old_subcontrib.person_links,
                                                                    event_exists=event_exists))
            self._subcontrib_map[old_subcontrib] = subcontrib
            yield subcontrib

    def _clone_references(self, cls, references):
        attrs = get_simple_column_attrs(cls) | {'reference_type'}
        for old_ref in references:
            ref = cls()
            ref.populate_from_attrs(old_ref, attrs)
            yield ref

    def _clone_person_links(self, cls, person_links, event_exists=False):
        attrs = get_simple_column_attrs(cls)
        for old_link in person_links:
            link = cls()
            link.populate_from_attrs(old_link, attrs)
            current_person = self._person_map[old_link.person]
            if event_exists and current_person.user_id in self._new_event_persons:
                link.person = self._new_event_persons[current_person.user_id]
            else:
                link.person = current_person
            yield link

    def _clone_fields(self, fields):
        attrs = get_simple_column_attrs(ContributionFieldValue)
        for old_field_value in fields:
            field_value = ContributionFieldValue()
            field_value.contribution_field = self._contrib_field_map[old_field_value.contribution_field]
            field_value.populate_from_attrs(old_field_value, attrs)
            yield field_value

    def _synchronize_friendly_id(self, new_event):
        new_event._last_friendly_contribution_id = (
            db.session
            .query(db.func.max(Contribution.friendly_id))
            .filter(Contribution.event_id == new_event.id)
            .scalar() or 0
        )
