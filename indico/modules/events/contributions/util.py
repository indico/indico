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

from collections import defaultdict, OrderedDict

from flask import flash
from sqlalchemy.orm import load_only, contains_eager, noload, joinedload

from indico.core.db import db
from indico.modules.events.models.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.persons import SubContributionPersonLink
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.util import serialize_person_link, ReporterBase
from indico.modules.fulltextindexes.models.events import IndexedEvent
from indico.util.i18n import _
from indico.util.string import to_unicode
from indico.web.flask.templating import get_template_module


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
    return data


def serialize_contribution_person_link(person_link, is_submitter=None):
    """Serialize ContributionPersonLink to JSON-like object"""
    data = serialize_person_link(person_link)
    data['isSpeaker'] = person_link.is_speaker
    data['authorType'] = person_link.author_type.value
    if not isinstance(person_link, SubContributionPersonLink):
        data['isSubmitter'] = person_link.is_submitter if is_submitter is None else is_submitter
    return data


class ContributionReporter(ReporterBase):
    """Reporting and filtering actions in the contribution report."""

    endpoint = '.manage_contributions'
    report_link_type = 'contribution'

    def __init__(self, event):
        super(ContributionReporter, self).__init__(event)
        self.default_report_config = {'filters': {'items': {}}}

        session_empty = {None: 'No session'}
        track_empty = {None: 'No track'}
        type_empty = {None: 'No type'}
        session_choices = {unicode(s.id): s.title for s in self.report_event.sessions.filter_by(is_deleted=False)}
        track_choices = {unicode(t.id): to_unicode(t.getTitle()) for t in self.report_event.as_legacy.getTrackList()}
        type_choices = {unicode(t.id): t.name for t in self.report_event.contribution_types}
        self.filterable_items = OrderedDict([
            ('session', {'title': _('Session'),
                         'filter_choices': OrderedDict(session_empty.items() + session_choices.items())}),
            ('track', {'title': _('Track'),
                       'filter_choices': OrderedDict(track_empty.items() + track_choices.items())}),
            ('type', {'title': _('Type'),
                      'filter_choices': OrderedDict(type_empty.items() + type_choices.items())}),
            # TODO: Handle contribution status
            ('status', {'title': _('Status'), 'filter_choices': {}})
        ])

        self.report_config = self._get_config()

    def build_query(self):
        timetable_entry_strategy = joinedload('timetable_entry')
        timetable_entry_strategy.lazyload('*')
        return (self.report_event.contributions
                .filter_by(is_deleted=False)
                .order_by(Contribution.friendly_id)
                .options(timetable_entry_strategy,
                         joinedload('session'),
                         db.undefer('subcontribution_count')))

    def filter_report_entries(self, query, filters):
        if not filters.get('items'):
            return query
        criteria = []
        # TODO: Handle contribution status
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

    def get_contrib_report_kwargs(self):
        contributions_query = self.build_query()
        total_entries = contributions_query.count()
        contributions = self.filter_report_entries(contributions_query, self.report_config['filters']).all()
        sessions = [{'id': s.id, 'title': s.title, 'colors': s.colors}
                    for s in self.report_event.sessions.filter_by(is_deleted=False)]
        tracks = [{'id': int(t.id), 'title': to_unicode(t.getTitle())}
                  for t in self.report_event.as_legacy.getTrackList()]
        return {'contribs': contributions, 'sessions': sessions, 'tracks': tracks, 'total_entries': total_entries}

    def render_contrib_report(self, contrib=None):
        """Render the contribution report template components.

        :param contrib: Used in RHs responsible for CRUD operations on a
                        contribution.
        :return: dict containing the report's entries, the fragment of
                 displayed entries and whether the contrib passed is displayed
                 in the results.
        """
        contrib_report_kwargs = self.get_contrib_report_kwargs()
        total_entries = contrib_report_kwargs.pop('total_entries')
        tpl = get_template_module('events/contributions/management/_contribution_report.html')
        fragment = tpl.render_displayed_entries_fragment(len(contrib_report_kwargs['contribs']), total_entries)
        return {'html': tpl.render_contrib_report(self.report_event, total_entries, **contrib_report_kwargs),
                'counter': fragment,
                'hide_contrib': contrib not in contrib_report_kwargs['contribs'] if contrib else None}

    def flash_info_message(self, contrib):
        flash(_("The contribution '{}' is not displayed in the list due to the enabled filters")
              .format(contrib.title), 'info')
