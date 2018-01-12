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

from copy import deepcopy

from sqlalchemy.orm import joinedload, subqueryload, undefer

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import clone_principals
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.events.cloning import EventCloner
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.fields import ContributionField, ContributionFieldValue
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.contributions.models.references import ContributionReference, SubContributionReference
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.contributions.models.types import ContributionType
from indico.util.i18n import _


class ContributionTypeCloner(EventCloner):
    name = 'contribution_types'
    friendly_name = _('Contribution types')
    is_internal = True

    # We do not override `is_available` as we have cloners depending
    # on this internal cloner even if it won't clone anything.

    def run(self, new_event, cloners, shared_data):
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

    def run(self, new_event, cloners, shared_data):
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
    is_internal = True

    # We do not override `is_available` as we have cloners depending
    # on this internal cloner even if it won't clone anything.

    def run(self, new_event, cloners, shared_data):
        self._person_map = shared_data['event_persons']['person_map']
        self._session_map = shared_data['sessions']['session_map']
        self._session_block_map = shared_data['sessions']['session_block_map']
        self._contrib_type_map = shared_data['contribution_types']['contrib_type_map']
        self._contrib_field_map = shared_data['contribution_fields']['contrib_field_map']
        self._contrib_map = {}
        self._subcontrib_map = {}
        with db.session.no_autoflush:
            self._clone_contribs(new_event)
        self._synchronize_friendly_id(new_event)
        db.session.flush()
        return {'contrib_map': self._contrib_map, 'subcontrib_map': self._subcontrib_map}

    def _clone_contribs(self, new_event):
        attrs = (get_simple_column_attrs(Contribution) | {'own_room', 'own_venue'}) - {'abstract_id'}
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
            contrib = Contribution()
            contrib.populate_from_attrs(old_contrib, attrs)
            contrib.subcontributions = list(self._clone_subcontribs(old_contrib.subcontributions))
            contrib.acl_entries = clone_principals(ContributionPrincipal, old_contrib.acl_entries)
            contrib.references = list(self._clone_references(ContributionReference, old_contrib.references))
            contrib.person_links = list(self._clone_person_links(ContributionPersonLink, old_contrib.person_links))
            contrib.field_values = list(self._clone_fields(old_contrib.field_values))
            if old_contrib.type is not None:
                contrib.type = self._contrib_type_map[old_contrib.type]
            if old_contrib.session is not None:
                contrib.session = self._session_map[old_contrib.session]
            if old_contrib.session_block is not None:
                contrib.session_block = self._session_block_map[old_contrib.session_block]
            new_event.contributions.append(contrib)
            self._contrib_map[old_contrib] = contrib

    def _clone_subcontribs(self, subcontribs):
        attrs = get_simple_column_attrs(SubContribution)
        for old_subcontrib in subcontribs:
            subcontrib = SubContribution()
            subcontrib.populate_from_attrs(old_subcontrib, attrs)
            subcontrib.references = list(self._clone_references(SubContributionReference, old_subcontrib.references))
            subcontrib.person_links = list(self._clone_person_links(SubContributionPersonLink,
                                                                    old_subcontrib.person_links))
            self._subcontrib_map[old_subcontrib] = subcontrib
            yield subcontrib

    def _clone_references(self, cls, references):
        attrs = get_simple_column_attrs(cls) | {'reference_type'}
        for old_ref in references:
            ref = cls()
            ref.populate_from_attrs(old_ref, attrs)
            yield ref

    def _clone_person_links(self, cls, person_links):
        attrs = get_simple_column_attrs(cls)
        for old_link in person_links:
            link = cls()
            link.populate_from_attrs(old_link, attrs)
            link.person = self._person_map[old_link.person]
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
