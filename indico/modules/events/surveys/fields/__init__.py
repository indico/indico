# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core import signals
from indico.modules.events.surveys.fields.base import SurveyField
from indico.web.fields import get_field_definitions


def get_field_types():
    """Get a dict containing all field types."""
    return get_field_definitions(SurveyField)


@signals.get_fields.connect_via(SurveyField)
def _get_fields(sender, **kwargs):
    from .simple import SurveyTextField, SurveyNumberField, SurveyBoolField
    from .choices import SurveySingleChoiceField, SurveyMultiSelectField
    yield SurveyTextField
    yield SurveyNumberField
    yield SurveyBoolField
    yield SurveySingleChoiceField
    yield SurveyMultiSelectField


@signals.app_created.connect
def _check_field_definitions(app, **kwargs):
    # This will raise RuntimeError if the field names are not unique
    get_field_types()
