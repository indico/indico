# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import re
from datetime import date, timedelta
from HTMLParser import HTMLParser
from operator import attrgetter
from uuid import uuid4

from indico.core.db import db
from indico.modules.events.models.settings import EventSetting
from indico.modules.events.surveys.models.surveys import Survey
from indico.modules.events.surveys.models.items import SurveyQuestion, SurveySection
from indico.modules.events.surveys.models.submissions import SurveySubmission, SurveyAnswer
from indico.modules.users import User
from indico.util.console import cformat, verbose_iterator
from indico.util.date_time import localize_as_utc
from indico.util.struct.iterables import committing_iterator
from indico.web.flask.templating import strip_tags
from indico_zodbimport import Importer, convert_to_unicode


WHITESPACE_RE = re.compile(r'\s+')


def _sanitize(title):
    return WHITESPACE_RE.sub(' ', HTMLParser().unescape(strip_tags(convert_to_unicode(title)))).strip()


class SurveyImporter(Importer):
    def has_data(self):
        return Survey.query.has_rows()

    def migrate(self):
        self.migrate_surveys()
        self.update_merged_users(SurveySubmission.user, "survey submissions")

    def migrate_surveys(self):
        self.print_step("Migrating old event evaluations")
        notification_pending = {es.event_id: es.value for es in EventSetting.find_all(module='evaluation',
                                                                                      name='send_notification')}
        for event, evaluation in committing_iterator(self._iter_evaluations(), 10):
            survey = self.migrate_survey(evaluation, event)
            if (survey.notifications_enabled and survey.start_notification_emails and
                    not notification_pending.get(survey.event_id)):
                survey.start_notification_sent = True
            db.session.add(survey)

    def migrate_survey(self, evaluation, event):
        survey = Survey(event_id=int(event.id))
        if evaluation.title and not evaluation.title.startswith('Evaluation for '):
            survey.title = _sanitize(evaluation.title)
        if not survey.title:
            survey.title = "Evaluation"
        survey.introduction = _sanitize(evaluation.announcement)
        if evaluation.contactInfo:
            contact_text = "Contact: ".format(_sanitize(evaluation.contactInfo))
            survey.introduction += "\n\n{}".format(contact_text) if survey.introduction else contact_text
        survey.submission_limit = evaluation.submissionsLimit if evaluation.submissionsLimit else None
        survey.anonymous = evaluation.anonymous
        # Require the user to login if the survey is not anonymous or if logging in was required before
        survey.require_user = not survey.anonymous or evaluation.mandatoryAccount

        if evaluation.startDate.date() == date.min or evaluation.endDate.date() == date.min:
            survey.start_dt = event.endDate
            survey.end_dt = survey.start_dt + timedelta(days=7)
        else:
            survey.start_dt = localize_as_utc(evaluation.startDate, event.tz)
            survey.end_dt = localize_as_utc(evaluation.endDate, event.tz)
        if survey.end_dt < survey.start_dt:
            survey.end_dt = survey.end_dt + timedelta(days=7)

        for kind, notification in evaluation.notifications.iteritems():
            survey.notifications_enabled = True
            recipients = set(notification._toList) | set(notification._ccList)
            if kind == 'evaluationStartNotify':
                survey.start_notification_emails = list(recipients)
            elif kind == 'newSubmissionNotify':
                survey.new_submission_emails = list(recipients)

        self.print_success(cformat('%{cyan}{}%{reset}').format(survey), always=True, event_id=event.id)

        question_map = {}
        section = SurveySection(survey=survey, display_as_section=False)
        for position, old_question in enumerate(evaluation._questions):
            question = self.migrate_question(old_question, position)
            question_map[old_question] = question
            section.children.append(question)

        for old_submission in evaluation._submissions:
            submission = self.migrate_submission(old_submission, question_map, event.tz)
            survey.submissions.append(submission)

        return survey

    def migrate_question(self, old_question, position):
        question = SurveyQuestion()
        question.position = position
        question.title = _sanitize(old_question.questionValue)
        question.description = _sanitize(old_question.description)
        if old_question.help:
            help_text = _sanitize(old_question.help)
            question.description += "\n\nHelp: {}".format(help_text) if question.description else help_text
        question.is_required = old_question.required
        question.field_data = {}
        class_name = old_question.__class__.__name__
        if class_name == 'Textbox':
            question.field_type = 'text'
        elif class_name == 'Textarea':
            question.field_type = 'text'
            question.field_data['multiline'] = True
        elif class_name == 'Password':
            question.field_type = 'text'
        elif class_name in ('Checkbox', 'Radio', 'Select'):
            question.field_data['options'] = []
            question.field_type = 'single_choice' if class_name in ('Radio', 'Select') else 'multiselect'
            if question.field_type == 'single_choice':
                question.field_data['display_type'] = class_name.lower()
            if class_name == 'Radio':
                question.field_data['radio_display_type'] = 'vertical'
            for option in old_question.choiceItems:
                question.field_data['options'].append({'option': option, 'id': unicode(uuid4())})
        self.print_success(" - Question: {}".format(question.title))
        return question

    def migrate_submission(self, old_submission, question_map, timezone):
        submission = SurveySubmission()
        submitted_dt = old_submission.submissionDate
        submission.submitted_dt = submitted_dt if submitted_dt.tzinfo else localize_as_utc(submitted_dt, timezone)
        if not old_submission.anonymous and old_submission._submitter:
            avatar = old_submission._submitter
            with db.session.no_autoflush:
                submission.user = User.get(int(avatar.id))
        self.print_success(" - Submission from user {}".format(submission.user_id or 'anonymous'))
        for old_answer in old_submission._answers:
            question = question_map[old_answer._question]
            answer = self.migrate_answer(old_answer, question)
            submission.answers.append(answer)
            question.answers.append(answer)
        return submission

    def migrate_answer(self, old_answer, question):
        answer = SurveyAnswer()
        if old_answer.__class__.__name__ == 'MultipleChoicesAnswer':
            answer.data = []
            for option in old_answer._selectedChoiceItems:
                answer.data.append(self._get_option_id(question, option))
        elif old_answer._question.__class__.__name__ in ('Radio', 'Select'):
            if old_answer._answerValue:
                answer.data = self._get_option_id(question, old_answer._answerValue)
        else:
            answer.data = _sanitize(old_answer._answerValue)
        self.print_success("   - Answer: {}".format(answer.data))
        return answer

    def _iter_evaluations(self):
        it = self.zodb_root['conferences'].itervalues()
        if self.quiet:
            it = verbose_iterator(it, len(self.zodb_root['conferences']), attrgetter('id'), attrgetter('title'))
        for event in self.flushing_iterator(it):
            for evaluation in getattr(event, '_evaluations', []):
                if evaluation._questions:
                    yield event, evaluation

    def _get_option_id(self, question, option):
        return next((opt['id'] for opt in question.field_data['options'] if opt['option'] == option), None)
