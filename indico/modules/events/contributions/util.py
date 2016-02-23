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
from sqlalchemy.orm import load_only, contains_eager, noload, joinedload, subqueryload

from indico.core.db import db
from indico.modules.events.models.events import Event
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.persons import SubContributionPersonLink
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.util import serialize_person_link, ReporterBase
from indico.modules.attachments.util import get_attached_items
from indico.util.date_time import format_human_timedelta, format_date
from indico.util.i18n import _
from indico.util.string import to_unicode
from indico.util.user import iter_acl
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data


def get_events_with_linked_contributions(user, from_dt=None, to_dt=None):
    """Returns a dict with keys representing event_id and the values containing
    data about the user rights for contributions within the event

    :param user: A `User`
    :param from_dt: The earliest event start time to look for
    :param to_dt: The latest event start time to look for
    """
    query = (user.in_contribution_acls
             .options(load_only('contribution_id', 'roles', 'full_access', 'read_access'))
             .options(noload('*'))
             .options(contains_eager(ContributionPrincipal.contribution).load_only('event_id'))
             .join(Contribution)
             .join(Event, Event.id == Contribution.event_id)
             .filter(~Contribution.is_deleted, ~Event.is_deleted, Event.starts_between(from_dt, to_dt)))
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
    if not isinstance(person_link, SubContributionPersonLink):
        data['authorType'] = person_link.author_type.value
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
        session_choices = {unicode(s.id): s.title for s in self.report_event.sessions}
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
        return (Contribution.query.with_parent(self.report_event)
                .order_by(Contribution.friendly_id)
                .options(timetable_entry_strategy,
                         joinedload('session'),
                         subqueryload('person_links'),
                         db.undefer('subcontribution_count'),
                         db.undefer('attachment_count'),
                         db.undefer('is_scheduled')))

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
        sessions = [{'id': s.id, 'title': s.title, 'colors': s.colors} for s in self.report_event.sessions]
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
        tpl_contrib = get_template_module('events/contributions/management/_contribution_report.html')
        tpl_reports = get_template_module('events/management/_reports.html')
        fragment = tpl_reports.render_displayed_entries_fragment(len(contrib_report_kwargs['contribs']), total_entries)
        return {'html': tpl_contrib.render_contrib_report(self.report_event, total_entries, **contrib_report_kwargs),
                'counter': fragment,
                'hide_contrib': contrib not in contrib_report_kwargs['contribs'] if contrib else None}

    def flash_info_message(self, contrib):
        flash(_("The contribution '{}' is not displayed in the list due to the enabled filters")
              .format(contrib.title), 'info')


def generate_spreadsheet_from_contributions(contributions):
    """Return a tuple consisting of spreadsheet columns and respective
    contribution values"""

    headers = ['ID', 'Title', 'Description', 'Date', 'Duration', 'Type', 'Session', 'Track', 'Presenters', 'Materials']
    rows = []
    for c in contributions:
        contrib_data = {'ID': c.id, 'Title': c.title, 'Description': c.description,
                        'Duration': format_human_timedelta(c.duration),
                        'Date': format_date(c.timetable_entry.start_dt) if c.timetable_entry else None,
                        'Type': c.type.name if c.type else None,
                        'Session': c.session.title if c.session else None,
                        'Track': c.track.title if c.track else None,
                        'Materials': None,
                        'Presenters': ', '.join(speaker.person.full_name for speaker in c.speakers)}

        attachments = []
        attached_items = get_attached_items(c)
        for attachment in attached_items.get('files', []):
            attachments.append(attachment.absolute_download_url)

        for folder in attached_items.get('folders', []):
            for attachment in folder.attachments:
                attachments.append(attachment.absolute_download_url)

        if attachments:
            contrib_data['Materials'] = ', '.join(attachments)
        rows.append(contrib_data)
    return headers, rows


def make_contribution_form(event):
    """Extends the contribution WTForm to add the extra fields.

    Each extra field will use a field named ``custom_ID``.

    :param event: The `Event` for which to create the contribution form.
    :return: A `ContributionForm` subclass.
    """
    from indico.modules.events.contributions.forms import ContributionForm

    form_class = type(b'_ContributionForm', (ContributionForm,), {})
    for custom_field in event.contribution_fields:
        field_impl = custom_field.field
        if field_impl is None:
            # field definition is not available anymore
            continue
        name = 'custom_{}'.format(custom_field.id)
        setattr(form_class, name, field_impl.create_wtf_field())
    return form_class


def contribution_type_row(contrib_type):
    template = get_template_module('events/contributions/management/_types_table.html')
    html = template.types_table_row(contrib_type=contrib_type)
    return jsonify_data(html_row=html, flash=False)


def get_contributions_with_user_as_submitter(event, user):
    """Get a list of contributions in which the `user` has submission rights"""
    contribs = (Contribution.query.with_parent(event)
                .options(joinedload('acl_entries'))
                .filter(Contribution.acl_entries.any(ContributionPrincipal.has_management_role('submit')))
                .all())
    return {c for c in contribs if any(user in entry.principal for entry in iter_acl(c.acl_entries))}
