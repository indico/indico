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

from flask import session
from sqlalchemy.orm import load_only, joinedload

from indico.modules.events import Event
from indico.modules.events.surveys.models.surveys import Survey
from indico.modules.events.surveys.models.submissions import SurveySubmission
from indico.util.caching import memoize_request
from indico.util.date_time import format_datetime
from indico.util.spreadsheets import unique_col
from indico.util.string import to_unicode
from indico.web.forms.base import IndicoForm


def make_survey_form(survey):
    """Creates a WTForm from survey questions.

    Each question will use a field named ``question_ID``.

    :param survey: The `Survey` for which to create the form.
    :return: An `IndicoForm` subclass.
    """
    form_class = type(b'SurveyForm', (IndicoForm,), {})

    for question in survey.questions:
        field_impl = question.field
        if field_impl is None:
            # field definition is not available anymore
            continue
        name = 'question_{}'.format(question.id)
        setattr(form_class, name, field_impl.create_wtf_field())
    return form_class


def save_submitted_survey_to_session(submission):
    """Save submission of a survey to session for further checks"""
    session.setdefault('submitted_surveys', {})[submission.survey.id] = submission.id
    session.modified = True


@memoize_request
def was_survey_submitted(survey):
    """Check whether the current user has submitted a survey"""
    if session.user and session.user.survey_submissions.filter_by(survey=survey).count():
        return True
    submission_id = session.get('submitted_surveys', {}).get(survey.id)
    if submission_id is None:
        return False
    return bool(SurveySubmission.find(id=submission_id).count())


def generate_spreadsheet_from_survey(survey, submission_ids):
    """Generates spreadsheet data from a given survey.

    :param survey: `Survey` for which the user wants to export submissions
    :param submission_ids: The list of submissions to include in the file
    """
    field_names = ['Submitter', 'Submission Date']
    field_names += [unique_col(question.title, question.id) for question in survey.questions]

    submissions = _filter_submissions(survey, submission_ids)
    rows = []
    for submission in submissions:
        submission_dict = {
            'Submitter': submission.user.full_name if submission.user else None,
            'Submission Date': to_unicode(format_datetime(submission.submitted_dt)),
        }

        for answer in submission.answers:
            key = unique_col(answer.question.title, answer.question.id)
            submission_dict[key] = answer.answer_data
        rows.append(submission_dict)
    return field_names, rows


def _filter_submissions(survey, submission_ids):
    if submission_ids:
        return SurveySubmission.find_all(SurveySubmission.id.in_(submission_ids), survey=survey)
    return survey.submissions


def get_events_with_submitted_surveys(user, from_dt=None, to_dt=None):
    """Gets the IDs of events where the user submitted a survey.

    :param user: A `User`
    :param from_dt: The earliest event start time to look for
    :param to_dt: The latest event start time to look for
    :return: A set of event ids
    """
    # Survey submissions are not stored in links anymore, so we need to get them directly
    query = (user.survey_submissions
             .options(load_only('survey_id'))
             .options(joinedload(SurveySubmission.survey).load_only('event_id'))
             .join(Survey)
             .join(Event)
             .filter(~Survey.is_deleted, ~Event.is_deleted, Event.starts_between(from_dt, to_dt)))
    return {submission.survey.event_id for submission in query}
