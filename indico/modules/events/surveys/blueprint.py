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

from indico.modules.events.surveys.controllers.display import RHSurveyList, RHSubmitSurvey, RHSaveSurveyAnswers
from indico.modules.events.surveys.controllers.management.questionnaire import (RHManageSurveyQuestionnaire,
                                                                                RHExportSurveyQuestionnaire,
                                                                                RHImportSurveyQuestionnaire,
                                                                                RHAddSurveyText, RHEditSurveyText,
                                                                                RHDeleteSurveyText, RHAddSurveyQuestion,
                                                                                RHEditSurveyQuestion,
                                                                                RHDeleteSurveyQuestion,
                                                                                RHAddSurveySection, RHEditSurveySection,
                                                                                RHDeleteSurveySection,
                                                                                RHSortSurveyItems)
from indico.modules.events.surveys.controllers.management.results import (RHSurveyResults, RHExportSubmissionsCSV,
                                                                          RHExportSubmissionsExcel, RHDeleteSubmissions,
                                                                          RHDisplaySubmission)
from indico.modules.events.surveys.controllers.management.survey import (RHManageSurveys, RHManageSurvey, RHEditSurvey,
                                                                         RHDeleteSurvey, RHCreateSurvey,
                                                                         RHScheduleSurvey, RHCloseSurvey, RHOpenSurvey,
                                                                         RHSendSurveyLinks)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('surveys', __name__, template_folder='templates', virtual_template_folder='events/surveys',
                      url_prefix='/event/<confId>', event_feature='surveys')

# survey display/submission
_bp.add_url_rule('/surveys/', 'display_survey_list', RHSurveyList)
_bp.add_url_rule('/surveys/<int:survey_id>', 'display_survey_form', RHSubmitSurvey, methods=('GET', 'POST'))
_bp.add_url_rule('/surveys/<int:survey_id>/save', 'display_save_answers', RHSaveSurveyAnswers, methods=('POST',))

# survey management
_bp.add_url_rule('/manage/surveys/', 'manage_survey_list', RHManageSurveys)
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
_bp.add_url_rule('/manage/surveys/<int:survey_id>/submissions.csv', 'export_submissions_csv', RHExportSubmissionsCSV,
                 methods=('POST',))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/submissions.xlsx', 'export_submissions_excel',
                 RHExportSubmissionsExcel, methods=('POST',))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/submissions', 'delete_submissions', RHDeleteSubmissions,
                 methods=('DELETE',))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/submission/<int:submission_id>', 'display_submission',
                 RHDisplaySubmission)
_bp.add_url_rule('/manage/surveys/<int:survey_id>/send-links', 'send_links', RHSendSurveyLinks, methods=('POST',))

# Survey questionnaire management
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/', 'manage_questionnaire', RHManageSurveyQuestionnaire)
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/sort', 'sort_items', RHSortSurveyItems,
                 methods=('POST',))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/survey.json', 'export_questionnaire',
                 RHExportSurveyQuestionnaire)
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/import', 'import_questionnaire',
                 RHImportSurveyQuestionnaire, methods=('GET', 'POST'))

# sections
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/add-section', 'add_section', RHAddSurveySection,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/<int:section_id>/', 'edit_section', RHEditSurveySection,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/<int:section_id>/', 'delete_section',
                 RHDeleteSurveySection, methods=('DELETE',))
# text
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/<int:section_id>/text/add', 'add_text',
                 RHAddSurveyText, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/<int:section_id>/text/<int:text_id>', 'edit_text',
                 RHEditSurveyText, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/<int:section_id>/text/<int:text_id>', 'delete_text',
                 RHDeleteSurveyText, methods=('DELETE',))
# questions
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/<int:section_id>/question/add-<type>', 'add_question',
                 RHAddSurveyQuestion, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/<int:section_id>/question/<int:question_id>',
                 'edit_question', RHEditSurveyQuestion, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/surveys/<int:survey_id>/questionnaire/<int:section_id>/question/<int:question_id>',
                 'delete_question', RHDeleteSurveyQuestion, methods=('DELETE',))
