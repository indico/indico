# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from pathlib import Path

from indico.core.db import db
from indico.modules.events.surveys.models.items import SurveyQuestion, SurveySection
from indico.modules.events.surveys.models.submissions import SurveySubmission
from indico.modules.events.surveys.models.surveys import Survey
from indico.web.flask.templating import get_template_module


def test_new_submission_email_plaintext(snapshot, dummy_event, dummy_user):
    survey = Survey(event=dummy_event, title='test')
    first_section = SurveySection(title='section 1', display_as_section=True, position=2)
    survey.items.append(first_section)
    question = SurveyQuestion(title='question in s1', field_type='text', is_required=True)
    first_section.children.append(question)
    submission = SurveySubmission(survey=survey, user=dummy_user)
    db.session.flush()
    template = get_template_module('events/surveys/emails/new_submission_email.txt',
                                   submission=submission)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), 'new_submission_email.txt')


def test_start_notification_email_plaintext(snapshot, dummy_event):
    survey = Survey(event=dummy_event, title='test')
    db.session.flush()
    template = get_template_module('events/surveys/emails/start_notification_email.txt',
                                   survey=survey)
    snapshot.snapshot_dir = Path(__file__).parent / 'templates/emails/tests'
    snapshot.assert_match(template.get_body(), 'start_notification_email.txt')
