# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import csv
import re
from io import BytesIO

from flask import session

from indico.modules.events.surveys.models.submissions import SurveySubmission
from indico.util.caching import memoize_request
from indico.util.date_time import format_datetime
from indico.web.forms.base import IndicoForm


def make_survey_form(questions):
    """Creates a WTForm from survey questions.

    Each question will use a field named ``question_ID``.

    :param questions: An iterable containing `SurveyQuestion`
                      objects.  The questions are expected to be
                      sorted according to their `position` attribute.
    :return: An `IndicoForm` subclass.
    """
    form_class = type(b'SurveyForm', (IndicoForm,), {})
    sections = [{'title': None, 'description': None, 'fields': []}]

    for question in questions:
        field_impl = question.field
        if field_impl is None:
            # field definition is not available anymore
            continue
        if field_impl.is_section:
            sections.append({'title': question.title, 'description': question.field_data['text'], 'fields': []})
            continue
        name = 'question_{}'.format(question.id)
        setattr(form_class, name, field_impl.create_wtf_field())
        sections[-1]['fields'].append(name)
    form_class._sections = sections
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


def generate_csv_from_survey(survey, submission_ids):
    """Generates a CSV file from a given survey.

    :param survey: `Survey` for which the user wants to export submissions
    :param submission_ids: The list of submissions to include in the file
    """
    field_names = {'submitter', 'submission_date'}
    field_names |= {'{}_{}'.format(question.title, question.id) for question in survey.questions
                    if not question.field.is_section}

    buf = BytesIO()
    submissions = _filter_submissions(survey, submission_ids)
    writer = csv.DictWriter(buf, fieldnames=field_names)
    writer.writeheader()
    for submission in submissions:
        submission_dict = {
            'submitter': submission.user.full_name.encode('utf-8') if submission.user else None,
            'submission_date': format_datetime(submission.submitted_dt),
        }

        for answer in submission.answers:
            key = '{}_{}'.format(answer.question.title, answer.question.id)
            submission_dict[key] = _prepare_data(answer.answer_data)
        writer.writerow(submission_dict)
    buf.seek(0)
    return buf


def _filter_submissions(survey, submission_ids):
    if submission_ids:
        return SurveySubmission.find_all(SurveySubmission.id.in_(submission_ids), survey=survey)
    return survey.submissions


def _prepare_data(data):
    if isinstance(data, list):
        data = ','.join(data)
    elif data is None:
        data = ''
    return re.sub(r'(\r?\n)+', '    ', unicode(data)).encode('utf-8')
