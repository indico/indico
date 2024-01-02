# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request

from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.surveys.models.surveys import Survey


class RHManageSurveysBase(RHManageEventBase):
    """Base class for all survey management RHs."""

    PERMISSION = 'surveys'


class RHManageSurveyBase(RHManageSurveysBase):
    """Base class for specific survey management RHs."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.survey
        }
    }

    def _process_args(self):
        RHManageSurveysBase._process_args(self)
        self.survey = Survey.query.filter_by(id=request.view_args['survey_id'], is_deleted=False).one()
