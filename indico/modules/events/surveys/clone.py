# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.events.cloning import EventCloner
from indico.modules.events.surveys.models.surveys import Survey
from indico.util.i18n import _


class EventSurveyCloner(EventCloner):
    name = 'event_survey'
    friendly_name = _('Surveys')
    is_default = False

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    def has_conflicts(self, target_event):
        return self._has_content(target_event)

    def run(self, new_event, cloners, shared_data, event_exists=False):
        with db.session.no_autoflush:
            self._clone_surveys(new_event)
        db.session.flush()

    def _has_content(self, event):
        return len([survey for survey in event.surveys if not survey.is_deleted])

    def _clone_surveys(self, new_event):
        survey_attrs = get_simple_column_attrs(Survey) - {'uuid', 'start_dt', 'end_dt', '_last_friendly_submission_id'}
        for old_survey in self.old_event.surveys:
            survey = Survey()
            survey.populate_from_attrs(old_survey, survey_attrs)
            item_map = {}
            for old_item in old_survey.items:
                item = self._clone_item(old_item)
                if old_item.parent:
                    assert old_item.parent != old_item
                    if old_item.parent not in item_map:
                        item_map[old_item.parent] = self._clone_item(old_item.parent)
                    item.parent = item_map[old_item.parent]
                item_map[old_item] = item
            survey.items.extend(item_map.values())
            new_event.surveys.append(survey)

    def _clone_item(self, old_item):
        item_cls = type(old_item)
        item = item_cls()
        item.populate_from_attrs(old_item, get_simple_column_attrs(item_cls))
        return item
