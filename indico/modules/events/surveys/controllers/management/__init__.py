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

from flask import request

from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.surveys.models.surveys import Survey


class RHManageSurveysBase(RHManageEventBase):
    """Base class for all survey management RHs"""

    ROLE = 'surveys'


class RHManageSurveyBase(RHManageSurveysBase):
    """Base class for specific survey management RHs."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.survey
        }
    }

    def _checkParams(self, params):
        RHManageSurveysBase._checkParams(self, params)
        self.survey = Survey.find_one(id=request.view_args['survey_id'], is_deleted=False)
