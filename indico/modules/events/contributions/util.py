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
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.util import serialize_event_person
from indico.modules.fulltextindexes.models.events import IndexedEvent
from indico.util.i18n import _
from indico.util.reporter import ReporterBase
from indico.util.string import to_unicode
from indico.web.flask.templating import get_template_module
from MaKaC.common.cache import GenericCache


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


def serialize_contribution_person_link(person_link):
    """Serialize ContributionPersonLink to JSON-like object"""
    data = serialize_event_person(person_link.person)
    data['isSpeaker'] = person_link.is_speaker
    data['authorType'] = person_link.author_type.value
    data['isSubmitter'] = person_link.is_submitter
    return data


class ContributionReporter(ReporterBase):
    """Class performing reporting and filtering actions in the contribution
    report
    """
    REPORT_ID = 'contribution_report'
    DEFAULT_REPORT_CONFIG = {'filters': {'items': {}}}
    FILTERABLE_ITEMS = OrderedDict([
        ('session', {
            'title': _('Session'),
            'filter_choices': {}
        }),
        ('track', {
            'title': _('Track'),
            'filter_choices': {}
        }),
        ('type', {
            'title': _('Type'),
            'filter_choices': {}
        }),
        ('status', {
            'title': _('Status'),
            'filter_choices': {}
        })
    ])

    cache = GenericCache('contrib-report-config')

    @classmethod
    def build_query(cls, event):
        timetable_entry_strategy = joinedload('timetable_entry')
        timetable_entry_strategy.lazyload('*')
        return (event.contributions
                .filter_by(is_deleted=False)
                .order_by(Contribution.friendly_id)
                .options(timetable_entry_strategy))

    @classmethod
    def filter_report_entries(cls, query, filters):
        if not filters.get('items'):
            return query
        item_criteria = []
        if 'session' in filters['items']:
            session_ids = filters['items']['session']
            item_criteria.append(Contribution.session_id.in_(session_ids))
        if 'track' in filters['items']:
            track_ids = filters['items']['track']
            item_criteria.append(Contribution.track_id.in_(track_ids))
        if 'type' in filters['items']:
            type_ids = filters['items']['type']
            item_criteria.append(Contribution.type_id.in_(type_ids))
        # TODO: Handle contribution status
        return query.filter(db.or_(*item_criteria))

    @classmethod
    def get_contrib_report_args(cls, event, filters):
        contributions_query = cls.build_query(event)
        total_entries = contributions_query.count()
        contributions = cls.filter_report_entries(contributions_query, filters).all()
        sessions = [{'id': s.id, 'title': s.title} for s in event.sessions.filter_by(is_deleted=False)]
        tracks = [{'id': int(t.id), 'title': to_unicode(t.getTitle())} for t in event.as_legacy.getTrackList()]
        return {'contribs': contributions, 'sessions': sessions, 'tracks': tracks, 'total_entries': total_entries}

    @classmethod
    def render_contrib_report(cls, event, filters, contrib=None):
        """Render the contribution report template components.

        :param event: The event of the contribution report.
        :param filters: The user specified filters.
        :param contrib: Used in RHs responsible for CRUD operations on a
        contribution.
        :returns: dict - dict containing the report's entries, the fragment of
        displayed entries and whether the contrib passed is displayed in the
        results.
        """
        contr_report_args = cls.get_contrib_report_args(event, filters)
        total_entries = contr_report_args.pop('total_entries')
        tpl = get_template_module('events/contributions/management/_contribution_report.html')
        fragment = tpl.render_displayed_entries_fragment(len(contr_report_args['contribs']), total_entries)
        return {'html': tpl.render_contrib_report(event=event, **contr_report_args),
                'displayed_records_fragment': fragment,
                'hide_contrib': contrib not in contr_report_args['contribs'] if contrib else None}

    @classmethod
    def flash_info_message(cls, contrib, hide_contrib):
        if hide_contrib:
            flash(_("The contribution '{}' is not displayed in the list due to the enabled filters")
                  .format(contrib.title), 'info')
