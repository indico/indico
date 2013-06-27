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

from MaKaC.webinterface.rh import evaluationDisplay
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.display import event


# Evaluation
event.add_url_rule('/<confId>/evaluation/', 'confDisplayEvaluation',
                   rh_as_view(evaluationDisplay.RHEvaluationMainInformation))
event.add_url_rule('/<confId>/evaluation/evaluate', 'confDisplayEvaluation-display',
                   rh_as_view(evaluationDisplay.RHEvaluationDisplay))
event.add_url_rule('/<confId>/evaluation/evaluate', 'confDisplayEvaluation-modif',
                   rh_as_view(evaluationDisplay.RHEvaluationDisplay))
event.add_url_rule('/<confId>/evaluation/signin', 'confDisplayEvaluation-signIn',
                   rh_as_view(evaluationDisplay.RHEvaluationSignIn))
event.add_url_rule('/<confId>/evaluation/evaluate', 'confDisplayEvaluation-submit',
                   rh_as_view(evaluationDisplay.RHEvaluationSubmit), methods=('POST',))
event.add_url_rule('/<confId>/evaluation/evaluate/success', 'confDisplayEvaluation-submitted',
                   rh_as_view(evaluationDisplay.RHEvaluationSubmitted))
