# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import OrderedDict
from operator import attrgetter

from flask import flash, request, session
from sqlalchemy.orm import joinedload, subqueryload

from indico.core.db import db
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.fields import AbstractFieldValue
from indico.modules.events.abstracts.models.reviews import AbstractReview
from indico.modules.events.contributions.models.fields import ContributionField
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.util import ListGeneratorBase
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module


class AbstractListGeneratorBase(ListGeneratorBase):
    """Listing and filtering actions in an abstract list."""

    show_contribution_fields = True

    def __init__(self, event):
        super(AbstractListGeneratorBase, self).__init__(event)

        self.default_list_config = {
            'items': (),
            'filters': {'fields': {}, 'items': {}, 'extra': {}}
        }
        track_empty = {None: _('No track')}
        type_empty = {None: _('No type')}
        track_choices = OrderedDict((unicode(t.id), t.title) for t in sorted(self.event.tracks,
                                                                             key=attrgetter('title')))
        type_choices = OrderedDict((unicode(t.id), t.name) for t in sorted(self.event.contribution_types,
                                                                           key=attrgetter('name')))
        self.static_items = OrderedDict([
            ('state', {'title': _('State'), 'filter_choices': {state.value: state.title for state in AbstractState}}),
            ('submitter', {'title': _('Submitter')}),
            ('authors', {'title': _('Primary authors')}),
            ('accepted_track', {'title': _('Accepted track'),
                                'filter_choices': OrderedDict(track_empty.items() + track_choices.items())}),
            ('submitted_for_tracks', {'title': _('Submitted for tracks'),
                                      'filter_choices': OrderedDict(track_empty.items() + track_choices.items())}),
            ('reviewed_for_tracks', {'title': _('Reviewed for tracks'),
                                     'filter_choices': OrderedDict(track_empty.items() + track_choices.items())}),
            ('accepted_contrib_type', {'title': _('Accepted type'),
                                       'filter_choices': OrderedDict(type_empty.items() + type_choices.items())}),
            ('submitted_contrib_type', {'title': _('Submitted type'),
                                        'filter_choices': OrderedDict(type_empty.items() + type_choices.items())}),
            ('score', {'title': _('Score')}),
            ('submitted_dt', {'title': _('Submission date')}),
            ('modified_dt', {'title': _('Modification date')})
        ])
        self.extra_filters = {}
        self.list_config = self._get_config()

    def _get_static_columns(self, ids):
        """
        Retrieve information needed for the header of the static columns.

        :return: a list of {'id': ..., 'caption': ...} dicts
        """
        return [{'id': id_, 'caption': self.static_items[id_]['title']} for id_ in self.static_items if id_ in ids]

    def get_all_contribution_fields(self):
        """Return the list of contribution fields for the event."""
        return self.event.contribution_fields if self.show_contribution_fields else []

    def _get_sorted_contribution_fields(self, item_ids):
        """
        Return the contribution fields ordered by their position in
        the abstract form.
        """

        if not item_ids or not self.show_contribution_fields:
            return []
        return (ContributionField.query
                .with_parent(self.event)
                .filter(ContributionField.id.in_(item_ids))
                .order_by(ContributionField.position)
                .all())

    def _get_filters_from_request(self):
        filters = super(AbstractListGeneratorBase, self)._get_filters_from_request()
        for field in self.event.contribution_fields:
            if field.field_type == 'single_choice':
                options = request.form.getlist('field_{}'.format(field.id))
                if options:
                    filters['fields'][unicode(field.id)] = options
        return filters

    def _build_query(self):
        return (Abstract.query
                .with_parent(self.event)
                .options(joinedload('submitter'),
                         joinedload('accepted_track'),
                         joinedload('accepted_contrib_type'),
                         joinedload('submitted_contrib_type'),
                         joinedload('contribution').load_only('id', 'event_id'),
                         subqueryload('field_values'),
                         subqueryload('submitted_for_tracks'),
                         subqueryload('reviewed_for_tracks'),
                         subqueryload('person_links'),
                         subqueryload('reviews').joinedload('ratings'))
                .order_by(Abstract.friendly_id))

    def _filter_list_entries(self, query, filters):
        criteria = []
        field_filters = filters.get('fields')
        item_filters = filters.get('items')
        extra_filters = filters.get('extra')

        if not (field_filters or item_filters or extra_filters):
            return query

        if field_filters:
            for contribution_type_id, field_values in field_filters.iteritems():
                criteria.append(Abstract.field_values.any(db.and_(
                    AbstractFieldValue.contribution_field_id == contribution_type_id,
                    AbstractFieldValue.data.op('#>>')('{}').in_(field_values)
                )))

        if item_filters:
            static_filters = {
                'accepted_track': Abstract.accepted_track_id,
                'accepted_contrib_type': Abstract.accepted_contrib_type_id,
                'submitted_contrib_type': Abstract.submitted_contrib_type_id,
                'submitted_for_tracks': Abstract.submitted_for_tracks,
                'reviewed_for_tracks': Abstract.reviewed_for_tracks
            }
            for key, column in static_filters.iteritems():
                ids = set(item_filters.get(key, ()))
                if not ids:
                    continue
                column_criteria = []
                if '_for_tracks' in key:
                    if None in ids:
                        column_criteria.append(~column.any())
                        ids.discard(None)
                    if ids:
                        column_criteria.append(column.any(Track.id.in_(ids)))
                else:
                    if None in ids:
                        column_criteria.append(column.is_(None))
                        ids.discard(None)
                    if ids:
                        column_criteria.append(column.in_(ids))
                criteria.append(db.or_(*column_criteria))
            if 'state' in item_filters:
                states = [AbstractState(int(state)) for state in item_filters['state']]
                criteria.append(Abstract.state.in_(states))
        if extra_filters:
            if extra_filters.get('multiple_tracks'):
                submitted_for_count = (db.select([db.func.count()])
                                       .as_scalar()
                                       .where(Abstract.submitted_for_tracks.prop.primaryjoin))
                criteria.append(submitted_for_count > 1)
            if extra_filters.get('comments'):
                criteria.append(Abstract.submission_comment != '')
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
            'dynamic_items': self._get_sorted_contribution_fields(dynamic_item_ids)
        }

    def render_list(self, abstract=None):
        list_kwargs = self.get_list_kwargs()
        tpl = get_template_module('events/abstracts/management/_abstract_list.html')
        filtering_enabled = list_kwargs.pop('filtering_enabled')
        tpl_lists = get_template_module('events/management/_lists.html')
        filter_statistics = tpl_lists.render_displayed_entries_fragment(len(list_kwargs['abstracts']),
                                                                        list_kwargs['total_abstracts'])
        return {
            'html': tpl.render_abstract_list(**list_kwargs),
            'filtering_enabled': filtering_enabled,
            'filter_statistics': filter_statistics,
            'hide_abstract': abstract not in list_kwargs['abstracts'] if abstract else None
        }

    def flash_info_message(self, abstract):
        flash(_("The abstract '{}' is not displayed in the list due to the enabled filters")
              .format(abstract.title), 'info')


