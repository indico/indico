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

from flask import request

from indico.core.db import db
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.contributions.models.fields import ContributionField
from indico.modules.events.util import ListGeneratorBase, serialize_person_link
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
            'items': ('submitted_type', 'accepted_type', 'submitted_for_tracks', 'accepted_track', 'state'),
            'filters': {'fields': {}, 'items': {}}
        }
        track_empty = {None: 'No track'}
        type_empty = {None: 'No type'}
        track_choices = {unicode(t.id): to_unicode(t.getTitle()) for t in self.list_event.as_legacy.getTrackList()}
        type_choices = {unicode(t.id): t.name for t in self.list_event.contribution_types}
        self.static_items = OrderedDict([
            ('state', {'title': _('State'), 'filter_choices': {state.name: state.title for state in AbstractState}}),
            ('accepted_track', {'title': _('Final track'),
                                'filter_choices': OrderedDict(track_empty.items() + track_choices.items())}),
            ('submitted_for_tracks', {'title': _('Submitted for tracks'),
                                      'filter_choices': OrderedDict(track_empty.items() + track_choices.items())}),
            ('accepted_type', {'title': _('Accepted type'),
                               'filter_choices': OrderedDict(type_empty.items() + type_choices.items())}),
            ('submitted_type', {'title': _('Submitted type'),
                                'filter_choices': OrderedDict(type_empty.items() + type_choices.items())}),
            ('submitted_dt', {'title': 'Submission date'}),
            ('modified_dt', {'title': 'Modification date'})
        ])
        self.list_config = self._get_config()

    def _get_static_columns(self, ids):
        """
        Retrieve information needed for the header of the static columns.

        :return: a list of {'id': ..., 'caption': ...} dicts
        """
        return [{'id': id_, 'caption': self.static_items[id_]['title']} for id_ in ids if id_ in self.static_items]

    def _get_sorted_contribution_fields(self, item_ids):
        """Return the contribution fields ordered by their position in the abstract form."""

        return (ContributionField
                .find(ContributionField.id.in_(item_ids))
                .with_parent(self.list_event)
                .order_by(ContributionField.position)
                .all())

    def _get_filters_from_request(self):
        filters = super(AbstractListGenerator, self)._get_filters_from_request()
        for field in self.list_event.contribution_fields:
            if field.field_type == 'single_choice':
                options = request.form.getlist('field_{}'.format(field.id))
                if options:
                    filters['fields'][str(field.id)] = options
        return filters

    def _build_query(self):
        return (Abstract.query
                .with_parent(self.list_event)
                .filter(~Abstract.is_deleted)
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
            'accepted_track': Abstract.accepted_track_id,
            'submitted_for_tracks': Abstract.submitted_for_tracks,
            'accepted_type': Abstract.accepted_type_id,
            'submitted_type': Abstract.submitted_type,
            'state': Abstract.state
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
        dynamic_columns = self._get_sorted_contribution_fields(dynamic_item_ids)
        return {
            'abstracts': abstracts,
            'total_abstracts': total_entries,
            'static_columns': static_columns,
            'dynamic_columns': dynamic_columns,
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


def serialize_abstract_person_link(person_link):
    """Serialize AbstractPersonLink to JSON-like object"""
    data = serialize_person_link(person_link)
    data['isSpeaker'] = person_link.is_speaker
    data['authorType'] = person_link.author_type.value
    return data


def make_abstract_form(event):
    """Extends the abstract WTForm to add the extra fields.

    Each extra field will use a field named ``custom_ID``.

    :param event: The `Event` for which to create the abstract form.
    :return: A `AbstractForm` subclass.
    """
    from indico.modules.events.abstracts.forms import AbstractForm

    form_class = type(b'_AbstractForm', (AbstractForm,), {})
    for custom_field in event.contribution_fields:
        field_impl = custom_field.mgmt_field
        if field_impl is None:
            # field definition is not available anymore
            continue
        name = 'custom_{}'.format(custom_field.id)
        setattr(form_class, name, field_impl.create_wtf_field())
    return form_class
