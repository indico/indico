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

from MaKaC.webinterface.rh import evaluationDisplay
from indico.web.flask.blueprints.event.display import event


# Evaluation
event.add_url_rule('/evaluation-old/', 'confDisplayEvaluation', evaluationDisplay.RHEvaluationMainInformation)
event.add_url_rule('/evaluation-old/evaluate', 'confDisplayEvaluation-display', evaluationDisplay.RHEvaluationDisplay)
event.add_url_rule('/evaluation-old/evaluate', 'confDisplayEvaluation-modif', evaluationDisplay.RHEvaluationDisplay)
event.add_url_rule('/evaluation-old/evaluate', 'confDisplayEvaluation-submit', evaluationDisplay.RHEvaluationSubmit,
                   methods=('POST',))
event.add_url_rule('/evaluation-old/evaluate/success', 'confDisplayEvaluation-submitted',
                   evaluationDisplay.RHEvaluationSubmitted)
