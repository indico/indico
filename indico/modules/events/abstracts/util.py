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

from collections import OrderedDict

from indico.core.db import db
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.email_templates import AbstractEmailTemplate
from indico.modules.events.util import ListGeneratorBase
from indico.util.i18n import _
from indico.util.string import to_unicode
from indico.web.flask.templating import get_template_module


class AbstractListGenerator(ListGeneratorBase):
    """Listing and filtering actions in the abstract list."""

    endpoint = '.manage_abstract_list'
    list_link_type = 'abstract'

    def __init__(self, event):
        super(AbstractListGenerator, self).__init__(event)
        self.default_list_config = {
            'items': ('proposed_type', 'final_type', 'proposed_track', 'final_track'),
            'filters': {'fields': {}, 'items': {}}
        }
        # TODO: session_empty = {None: 'No session'}
        track_empty = {None: 'No track'}
        type_empty = {None: 'No type'}
        track_choices = {unicode(t.id): to_unicode(t.getTitle()) for t in self.list_event.as_legacy.getTrackList()}
        type_choices = {unicode(t.id): t.name for t in self.list_event.contribution_types}
        self.static_items = OrderedDict([
            # TODO: ('session', {'title': _('Session'),
            #                    'filter_choices': OrderedDict(session_empty.items() + session_choices.items())}),
            ('final_track', {'title': _('Final track'),
                             'filter_choices': OrderedDict(track_empty.items() + track_choices.items())}),
            ('proposed_track', {'title': _('Proposed track'),
                                'filter_choices': OrderedDict(track_empty.items() + track_choices.items())}),
            ('final_type', {'title': _('Final type'),
                            'filter_choices': OrderedDict(type_empty.items() + type_choices.items())}),
            ('proposed_type', {'title': _('Proposed type'),
                               'filter_choices': OrderedDict(type_empty.items() + type_choices.items())})
        ])
        self.list_config = self._get_config()

    def _get_static_columns(self, ids):
        """
        Retrieve information needed for the header of the static columns.

        :return: a list of {'id': ..., 'caption': ...} dicts
        """
        return [{'id': id_, 'caption': self.static_items[id_]['title']} for id_ in ids if id_ in self.static_items]

    def _build_query(self):
        return (Abstract.query
                .with_parent(self.list_event)
                # TODO: .filter(~Abstract.is_deleted)
                # TODO: add options to `joinedload` fields (once implemented)
                .order_by(Abstract.id))

    def _filter_list_entries(self, query, filters):
        if not (filters.get('fields') or filters.get('items')):
            return query
        # TODO: Get field filters
        field_filters = {}
        if not field_filters and not filters['items']:
            return query
        # TODO: Construct field items criteria
        # items_criteria = []
        criteria = []
        static_filters = {
            # TODO: 'session': Contribution.session_id,
            'final_track': Abstract.final_track_id,
            # TODO: 'proposed_track': Abstract.track_id,
            'final_type': Abstract.final_type_id,
            'proposed_type': Abstract.type_id
        }
        for key, column in static_filters.iteritems():
            ids = set(filters['items'].get(key, ()))
            if not ids:
                continue
            column_criteria = []
            if None in ids:
                column_criteria.append(column.is_(None))
            if ids - {None}:
                column_criteria.append(column.in_(ids - {None}))
            criteria.append(db.or_(*column_criteria))
        return query.filter(db.and_(*criteria))

    def get_list_kwargs(self):
        list_config = self._get_config()
        abstracts_query = self._build_query()
        total_entries = abstracts_query.count()
        abstracts = self._filter_list_entries(abstracts_query, list_config['filters']).all()
        dynamic_item_ids, static_item_ids = self._split_item_ids(list_config['items'], 'dynamic')
        static_columns = self._get_static_columns(static_item_ids)
        return {
            'abstracts': abstracts,
            'total_abstracts': total_entries,
            'static_columns': static_columns,
            # TODO: 'dynamic_columns'
            'filtering_enabled': total_entries != len(abstracts)
        }

    def get_list_export_config(self):
        list_config = self._get_config()
        static_item_ids, dynamic_item_ids = self._split_item_ids(list_config['items'], 'static')
        return {
            'static_item_ids': static_item_ids,
            # TODO: 'dynamic_item_ids'
        }

    def render_list(self):
        list_kwargs = self.get_list_kwargs()
        tpl = get_template_module('events/abstracts/management/_abstract_list.html')
        filtering_enabled = list_kwargs.pop('filtering_enabled')
        tpl_lists = get_template_module('events/management/_lists.html')
        filter_statistics = tpl_lists.render_displayed_entries_fragment(len(list_kwargs['abstracts']),
                                                                        list_kwargs['total_abstracts'])
        return {
            'html': tpl.render_abstract_list(**list_kwargs),
            'filtering_enabled': filtering_enabled,
            'filter_statistics': filter_statistics
        }


def build_default_email_template(event, tpl_type):
    """Build a default e-mail template based on a notification type provided by the user."""
    email = get_template_module('events/abstracts/emails/abstract_{}_notification.txt'.format(tpl_type))
    tpl = AbstractEmailTemplate(body=email.get_body(),
                                extra_cc_emails=[],
                                reply_to_address=to_unicode(event.as_legacy.getSupportInfo().getEmail()) or '',
                                subject=email.get_subject(),
                                include_authors=True,
                                include_submitter=True,
                                include_coauthors=True)
    return tpl
