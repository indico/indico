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

from flask import request, flash, redirect, jsonify
from sqlalchemy.orm import joinedload, defaultload

from indico.modules.events.logs import EventLogRealm, EventLogKind
from indico.modules.events.surveys import logger
from indico.modules.events.surveys.controllers.management import RHManageSurveyBase, RHManageSurveysBase
from indico.modules.events.surveys.models.items import SurveySection
from indico.modules.events.surveys.models.submissions import SurveySubmission
from indico.modules.events.surveys.models.surveys import Survey
from indico.modules.events.surveys.util import generate_spreadsheet_from_survey
from indico.modules.events.surveys.views import WPSurveyResults, WPManageSurvey
from indico.util.i18n import _
from indico.util.spreadsheets import send_csv, send_xlsx
from indico.web.flask.util import url_for


class RHSurveyResults(RHManageSurveyBase):
    """Displays summarized results of the survey"""

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        # include all the sections and children to avoid querying them in a loop
        self.survey = (Survey.query
                       .filter_by(id=request.view_args['survey_id'], is_deleted=False)
                       .options(joinedload(Survey.sections).joinedload(SurveySection.children))
                       .one())

    def _process(self):
        return WPSurveyResults.render_template('management/survey_results.html', self._conf, survey=self.survey)


class RHExportSubmissionsBase(RHManageSurveyBase):
    """Export submissions from the survey"""

    CSRF_ENABLED = False
    ALLOW_LOCKED = True

    def _process(self):
        if not self.survey.submissions:
            flash(_('There are no submissions in this survey'))
            return redirect(url_for('.manage_survey', self.survey))

        submission_ids = set(map(int, request.form.getlist('submission_ids')))
        headers, rows = generate_spreadsheet_from_survey(self.survey, submission_ids)
        filename = 'submissions-{}'.format(self.survey.id)
        return self._export(filename, headers, rows)

    def _export(self, filename, headers, rows):
        raise NotImplementedError


class RHExportSubmissionsCSV(RHExportSubmissionsBase):
    """Export submissions as CSV"""

    def _export(self, filename, headers, rows):
        return send_csv(filename + '.csv', headers, rows)


class RHExportSubmissionsExcel(RHExportSubmissionsBase):
    """Export submissions as XLSX"""

    def _export(self, filename, headers, rows):
        return send_xlsx(filename + '.xlsx', headers, rows, tz=self.event_new.tzinfo)


class RHSurveySubmissionBase(RHManageSurveysBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.submission
        }
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        survey_strategy = joinedload('survey')
        answers_strategy = defaultload('answers').joinedload('question')
        sections_strategy = joinedload('survey').defaultload('sections').joinedload('children')
        self.submission = (SurveySubmission
                           .find(id=request.view_args['submission_id'])
                           .options(answers_strategy, survey_strategy, sections_strategy)
                           .one())


class RHDeleteSubmissions(RHManageSurveyBase):
    """Remove submissions from the survey"""

    def _process(self):
        submission_ids = set(map(int, request.form.getlist('submission_ids')))
        for submission in self.survey.submissions[:]:
            if submission.id in submission_ids:
                self.survey.submissions.remove(submission)
                logger.info('Submission %s deleted from survey %s', submission, self.survey)
                self.event_new.log(EventLogRealm.management, EventLogKind.negative, 'Surveys',
                                   'Submission removed from survey "{}"'.format(self.survey.title),
                                   data={'Submitter': submission.user.full_name
                                         if not submission.is_anonymous else 'Anonymous'})
        return jsonify(success=True)


class RHDisplaySubmission(RHSurveySubmissionBase):
    """Display a single submission-page"""

    def _process(self):
        answers = {answer.question_id: answer for answer in self.submission.answers}
        return WPManageSurvey.render_template('management/survey_submission.html', self._conf,
                                              survey=self.submission.survey, submission=self.submission,
                                              answers=answers)
