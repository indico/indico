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

from indico.modules.events.evaluation.controllers.management import (RHManageEvaluations, RHManageEvaluation,
                                                                     RHEditEvaluation, RHScheduleEvaluation,
                                                                     RHManageEvaluationQuestionnaire,
                                                                     RHAddEvaluationQuestion, RHEditEvaluationQuestion,
                                                                     RHCreateEvaluation)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('evaluation', __name__, template_folder='templates', virtual_template_folder='events/evaluation',
                      url_prefix='/event/<confId>', event_feature='evaluation')

# Evaluations management
_bp.add_url_rule('/manage/evaluations/', 'management', RHManageEvaluations)
_bp.add_url_rule('/manage/evaluations/create', 'create', RHCreateEvaluation, methods=('GET', 'POST'))

# Sinle evaluation management
_bp.add_url_rule('/manage/evaluation/<evaluation_id>/', 'manage_evaluation', RHManageEvaluation)
_bp.add_url_rule('/manage/evaluation/<evaluation_id>/edit',
                 'edit_evaluation', RHEditEvaluation, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/evaluation/<evaluation_id>/schedule',
                 'schedule_evaluation', RHScheduleEvaluation, methods=('GET', 'POST'))

# Evaluation question management
_bp.add_url_rule('/manage/evaluation/<evaluation_id>/questionnaire/',
                 'manage_questionnaire', RHManageEvaluationQuestionnaire)
_bp.add_url_rule('/manage/evaluation/<evaluation_id>/questionnaire/add/<type>', 'add_question', RHAddEvaluationQuestion,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/evaluation/<evaluation_id>/questionnaire/<question_id>',
                 'edit_question', RHEditEvaluationQuestion, methods=('GET', 'POST'))
