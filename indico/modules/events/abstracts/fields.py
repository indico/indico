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

from flask import jsonify, request, session
from werkzeug.exceptions import BadRequest
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from indico.core.db.sqlalchemy.util.queries import escape_like
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.models.review_questions import AbstractReviewQuestion
from indico.modules.events.abstracts.notifications import StateCondition, TrackCondition, ContributionTypeCondition
from indico.modules.events.abstracts.util import serialize_abstract_person_link
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.fields import PersonLinkListFieldBase
from indico.util.decorators import classproperty
from indico.util.i18n import _
from indico.web.forms.base import AjaxFieldMixin
from indico.web.forms.fields import MultipleItemsField, JSONField
from indico.web.forms.widgets import JinjaWidget, SelectizeWidget


class EmailRuleListField(JSONField):
    """A field that stores a list of e-mail template rules."""

    CAN_POPULATE = True
    widget = JinjaWidget('events/abstracts/forms/rule_list_widget.html')
    accepted_condition_types = (StateCondition, TrackCondition, ContributionTypeCondition)

    @classproperty
    @classmethod
    def condition_class_map(cls):
        return {r.name: r for r in cls.accepted_condition_types}

    @property
    def condition_choices(self):
        return {
            c.name: {
                'title': c.description,
                'labelText': c.label_text,
                'options': list(c.get_available_values(event=self.event).viewitems()),
                'compatibleWith': c.compatible_with,
                'required': c.required
            } for c in self.accepted_condition_types
        }

    def _convert_condition(self, condition_data):
        condition_type = condition_data.pop('type')
        return self.condition_class_map[condition_type](**condition_data)

    def _convert_condition_list(self, condition_list):
        return map(self._convert_condition, condition_list)

    def _value(self):
        return super(EmailRuleListField, self)._value() if self.data else '[]'


class AbstractReviewQuestionsField(MultipleItemsField):
    def __init__(self, *args, **kwargs):
        self.fields = [{'id': 'text', 'caption': _("Question"), 'type': 'text', 'required': True}]
        super(AbstractReviewQuestionsField, self).__init__(*args, uuid_field='id', uuid_field_opaque=True,
                                                           sortable=True, **kwargs)

    def process_formdata(self, valuelist):
        super(AbstractReviewQuestionsField, self).process_formdata(valuelist)
        if valuelist:
            existing = {x.id: x for x in self.object_data or ()}
            data = []
            for pos, entry in enumerate(self.data, 1):
                question = existing.pop(int(entry['id'])) if entry.get('id') is not None else AbstractReviewQuestion()
                question.text = entry['text']
                question.position = pos
                data.append(question)
            for question in existing.itervalues():
                if question.ratings:
                    # keep it around and soft-delete if it has been used; otherwise we just skip it
                    # which will delete it once it's gone from the relationship (when populating the
                    # Event from the form's data)
                    question.is_deleted = True
                    data.append(question)
            self.data = data

    def _value(self):
        if not self.data:
            return []
        else:
            return [{'id': q.id, 'text': q.text} for q in self.data]


class AbstractPersonLinkListField(PersonLinkListFieldBase):
    """A field to configure a list of abstract persons"""

    person_link_cls = AbstractPersonLink
    linked_object_attr = 'abstract'
    widget = JinjaWidget('events/contributions/forms/contribution_person_link_widget.html', allow_empty_email=True)

    def __init__(self, *args, **kwargs):
        self.author_types = AuthorType.serialize()
        self.allow_authors = True
        self.allow_submitters = False
        self.show_empty_coauthors = kwargs.pop('show_empty_coauthors', True)
        self.default_author_type = kwargs.pop('default_author_type', AuthorType.none)
        self.default_is_submitter = False
        self.default_is_speaker = True
        self.require_primary_author = True
        super(AbstractPersonLinkListField, self).__init__(*args, **kwargs)

    def _convert_data(self, data):
        return list({self._get_person_link(x) for x in data})

    @no_autoflush
    def _get_person_link(self, data):
        extra_data = {'author_type': data.pop('authorType', self.default_author_type),
                      'is_speaker': data.pop('isSpeaker', self.default_is_speaker)}
        return super(AbstractPersonLinkListField, self)._get_person_link(data, extra_data)

    def _serialize_person_link(self, principal, extra_data=None):
        return serialize_abstract_person_link(principal)

    def pre_validate(self, form):
        super(AbstractPersonLinkListField, self).pre_validate(form)
        for person_link in self.data:
            if not self.allow_authors and person_link.author_type != AuthorType.none:
                if not self.object_data or person_link not in self.object_data:
                    person_link.author_type = AuthorType.none
            if person_link.author_type == AuthorType.none and not person_link.is_speaker:
                raise ValueError(_("{} has no role").format(person_link.full_name))


class AbstractField(AjaxFieldMixin, QuerySelectField):
    """A selectize-based field to select an abstract from an event."""

    widget = SelectizeWidget(allow_by_id=True, search_field='title', label_field='full_title')

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('allow_blank', True)
        kwargs.setdefault('render_kw', {}).setdefault('placeholder', _('Enter #id or search string'))
        kwargs['query_factory'] = self._get_query
        kwargs['get_label'] = lambda a: '#{}: {}'.format(a.friendly_id, a.title)
        self.excluded_abstract = None
        super(AbstractField, self).__init__(*args, **kwargs)

    def process_ajax(self):
        query = self._get_query()
        if 'id' in request.args:
            query = query.filter_by(friendly_id=int(request.args['id']))
        else:
            q = request.args.get('q', '').strip()
            if len(q) < 3:
                raise BadRequest('An ID or query (min. 3 chars) must be provided')
            query = query.filter(Abstract.title.ilike('%{}%'.format(escape_like(q))))
        result = [{'id': abstract.id, 'friendly_id': abstract.friendly_id, 'title': abstract.title,
                   'full_title': '#{}: {}'.format(abstract.friendly_id, abstract.title)}
                  for abstract in query
                  if abstract.can_access(session.user)]
        return jsonify(result)

    def _get_query(self):
        query = Abstract.query.with_parent(self.event)
        if self.excluded_abstract is not None:
            query = query.filter(Abstract.id != self.excluded_abstract.id)
        return query.order_by(Abstract.friendly_id)

    def _get_object_list(self):
        return [(key, abstract)
                for key, abstract in super(AbstractField, self)._get_object_list()
                if abstract.can_access(session.user)]

    @property
    def event(self):
        # This cannot be accessed in __init__ since `get_form` is set
        # afterwards (when the field gets bound to its form) so we
        # need to access it through a property instead.
        return self.get_form().event

    @property
    def search_url(self):
        return self.get_ajax_url()
