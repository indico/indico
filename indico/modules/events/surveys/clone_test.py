# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.events.surveys.clone import EventSurveyCloner
from indico.modules.events.surveys.models.items import SurveyItem, SurveyQuestion, SurveySection
from indico.modules.events.surveys.models.surveys import Survey


def test_survey_clone(db, create_event, dummy_event):
    survey = Survey(title='test')
    section = SurveySection(title='test', display_as_section=True)
    survey.items.append(section)
    SurveyQuestion(title='question', field_type='text', is_required=True, parent=section)
    dummy_event.surveys.append(survey)
    db.session.flush()

    new_event = create_event()
    cloner = EventSurveyCloner(dummy_event)
    cloner.run(new_event, {}, {}, False)

    assert len(new_event.surveys) == 1
    assert len(new_event.surveys[0].items) == len(survey.items)
    for i, item in enumerate(new_event.surveys[0].items):
        for attr in get_simple_column_attrs(SurveyItem):
            assert getattr(item, attr) == getattr(survey.items[i], attr)
