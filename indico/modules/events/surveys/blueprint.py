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

from indico.modules.events.surveys.controllers.management import (RHManageSurveys, RHCreateSurvey, RHManageSurvey,
                                                                  RHDeleteSurvey, RHEditSurvey, RHScheduleSurvey,
                                                                  RHCloseSurvey, RHOpenSurvey,
                                                                  RHManageSurveyQuestionnaire, RHAddSurveyQuestion,
                                                                  RHEditSurveyQuestion, RHDeleteSurveyQuestion,
                                                                  RHSortQuestions, RHSurveyResults, RHExportSubmissions,
                                                                  RHDeleteSubmissions)
from indico.modules.events.surveys.controllers.display import RHSurveyList, RHSubmitSurvey
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('survey', __name__, template_folder='templates', virtual_template_folder='events/surveys',
                      url_prefix='/event/<confId>', event_feature='surveys')

# surveys display
_bp.add_url_rule('/surveys/', 'display_survey_list', RHSurveyList)
_bp.add_url_rule('/surveys/<int:survey_id>', 'display_survey_form', RHSubmitSurvey, methods=('GET', 'POST'))

# surveys management
_bp.add_url_rule('/manage/surveys/', 'management', RHManageSurveys)
_bp.add_url_rule('/manage/surveys/create', 'create', RHCreateSurvey, methods=('GET', 'POST'))

# Single survey management
_bp.add_url_rule('/manage/surveys/<int:survey_id>/', 'manage_survey', RHManageSurvey)
_bp.add_url_rule('/manage/surveys/<int:survey_id>/results', 'survey_results', RHSurveyResults)
_bp.add_url_rule('/manage/surveys/<int:survey_id>/delete', 'delete_survey', RHDeleteSurvey, methods=('POST',))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/edit', 'edit_survey', RHEditSurvey, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/schedule', 'schedule_survey', RHScheduleSurvey,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/open', 'open_survey', RHOpenSurvey, methods=('POST',))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/close', 'close_survey', RHCloseSurvey, methods=('POST',))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/submissions.csv', 'export_submissions', RHExportSubmissions,
                 methods=('POST',))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/submissions', 'delete_submissions', RHDeleteSubmissions,
                 methods=('DELETE',))

# Survey question management
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/', 'manage_questionnaire', RHManageSurveyQuestionnaire)
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/add/<type>', 'add_question', RHAddSurveyQuestion,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/<int:question_id>/', 'edit_question',
                 RHEditSurveyQuestion, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/<int:question_id>/', 'delete_question',
                 RHDeleteSurveyQuestion, methods=('DELETE',))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/sort-questions', 'sort_questions',
                 RHSortQuestions, methods=('POST',))