class AbstractListGeneratorManagement(AbstractListGeneratorBase):
    """
    Listing and filtering actions in the abstract list in the
    management view.
    """

    list_link_type = 'abstract_management'
    endpoint = '.manage_abstract_list'

    def __init__(self, event):
        super(AbstractListGeneratorManagement, self).__init__(event)
        self.default_list_config['items'] = ('submitted_contrib_type', 'accepted_contrib_type', 'state')
        if event.tracks:
            self.default_list_config['items'] += ('submitted_for_tracks', 'reviewed_for_tracks', 'accepted_track')
        self.extra_filters = OrderedDict([
            ('multiple_tracks', {'title': _('Proposed for multiple tracks'), 'type': 'bool'}),
            ('comments', {'title': _('Must have comments'), 'type': 'bool'})
        ])


class AbstractListGeneratorDisplay(AbstractListGeneratorBase):
    """
    Listing and filtering actions in the abstract list in the display view.
    """

    list_link_type = 'abstract_display'
    endpoint = '.display_reviewable_track_abstracts'
    show_contribution_fields = False

    def __init__(self, event, track):
        super(AbstractListGeneratorDisplay, self).__init__(event)
        self.track = track
        self.default_list_config['items'] = ('accepted_contrib_type', 'state')
        items = {'submitted_contrib_type', 'submitter', 'accepted_contrib_type', 'state'}
        if self.track.can_convene(session.user):
            items.add('score')
        self.static_items = OrderedDict((key, value)
                                        for key, value in self.static_items.iteritems()
                                        if key in items)

    def _build_query(self):
        return (super(AbstractListGeneratorDisplay, self)._build_query()
                .filter(Abstract.state != AbstractState.invited,
                        Abstract.reviewed_for_tracks.contains(self.track)))

    def get_user_reviewed_abstracts_for_track(self, user, track):
        return (Abstract.query
                .join(Abstract.reviews)
                .filter(AbstractReview.user == user,
                        Abstract.state != AbstractState.invited,
                        Abstract.reviewed_for_tracks.contains(track),
                        ~Abstract.is_deleted)
                .all())

    def get_list_kwargs(self):
        kwargs = super(AbstractListGeneratorDisplay, self).get_list_kwargs()
        kwargs['reviewed_abstracts'] = self.get_user_reviewed_abstracts_for_track(session.user, self.track)
        return kwargs
