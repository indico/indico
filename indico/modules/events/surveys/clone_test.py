# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.events.surveys.clone import EventSurveyCloner
from indico.modules.events.surveys.models.items import SurveyItem, SurveyQuestion, SurveySection, SurveyText
from indico.modules.events.surveys.models.surveys import Survey


def test_survey_clone(db, create_event, dummy_event):
    survey = Survey(event=dummy_event, title='test')

    first_section = SurveySection(title='section 1', display_as_section=True, position=2)
    survey.items.append(first_section)
    first_section.children.append(SurveyQuestion(title='question in s1', field_type='text', is_required=True))

    second_section = SurveySection(title='section 2', display_as_section=True, position=1)
    survey.items.append(second_section)
    second_section.children.append(SurveyText(description='My text'))
    second_section.children.append(SurveyQuestion(title='What is your name?', field_type='text', is_required=False))

    db.session.flush()

    new_event = create_event()
    cloner = EventSurveyCloner(dummy_event)
    cloner.run(new_event, {}, {}, False)

    assert len(new_event.surveys) == 1
    assert len(new_event.surveys[0].items) == len(survey.items)
    for i, item in enumerate(new_event.surveys[0].items):
        for attr in get_simple_column_attrs(SurveyItem):
            assert getattr(item, attr) == getattr(survey.items[i], attr)
