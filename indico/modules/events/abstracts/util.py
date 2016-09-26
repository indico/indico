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

from collections import OrderedDict, namedtuple

from flask import request

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.email_templates import AbstractEmailTemplate
from indico.modules.events.abstracts.models.fields import AbstractFieldValue
from indico.modules.events.abstracts.settings import abstracts_settings
from indico.modules.events.contributions.models.fields import ContributionField
from indico.modules.events.tracks.models.tracks import Track
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
            'items': ('submitted_contrib_type', 'accepted_contrib_type', 'submitted_for_tracks', 'reviewed_for_tracks',
                      'accepted_track', 'state'),
            'filters': {'fields': {}, 'items': {}, 'extra': {}}
        }
        track_empty = {None: 'No track'}
        type_empty = {None: 'No type'}
        track_choices = {unicode(track.id): track.title for track in event.tracks}
        type_choices = {unicode(t.id): t.name for t in self.list_event.contribution_types}
        self.static_items = OrderedDict([
            ('state', {'title': _('State'), 'filter_choices': {state.name: state.title for state in AbstractState}}),
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
            # TODO: Rating
            ('submitted_dt', {'title': _('Submission date')}),
            ('modified_dt', {'title': _('Modification date')})
        ])
        self.extra_filters = OrderedDict([
            ('multiple_tracks', {'title': _('Proposed for multiple tracks'), 'type': 'bool'}),
            ('comments', {'title': _('Must have comments'), 'type': 'bool'})
        ])
        self.list_config = self._get_config()

    def _get_static_columns(self, ids):
        """
        Retrieve information needed for the header of the static columns.

        :return: a list of {'id': ..., 'caption': ...} dicts
        """
        return [{'id': id_, 'caption': self.static_items[id_]['title']} for id_ in self.static_items if id_ in ids]

    def _get_sorted_contribution_fields(self, item_ids):
        """Return the contribution fields ordered by their position in the abstract form."""

        return (ContributionField.query
                .with_parent(self.list_event)
                .filter(ContributionField.id.in_(item_ids))
                .order_by(ContributionField.position)
                .all())

    def _get_filters_from_request(self):
        filters = super(AbstractListGenerator, self)._get_filters_from_request()
        for field in self.list_event.contribution_fields:
            if field.field_type == 'single_choice':
                options = request.form.getlist('field_{}'.format(field.id))
                if options:
                    filters['fields'][unicode(field.id)] = options
        return filters

    def _build_query(self):
        return (Abstract.query
                .with_parent(self.list_event)
                .order_by(Abstract.id))

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
                'state': Abstract.state,
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
    email = get_template_module('events/abstracts/emails/default_{}_notification.txt'.format(tpl_type))
    tpl = AbstractEmailTemplate(body=email.get_body(),
                                extra_cc_emails=[],
                                reply_to_address=to_unicode(event.as_legacy.getSupportInfo().getEmail()) or '',
                                subject=email.get_subject(),
                                include_authors=True,
                                include_submitter=True,
                                include_coauthors=True)
    return tpl


@no_autoflush
def create_mock_abstract(event):
    """Create a mock abstract that can be used in previews.

    Brace for geek references.
    """
    User = namedtuple('Author', ['first_name', 'last_name', 'title', 'full_name'])
    Track = namedtuple('Track', ['title'])
    Session = namedtuple('Session', ['title'])
    ContributionType = namedtuple('ContributionType', ['name'])
    Contribution = namedtuple('Contribution', ['title', 'track', 'session', 'type', 'locator'])
    Abstract = namedtuple('Abstract', ['friendly_id', 'title', 'event_new', 'submitter', 'contribution',
                                       'primary_authors', 'secondary_authors', 'locator', 'judgment_comment',
                                       'accepted_track', 'accepted_contrib_type', 'state'])

    englert = User(full_name="Fran\xe7ois Englert", first_name="Fran\xe7ois", last_name="Englert", title="Prof.")
    brout = User(full_name="Robert Brout", first_name="Robert", last_name="Brout", title="Prof.")
    guralnik = User(full_name="Gerald Guralnik", first_name="Gerald", last_name="Guralnik", title="Prof.")
    hagen = User(full_name="Carl Hagen", first_name="Carl", last_name="Hagen", title="Prof.")
    kibble = User(full_name="Tom Kibble", first_name="Tom", last_name="Kibble", title="Prof.")
    higgs = User(full_name="Peter Higgs", first_name="Peter", last_name="Higgs", title="Prof.")

    track = Track(title=_("Higgs Fields"))
    session = Session(title=_("Higgs Fields Posters"))
    contribution_type = ContributionType(name=_("Poster"))
    contribution = Contribution(title="Broken Symmetry and the Mass of Gauge Vector Mesons",
                                track=track,
                                session=session,
                                type=contribution_type,
                                locator={'confId': -314, 'contrib_id': 1234})
    abstract = Abstract(friendly_id=314,
                        title="Broken Symmetry and the Mass of Gauge Vector Mesons",
                        accepted_track=track,
                        accepted_contrib_type=contribution_type,
                        event_new=event,
                        submitter=brout,
                        state=AbstractState.accepted,
                        contribution=contribution,
                        primary_authors=[englert, brout],
                        secondary_authors=[guralnik, hagen, kibble, higgs],
                        locator={'confId': -314, 'abstract_id': 1234},
                        judgment_comment='Vague but interesting!')

    return abstract


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
    :return: An `AbstractForm` subclass.
    """
    from indico.modules.events.abstracts.forms import AbstractForm, MultiTrackMixin, SingleTrackMixin

    mixins = []
    if abstracts_settings.get(event, 'allow_multiple_tracks'):
        mixins.append(MultiTrackMixin)
    else:
        mixins.append(SingleTrackMixin)
    form_class = type(b'_AbstractForm', tuple(mixins) + (AbstractForm,), {})
    for custom_field in event.contribution_fields:
        field_impl = custom_field.mgmt_field
        if field_impl is None:
            # field definition is not available anymore
            continue
        name = 'custom_{}'.format(custom_field.id)
        setattr(form_class, name, field_impl.create_wtf_field())
    return form_class
