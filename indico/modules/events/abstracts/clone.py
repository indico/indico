# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.abstracts.models.email_templates import AbstractEmailTemplate
from indico.modules.events.abstracts.models.review_questions import AbstractReviewQuestion
from indico.modules.events.abstracts.settings import abstracts_reviewing_settings, abstracts_settings, boa_settings
from indico.modules.events.cloning import EventCloner
from indico.modules.events.models.events import EventType
from indico.util.i18n import _


class AbstractSettingsCloner(EventCloner):
    name = 'abstracts_settings'
    friendly_name = _('Call for Abstracts (settings, email templates, review questions)')
    requires = {'contribution_fields', 'contribution_types', 'tracks'}

    @property
    def is_visible(self):
        return self.old_event.type_ == EventType.conference

    def has_conflicts(self, target_event):
        return bool(target_event.abstract_review_questions) or bool(target_event.abstract_email_templates)

    @no_autoflush
    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._contrib_type_id_map = {old.id: new.id
                                     for old, new in shared_data['contribution_types']['contrib_type_map'].iteritems()}
        self._track_id_map = {old.id: new.id for old, new in shared_data['tracks']['track_map'].iteritems()}
        self._clone_settings(new_event)
        self._clone_email_templates(new_event)
        self._clone_review_questions(new_event)
        db.session.flush()

    def _clone_settings(self, new_event):
        old_settings = abstracts_settings.get_all(self.old_event, no_defaults=True)
        offset = new_event.start_dt - self.old_event.start_dt
        for key in ('start_dt', 'end_dt', 'modification_end_dt'):
            if not old_settings.get(key):
                continue
            old_settings[key] += offset
        abstracts_settings.set_multi(new_event, old_settings)
        abstracts_reviewing_settings.set_multi(new_event, abstracts_reviewing_settings.get_all(self.old_event,
                                                                                               no_defaults=True))
        boa_settings.set_multi(new_event, boa_settings.get_all(self.old_event, no_defaults=True))

    def _clone_email_templates(self, new_event):
        attrs = get_simple_column_attrs(AbstractEmailTemplate) - {'rules'}
        for old_tpl in self.old_event.abstract_email_templates:
            tpl = AbstractEmailTemplate()
            tpl.populate_from_attrs(old_tpl, attrs)
            tpl.rules = filter(None, map(self._clone_email_template_rule, old_tpl.rules))
            new_event.abstract_email_templates.append(tpl)

    def _clone_email_template_rule(self, old_rule):
        rule = {'state': old_rule['state']}
        if 'track' in old_rule:
            try:
                rule['track'] = [self._track_id_map[t] for t in old_rule['track']]
            except KeyError:
                return None
        if 'contribution_type' in old_rule:
            try:
                rule['contribution_type'] = [self._contrib_type_id_map[ct] for ct in old_rule['contribution_type']]
            except KeyError:
                return None
        return rule

    def _clone_review_questions(self, new_event):
        attrs = get_simple_column_attrs(AbstractReviewQuestion)
        for old_question in self.old_event.abstract_review_questions:
            question = AbstractReviewQuestion()
            question.populate_from_attrs(old_question, attrs)
            new_event.abstract_review_questions.append(question)
