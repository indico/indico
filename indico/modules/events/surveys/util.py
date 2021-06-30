# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from operator import attrgetter

from flask import session
from sqlalchemy.orm import joinedload, load_only

from indico.core.db import db
from indico.modules.events import Event
from indico.modules.events.surveys.models.submissions import SurveySubmission
from indico.util.caching import memoize_request
from indico.util.spreadsheets import unique_col
from indico.web.forms.base import IndicoForm


def make_survey_form(survey):
    """Create a WTForm from survey questions.

    Each question will use a field named ``question_ID``.

    :param survey: The `Survey` for which to create the form.
    :return: An `IndicoForm` subclass.
    """
    form_class = type('SurveyForm', (IndicoForm,), {})

    for question in survey.questions:
        field_impl = question.field
        if field_impl is None:
            # field definition is not available anymore
            continue
        name = f'question_{question.id}'
        setattr(form_class, name, field_impl.create_wtf_field())
    return form_class


def save_submitted_survey_to_session(submission):
    """Save submission of a survey to session for further checks."""
    session.setdefault('submitted_surveys', {})[submission.survey.id] = submission.id
    session.modified = True


@memoize_request
def was_survey_submitted(survey):
    """Check whether the current user has submitted a survey."""
    from indico.modules.events.surveys.models.surveys import Survey
    query = (Survey.query.with_parent(survey.event)
             .filter(Survey.submissions.any(db.and_(SurveySubmission.is_submitted,
                                                    SurveySubmission.user == session.user))))
    user_submitted_surveys = set(query)
    if session.user and survey in user_submitted_surveys:
        return True

    # anonymous survey: check anonymous submission table
    if survey.anonymous and session.user:
        return session.user.anonymous_survey_submissions.filter_by(survey=survey).has_rows()

    submission_id = session.get('submitted_surveys', {}).get(survey.id)
    if submission_id is None:
        return False
    return SurveySubmission.query.filter_by(id=submission_id, is_submitted=True).has_rows()


def is_submission_in_progress(survey):
    """Check whether the current user has a survey submission in progress."""
    from indico.modules.events.surveys.models.surveys import Survey
    if session.user:
        query = (Survey.query.with_parent(survey.event)
                 .filter(Survey.submissions.any(db.and_(~SurveySubmission.is_submitted,
                                                        SurveySubmission.user == session.user))))
        user_incomplete_surveys = set(query)
        return survey in user_incomplete_surveys
    else:
        return False


def generate_spreadsheet_from_survey(survey, submission_ids):
    """Generate spreadsheet data from a given survey.

    :param survey: `Survey` for which the user wants to export submissions
    :param submission_ids: The list of submissions to include in the file
    """
    field_names = ['Submitter', 'Submitter Email', 'Submission Date']
    sorted_questions = sorted(survey.questions, key=attrgetter('parent.position', 'position'))
    field_names += [unique_col(_format_title(question), question.id) for question in sorted_questions]

    submissions = _filter_submissions(survey, submission_ids)
    rows = []
    for submission in submissions:
        submission_dict = {
            'Submitter': submission.user.full_name if not submission.is_anonymous else None,
            'Submitter Email': submission.user.email if not submission.is_anonymous else None,
            'Submission Date': submission.submitted_dt,
        }
        for key in field_names:
            submission_dict.setdefault(key, '')
        for answer in submission.answers:
            key = unique_col(_format_title(answer.question), answer.question.id)
            submission_dict[key] = answer.answer_data
        rows.append(submission_dict)
    return field_names, rows


def _format_title(question):
    if question.parent.title:
        return f'{question.parent.title}: {question.title}'
    else:
        return question.title


def _filter_submissions(survey, submission_ids):
    if submission_ids:
        return (SurveySubmission.query
                .filter(SurveySubmission.id.in_(submission_ids),
                        SurveySubmission.survey == survey)
                .all())
    return [x for x in survey.submissions if x.is_submitted]


def get_events_with_submitted_surveys(user, dt=None):
    """Get the IDs of events where the user submitted a survey.

    :param user: A `User`
    :param dt: Only include events taking place on/after that date
    :return: A set of event ids
    """
    from indico.modules.events.surveys.models.surveys import Survey

    # Survey submissions are not stored in links anymore, so we need to get them directly
    query = (user.survey_submissions
             .options(load_only('survey_id'))
             .options(joinedload(SurveySubmission.survey).load_only('event_id'))
             .join(Survey)
             .join(Event)
             .filter(~Survey.is_deleted, ~Event.is_deleted, Event.ends_after(dt)))
    return {submission.survey.event_id for submission in query}


def query_active_surveys(event):
    from indico.modules.events.surveys.models.surveys import Survey
    private_criterion = ~Survey.private
    if session.user:
        user_pending_criterion = ~SurveySubmission.is_submitted & (SurveySubmission.user == session.user)
        private_criterion |= Survey.submissions.any(user_pending_criterion)
    return (Survey.query.with_parent(event)
            .filter(Survey.is_active, private_criterion)
            .order_by(db.func.lower(Survey.title)))
