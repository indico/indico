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

from indico.core import signals
from indico.modules.events.surveys.fields.base import SurveyField
from indico.web.fields import get_field_definitions


def get_field_types():
    """Gets a dict containing all field types"""
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
