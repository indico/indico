# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import OrderedDict
from datetime import timedelta
from operator import attrgetter

from flask import flash, request, session
from sqlalchemy.orm import joinedload, subqueryload

from indico.core.db import db
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.persons import ContributionPersonLink
from indico.modules.events.models.persons import EventPerson
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

    def __init__(self, event):
        super(ContributionListGenerator, self).__init__(event)
        self.default_list_config = {'filters': {'items': {}}}

        session_empty = {None: _('No session')}
        track_empty = {None: _('No track')}
        type_empty = {None: _('No type')}
        session_choices = OrderedDict((unicode(s.id), s.title) for s in sorted(self.event.sessions,
                                                                               key=attrgetter('title')))
        track_choices = OrderedDict((unicode(t.id), t.title) for t in sorted(self.event.tracks,
                                                                             key=attrgetter('title')))
        type_choices = OrderedDict((unicode(t.id), t.name) for t in sorted(self.event.contribution_types,
                                                                           key=attrgetter('name')))
        self.static_items = OrderedDict([
            ('session', {'title': _('Session'),
                         'filter_choices': OrderedDict(session_empty.items() + session_choices.items())}),
            ('track', {'title': _('Track'),
                       'filter_choices': OrderedDict(track_empty.items() + track_choices.items())}),
            ('type', {'title': _('Type'),
                      'filter_choices': OrderedDict(type_empty.items() + type_choices.items())}),
            ('status', {'title': _('Status'), 'filter_choices': {'scheduled': _('Scheduled'),
                                                                 'unscheduled': _('Not scheduled')}}),
            ('speakers', {'title': _('Speakers'), 'filter_choices': {'registered': _('Registered'),
                                                                     'not_registered': _('Not registered')}})
        ])

        self.list_config = self._get_config()

    def _build_query(self):
        timetable_entry_strategy = joinedload('timetable_entry')
        timetable_entry_strategy.lazyload('*')
        return (Contribution.query.with_parent(self.event)
                .order_by(Contribution.friendly_id)
                .options(timetable_entry_strategy,
                         joinedload('session'),
                         subqueryload('person_links'),
                         db.undefer('subcontribution_count'),
                         db.undefer('attachment_count'),
                         db.undefer('is_scheduled')))

    def _filter_list_entries(self, query, filters):
        if not filters.get('items'):
            return query
        criteria = []
        if 'status' in filters['items']:
            filtered_statuses = filters['items']['status']
            status_criteria = []
            if 'scheduled' in filtered_statuses:
                status_criteria.append(Contribution.is_scheduled)
            if 'unscheduled' in filtered_statuses:
                status_criteria.append(~Contribution.is_scheduled)
            if status_criteria:
                criteria.append(db.or_(*status_criteria))

        if 'speakers' in filters['items']:
            registration_join_criteria = db.and_(
                Registration.event_id == Contribution.event_id,
                Registration.is_active,
                ContributionPersonLink.is_speaker,
                (Registration.user_id == EventPerson.user_id) | (Registration.email == EventPerson.email)
            )
            contrib_query = (db.session.query(Contribution.id)
                             .filter(Contribution.event_id == self.event.id)
                             .join(ContributionPersonLink)
                             .join(EventPerson)
                             .join(Registration, registration_join_criteria))
            registered_contribs = {id_ for id_, in contrib_query}

            filtered_speakers = filters['items']['speakers']
            speakers_criteria = []
            if 'registered' in filtered_speakers:
                speakers_criteria.append(Contribution.id.in_(registered_contribs))
            if 'not_registered' in filtered_speakers:
                speakers_criteria.append(~Contribution.id.in_(registered_contribs))
            if speakers_criteria:
                criteria.append(db.or_(*speakers_criteria))

        filter_cols = {'session': Contribution.session_id,
                       'track': Contribution.track_id,
                       'type': Contribution.type_id}
        for key, column in filter_cols.iteritems():
            ids = set(filters['items'].get(key, ()))
            if not ids:
                continue
            column_criteria = []
            if None in ids:
                column_criteria.append(column.is_(None))
            if ids - {None}:
                column_criteria.append(column.in_(ids - {None}))
            criteria.append(db.or_(*column_criteria))
        return query.filter(*criteria)

    def get_list_kwargs(self):
        if self.check_access:
            self.event.preload_all_acl_entries()
        contributions_query = self._build_query()
        total_entries = (sum(1 for c in contributions_query if c.can_access(session.user)) if self.check_access else
                         contributions_query.count())
        contributions = [c for c in self._filter_list_entries(contributions_query, self.list_config['filters'])
                         if not self.check_access or c.can_access(session.user)]
        sessions = [{'id': s.id, 'title': s.title, 'colors': s.colors} for s in self.event.sessions]
        tracks = [{'id': int(t.id), 'title': t.title_with_group} for t in self.event.tracks]
        total_duration = (sum((c.duration for c in contributions), timedelta()),
                          sum((c.duration for c in contributions if c.timetable_entry), timedelta()))
        selected_entry = request.args.get('selected')
        selected_entry = int(selected_entry) if selected_entry else None
        registered_persons = get_registered_event_persons(self.event)
        return {'contribs': contributions, 'sessions': sessions, 'tracks': tracks, 'total_entries': total_entries,
                'total_duration': total_duration, 'selected_entry': selected_entry,
                'registered_persons': registered_persons}

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
