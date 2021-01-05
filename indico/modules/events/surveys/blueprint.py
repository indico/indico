# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.surveys.controllers.display import RHSaveSurveyAnswers, RHSubmitSurvey, RHSurveyList
from indico.modules.events.surveys.controllers.management.questionnaire import (RHAddSurveyQuestion, RHAddSurveySection,
                                                                                RHAddSurveyText, RHDeleteSurveyQuestion,
                                                                                RHDeleteSurveySection,
                                                                                RHDeleteSurveyText,
                                                                                RHEditSurveyQuestion,
                                                                                RHEditSurveySection, RHEditSurveyText,
                                                                                RHExportSurveyQuestionnaire,
                                                                                RHImportSurveyQuestionnaire,
                                                                                RHManageSurveyQuestionnaire,
                                                                                RHSortSurveyItems)
from indico.modules.events.surveys.controllers.management.results import (RHDeleteSubmissions, RHDisplaySubmission,
                                                                          RHExportSubmissionsCSV,
                                                                          RHExportSubmissionsExcel, RHSurveyResults)
from indico.modules.events.surveys.controllers.management.survey import (RHCloseSurvey, RHCreateSurvey, RHDeleteSurvey,
                                                                         RHEditSurvey, RHManageSurvey, RHManageSurveys,
                                                                         RHOpenSurvey, RHScheduleSurvey,
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
