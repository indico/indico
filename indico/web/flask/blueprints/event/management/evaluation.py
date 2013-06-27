# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh import evaluationModif
from indico.web.flask.util import rh_as_view, redirect_view
from indico.web.flask.blueprints.event.management import event_mgmt


# Setup
event_mgmt.add_url_rule('/evaluation/', 'confModifEvaluation', redirect_view('.confModifEvaluation-setup'))
event_mgmt.add_url_rule('/evaluation/setup/', 'confModifEvaluation-setup',
                        rh_as_view(evaluationModif.RHEvaluationSetup))
event_mgmt.add_url_rule('/evaluation/setup/change-status', 'confModifEvaluation-changeStatus',
                        rh_as_view(evaluationModif.RHEvaluationSetupChangeStatus), methods=('POST',))
event_mgmt.add_url_rule('/evaluation/setup/modify', 'confModifEvaluation-dataModif',
                        rh_as_view(evaluationModif.RHEvaluationSetupDataModif), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/evaluation/setup/modify/save', 'confModifEvaluation-performDataModif',
                        rh_as_view(evaluationModif.RHEvaluationSetupPerformDataModif), methods=('POST',))
event_mgmt.add_url_rule('/evaluation/setup/special-action', 'confModifEvaluation-specialAction',
                        rh_as_view(evaluationModif.RHEvaluationSetupSpecialAction), methods=('POST',))

# Edit questions
event_mgmt.add_url_rule('/evaluation/edit', 'confModifEvaluation-edit',
                        rh_as_view(evaluationModif.RHEvaluationEdit))
event_mgmt.add_url_rule('/evaluation/edit', 'confModifEvaluation-editPerformChanges',
                        rh_as_view(evaluationModif.RHEvaluationEditPerformChanges), methods=('POST',))

# Preview
event_mgmt.add_url_rule('/evaluation/preview', 'confModifEvaluation-preview',
                        rh_as_view(evaluationModif.RHEvaluationPreview), methods=('GET', 'POST'))

# Results
event_mgmt.add_url_rule('/evaluation/results/', 'confModifEvaluation-results',
                        rh_as_view(evaluationModif.RHEvaluationResults), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/evaluation/results/options', 'confModifEvaluation-resultsOptions',
                        rh_as_view(evaluationModif.RHEvaluationResultsOptions), methods=('POST',))
event_mgmt.add_url_rule('/evaluation/results/perform-action', 'confModifEvaluation-resultsSubmittersActions',
                        rh_as_view(evaluationModif.RHEvaluationResultsSubmittersActions), methods=('POST',))
