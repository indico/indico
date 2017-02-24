# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from collections import OrderedDict
from operator import attrgetter

from flask import request
from sqlalchemy.orm import subqueryload, undefer

from indico.core.db import db
from indico.modules.events.contributions import Contribution
from indico.modules.events.papers.models.revisions import PaperRevisionState, PaperRevision
from indico.modules.events.papers.settings import PaperReviewingRole
from indico.modules.events.util import ListGeneratorBase
from indico.modules.users import User
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module


class PaperListGeneratorBase(ListGeneratorBase):
    """Listing and filtering actions in a paper list."""

    def __init__(self, event):
        super(PaperListGeneratorBase, self).__init__(event)
        self.default_list_config = {
            'items': ('state',),
            'filters': {'items': {}}
        }

        state_not_submitted = {None: _('Not yet submitted')}
        track_empty = {None: _('No track')}
        session_empty = {None: _('No session')}
        type_empty = {None: _('No type')}
        state_choices = OrderedDict((state.value, state.title) for state in PaperRevisionState)
        unassigned_choices = OrderedDict((role.value, role.title) for role in PaperReviewingRole)
        track_choices = OrderedDict((unicode(t.id), t.title) for t in sorted(self.event.tracks,
                                                                             key=attrgetter('title')))
        session_choices = OrderedDict((unicode(s.id), s.title) for s in sorted(self.event.sessions,
                                                                               key=attrgetter('title')))
        type_choices = OrderedDict((unicode(t.id), t.name) for t in sorted(self.event.contribution_types,
                                                                           key=attrgetter('name')))

        if not event.cfp.content_reviewing_enabled:
            del unassigned_choices[PaperReviewingRole.content_reviewer.value]
        if not event.cfp.layout_reviewing_enabled:
            del unassigned_choices[PaperReviewingRole.layout_reviewer.value]

        self.static_items = OrderedDict([
            ('state', {'title': _('State'),
                       'filter_choices': OrderedDict(state_not_submitted.items() + state_choices.items())}),
            ('track', {'title': _('Track'),
                       'filter_choices': OrderedDict(track_empty.items() + track_choices.items())}),
            ('session', {'title': _('Session'),
                         'filter_choices': OrderedDict(session_empty.items() + session_choices.items())}),
            ('type', {'title': _('Type'),
                      'filter_choices': OrderedDict(type_empty.items() + type_choices.items())}),
            ('unassigned', {'title': _('Unassigned'), 'filter_choices': unassigned_choices}),
        ])
        self.list_config = self._get_config()

    def _get_static_columns(self, ids):
        """
        Retrieve information needed for the header of the static columns.

        :return: a list of {'id': ..., 'caption': ...} dicts
        """
        return [{'id': id_, 'caption': self.static_items[id_]['title']} for id_ in self.static_items if id_ in ids]

    def _build_query(self):
        return (Contribution.query.with_parent(self.event)
                .order_by(Contribution.friendly_id)
                .options(subqueryload('_paper_last_revision'),
                         subqueryload('paper_judges'),
                         subqueryload('paper_content_reviewers'),
                         subqueryload('paper_layout_reviewers'),
                         undefer('_paper_revision_count')))

    def _filter_list_entries(self, query, filters):
        if not filters.get('items'):
            return query
        criteria = []
        if 'state' in filters['items']:
            filtered_states = filters['items']['state']
            state_criteria = []
            for filter_state in filtered_states:
                if filter_state is None:
                    state_criteria.append(~Contribution._paper_last_revision.has())
                else:
                    state_criteria.append(Contribution._paper_last_revision
                                          .has(PaperRevision.state == int(filter_state)))
            if state_criteria:
                criteria.append(db.or_(*state_criteria))

        if 'unassigned' in filters['items']:
            role_map = {
                PaperReviewingRole.judge.value: Contribution.paper_judges,
                PaperReviewingRole.content_reviewer.value: Contribution.paper_content_reviewers,
                PaperReviewingRole.layout_reviewer.value: Contribution.paper_layout_reviewers,
            }
            filtered_roles = map(PaperReviewingRole, map(int, filters['items']['unassigned']))
            unassigned_criteria = [~role_map[role.value].any() for role in filtered_roles
                                   if (role == PaperReviewingRole.judge or
                                       self.event.cfp.get_reviewing_state(role.review_type))]
            if unassigned_criteria:
                criteria.append(db.or_(*unassigned_criteria))

        filter_cols = {'track': Contribution.track_id,
                       'session': Contribution.session_id,
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
        list_config = self._get_config()
        contributions_query = self._build_query()
        total_entries = contributions_query.count()
        contributions = self._filter_list_entries(contributions_query, self.list_config['filters']).all()
        selected_entry = request.args.get('selected')
        selected_entry = int(selected_entry) if selected_entry else None
        static_item_ids, dynamic_item_ids = self._split_item_ids(list_config['items'], 'static')
        static_columns = self._get_static_columns(static_item_ids)
        return {'contribs': contributions, 'total_entries': total_entries, 'selected_entry': selected_entry,
                'static_columns': static_columns}

    def render_list(self):
        """Render the contribution list template components.

        :return: dict containing the list's entries, the fragment of
                 displayed entries and whether the contribution passed is displayed
                 in the results.
        """
        contrib_list_kwargs = self.get_list_kwargs()
        total_entries = contrib_list_kwargs.pop('total_entries')
        selected_entry = contrib_list_kwargs.pop('selected_entry')
        tpl_contrib = get_template_module('events/papers/_paper_list.html')
        tpl_lists = get_template_module('events/management/_lists.html')
        contribs = contrib_list_kwargs['contribs']
        filter_statistics = tpl_lists.render_displayed_entries_fragment(len(contribs), total_entries)
        return {'html': tpl_contrib.render_paper_assignment_list(self.event, total_entries, **contrib_list_kwargs),
                'filter_statistics': filter_statistics,
                'selected_entry': selected_entry}


class PaperAssignmentListGenerator(PaperListGeneratorBase):
    """Listing and filtering actions in a paper assignment list."""

    endpoint = '.papers_list'
    list_link_type = 'paper_asssignment_management'

    def __init__(self, event):
        super(PaperAssignmentListGenerator, self).__init__(event)
        self.default_list_config = {
            'items': ('state',),
            'filters': {'items': {}}
        }

    def get_list_kwargs(self):
        kwargs = super(PaperAssignmentListGenerator, self).get_list_kwargs()
        kwargs['management'] = True
        return kwargs


class PaperJudgingAreaListGeneratorDisplay(PaperListGeneratorBase):
    """Listing and filtering actions in paper judging area list in the display view"""

    endpoint = '.papers_list'
    list_link_type = 'paper_judging_display'

    def __init__(self, event, user):
        super(PaperJudgingAreaListGeneratorDisplay, self).__init__(event)
        self.user = user
        self.default_list_config = {
            'items': ('state',),
            'filters': {'items': {}}
        }
        judging_unassigned_choices = {role.value: role.title for role in PaperReviewingRole
                                      if role is not PaperReviewingRole.judge}
        self.static_items['unassigned']['filter_choices'] = OrderedDict(sorted(judging_unassigned_choices.items()))

    def _build_query(self):
        query = super(PaperJudgingAreaListGeneratorDisplay, self)._build_query()
        return query.filter(Contribution.paper_judges.any(User.id == self.user.id))

    def get_list_kwargs(self):
        kwargs = super(PaperJudgingAreaListGeneratorDisplay, self).get_list_kwargs()
        kwargs['management'] = False
        return kwargs
