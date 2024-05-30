# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta
from operator import attrgetter

from flask import flash, request, session
from sqlalchemy.orm import joinedload, subqueryload

from indico.core.db import db
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.fields import ContributionField, ContributionFieldValue
from indico.modules.events.contributions.models.persons import ContributionPersonLink
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.registration.util import get_registered_event_persons
from indico.modules.events.util import ListGeneratorBase
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module


class ContributionListGenerator(ListGeneratorBase):
    """Listing and filtering actions in the contribution list."""

    endpoint = '.manage_contributions'
    list_link_type = 'contribution'
    check_access = False
    show_custom_fields = True

    def __init__(self, event):
        super().__init__(event)
        self.default_list_config = {
            'items': ('type', 'session', 'track'),
            'filters': {'fields': {}, 'items': {}, 'extra': {}},
        }

        session_empty = {None: _('No session')}
        track_empty = {None: _('No track')}
        type_empty = {None: _('No type')}
        session_choices = {str(s.id): s.title for s in sorted(self.event.sessions, key=attrgetter('title'))}
        track_choices = {str(t.id): t.title for t in sorted(self.event.tracks, key=attrgetter('title'))}
        type_choices = {str(t.id): t.name for t in sorted(self.event.contribution_types, key=attrgetter('name'))}
        self.static_items = {
            'type': {'title': _('Type'),
                     'filter_choices': type_empty | type_choices},
            'session': {'title': _('Session'),
                        'filter_choices': session_empty | session_choices},
            'track': {'title': _('Track'),
                      'filter_choices': track_empty | track_choices},
        }

        self.list_config = self._get_config()
        self.extra_filters = {
            'people': {'title': _('People'), 'filter_choices': {'registered': _('Registered'),
                                                                'not_registered': _('Nobody registered')}},
            'speakers': {'title': _('Speakers'), 'filter_choices': {'registered': _('Registered'),
                                                                    'not_registered': _('Nobody registered')}},
            'status': {'title': _('Status'), 'filter_choices': {'scheduled': _('Scheduled'),
                                                                'unscheduled': _('Not scheduled')}},
        }

    def _get_static_columns(self, ids):
        """Retrieve information needed for the header of the static columns.

        :return: a list of {'id': ..., 'caption': ...} dicts
        """
        return [{'id': id_, 'caption': self.static_items[id_]['title']} for id_ in self.static_items if id_ in ids]

    def get_all_custom_fields(self):
        """Return the list of contribution fields for the event."""
        return self.event.contribution_fields.all() if self.show_custom_fields else []

    def _get_sorted_custom_fields(self, item_ids):
        """
        Return the contribution fields ordered by their position in
        the abstract form.
        """
        if not item_ids or not self.show_custom_fields:
            return []
        return (ContributionField.query
                .with_parent(self.event)
                .filter(ContributionField.id.in_(item_ids))
                .order_by(ContributionField.position)
                .all())

    def _get_filters_from_request(self):
        filters = super()._get_filters_from_request()
        for field in self.event.contribution_fields:
            if field.field_type == 'single_choice':
                options = [x if x != 'None' else None for x in request.form.getlist(f'field_{field.id}')]
                if options:
                    filters['fields'][str(field.id)] = options
        # Ensure enum filters remain as integers
        for idx, value in enumerate(filters['items'].get('state', [])):
            filters['items']['state'][idx] = int(value)
        return filters

    def _build_query(self):
        timetable_entry_strategy = joinedload('timetable_entry')
        timetable_entry_strategy.lazyload('*')
        return (Contribution.query.with_parent(self.event)
                .order_by(Contribution.friendly_id)
                .options(timetable_entry_strategy,
                         joinedload('session'),
                         subqueryload('field_values'),
                         subqueryload('person_links'),
                         db.undefer('subcontribution_count'),
                         db.undefer('attachment_count'),
                         db.undefer('is_scheduled')))

    def _build_registration_query(self, is_speaker=False):
        registration_join_criteria = [
            Registration.event_id == Contribution.event_id,
            Registration.is_active,
            (Registration.user_id == EventPerson.user_id) | (Registration.email == EventPerson.email)
        ]
        if is_speaker:
            registration_join_criteria.append(ContributionPersonLink.is_speaker)
        return (db.session.query(Contribution.id)
                .filter(Contribution.event_id == self.event.id)
                .join(ContributionPersonLink)
                .join(EventPerson)
                .join(Registration, db.and_(*registration_join_criteria))
                .join(RegistrationForm, db.and_(RegistrationForm.id == Registration.registration_form_id,
                                                ~RegistrationForm.is_deleted)))

    def _filter_list_entries(self, query, filters):
        criteria = []
        field_filters = filters.get('fields')
        item_filters = filters.get('items')
        extra_filters = filters.get('extra')

        if not (field_filters or item_filters or extra_filters):
            return query

        if field_filters:
            for field_id, field_values in field_filters.items():
                field_values = set(field_values)

                field_criteria = []
                if None in field_values:
                    # Handle the case when there is no value in
                    # 'Contribution.field_values' matching the 'field_id'.
                    # This can happen when custom fields are added after the
                    # contribution had already been created or when the field is left
                    # empty.
                    # In these cases, we still want to show the contributions.
                    field_values.discard(None)
                    field_criteria += [
                        ~Contribution.field_values.any(ContributionFieldValue.contribution_field_id == field_id),
                        Contribution.field_values.any(db.and_(
                            ContributionFieldValue.contribution_field_id == field_id,
                            ContributionFieldValue.data.op('#>>')('{}').is_(None)
                        ))
                    ]

                if field_values:
                    field_criteria.append(Contribution.field_values.any(db.and_(
                        ContributionFieldValue.contribution_field_id == field_id,
                        ContributionFieldValue.data.op('#>>')('{}').in_(field_values)
                    )))

                criteria.append(db.or_(*field_criteria))

        if item_filters:
            filter_cols = {'session': Contribution.session_id,
                           'track': Contribution.track_id,
                           'type': Contribution.type_id}
            for key, column in filter_cols.items():
                ids = set(filters['items'].get(key, ()))
                if not ids:
                    continue
                column_criteria = []
                if None in ids:
                    column_criteria.append(column.is_(None))
                if ids - {None}:
                    column_criteria.append(column.in_(ids - {None}))
                criteria.append(db.or_(*column_criteria))

        if extra_filters:
            if 'status' in filters['extra']:
                filtered_statuses = filters['extra']['status']
                status_criteria = []
                if 'scheduled' in filtered_statuses:
                    status_criteria.append(Contribution.is_scheduled)
                if 'unscheduled' in filtered_statuses:
                    status_criteria.append(~Contribution.is_scheduled)
                if status_criteria:
                    criteria.append(db.or_(*status_criteria))
            if 'people' in filters['extra']:
                filtered_people = filters['extra'].get('people')
                contrib_query = self._build_registration_query()
                people_criteria = []
                if 'registered' in filtered_people:
                    people_criteria.append(Contribution.id.in_(contrib_query))
                if 'not_registered' in filtered_people:
                    people_criteria.append(~Contribution.id.in_(contrib_query))
                if people_criteria:
                    criteria.append(db.or_(*people_criteria))
            if 'speakers' in filters['extra']:
                filtered_people = filters['extra'].get('speakers')
                contrib_query = self._build_registration_query(is_speaker=True)
                people_criteria = []
                if 'registered' in filtered_people:
                    people_criteria.append(Contribution.id.in_(contrib_query))
                if 'not_registered' in filtered_people:
                    people_criteria.append(~Contribution.id.in_(contrib_query))
                if people_criteria:
                    criteria.append(db.or_(*people_criteria))

        return query.filter(*criteria)

    def get_list_kwargs(self):
        if self.check_access:
            self.event.preload_all_acl_entries()
        list_config = self._get_config()
        contributions_query = self._build_query()
        total_entries = (sum(1 for c in contributions_query if c.can_access(session.user)) if self.check_access else
                         contributions_query.count())
        contributions = [c for c in self._filter_list_entries(contributions_query, list_config['filters'])
                         if not self.check_access or c.can_access(session.user)]
        sessions = [{'id': s.id, 'title': s.title, 'colors': s.colors} for s in self.event.sessions]
        tracks = [{'id': int(t.id), 'title': t.title_with_group} for t in self.event.tracks]
        total_duration = (sum((c.duration for c in contributions), timedelta()),
                          sum((c.duration for c in contributions if c.timetable_entry), timedelta()))
        selected_entry = request.args.get('selected')
        selected_entry = int(selected_entry) if selected_entry else None
        registered_persons = get_registered_event_persons(self.event)
        dynamic_item_ids, static_item_ids = self._split_item_ids(list_config.get('items', ()), 'dynamic')
        static_columns = self._get_static_columns(static_item_ids)
        dynamic_columns = self._get_sorted_custom_fields(dynamic_item_ids)
        has_types = bool(self.event.contribution_types.all())
        return {'contribs': contributions, 'sessions': sessions, 'tracks': tracks, 'total_entries': total_entries,
                'total_duration': total_duration, 'selected_entry': selected_entry,
                'registered_persons': registered_persons, 'static_columns': static_columns,
                'dynamic_columns': dynamic_columns, 'has_types': has_types}

    def render_list(self, contrib=None):
        """Render the contribution list template components.

        :param contrib: Used in RHs responsible for CRUD operations on a
                        contribution.
        :return: dict containing the list's entries, the fragment of
                 displayed entries and whether the contribution passed is
                 displayed in the results.
        """
        contrib_list_kwargs = self.get_list_kwargs()
        total_entries = contrib_list_kwargs.pop('total_entries')
        selected_entry = contrib_list_kwargs.pop('selected_entry')
        tpl_contrib = get_template_module('events/contributions/management/_contribution_list.html')
        tpl_lists = get_template_module('events/management/_lists.html')
        contribs = contrib_list_kwargs['contribs']
        filter_statistics = tpl_lists.render_filter_statistics(len(contribs), total_entries,
                                                               contrib_list_kwargs.pop('total_duration'))
        return {'html': tpl_contrib.render_contrib_list(self.event, total_entries, **contrib_list_kwargs),
                'hide_contrib': contrib not in contribs if contrib else None,
                'filter_statistics': filter_statistics,
                'selected_entry': selected_entry}

    def flash_info_message(self, contrib):
        flash(_("The contribution '{}' is not displayed in the list due to the enabled filters")
              .format(contrib.title), 'info')


class ContributionDisplayListGenerator(ContributionListGenerator):
    endpoint = '.contribution_list'
    list_link_type = 'contribution_display'
    check_access = True

    def __init__(self, event):
        super().__init__(event)
        self.extra_filters = {}

    def render_contribution_list(self):
        """Render the contribution list template components.

        :return: dict containing the list's entries, the fragment of
                 displayed entries and whether the contribution passed is displayed
                 in the results.
        """
        contrib_list_kwargs = self.get_list_kwargs()
        total_entries = contrib_list_kwargs.pop('total_entries')
        contribs = contrib_list_kwargs['contribs']
        tpl = get_template_module('events/contributions/display/_contribution_list.html')
        tpl_lists = get_template_module('events/management/_lists.html')
        return {'html': tpl.render_contribution_list(self.event, self.event.display_tzinfo, contribs, total_entries),
                'counter': tpl_lists.render_displayed_entries_fragment(len(contribs), total_entries)}
