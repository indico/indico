# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from markupsafe import Markup, escape

from indico.util.i18n import _
from indico.util.placeholders import ParametrizedPlaceholder, Placeholder
from indico.web.flask.util import url_for


class SurveyTitlePlaceholder(Placeholder):
    name = 'survey_title'
    description = _('The title of the survey')

    @classmethod
    def render(cls, event, survey, **kwargs):
        return survey.title


class SurveyLinkPlaceholder(ParametrizedPlaceholder):
    name = 'survey_link'
    param_friendly_name = 'link title'
    required = True

    @classmethod
    def render(cls, param, survey, **kwargs):
        url = url_for('.display_survey_form', survey, survey.locator.token, _external=True)
        return Markup(f'<a href="{url}" title="{escape(survey.title)}">{param or url}</a>')

    @classmethod
    def iter_param_info(cls, **kwargs):
        yield None, _('Link to the survey')
        yield 'custom-text', _('Custom link text instead of the full URL')
