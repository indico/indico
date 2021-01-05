# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from markupsafe import Markup, escape

from indico.util.i18n import _
from indico.util.placeholders import Placeholder
from indico.web.flask.util import url_for


class EventTitlePlaceholder(Placeholder):
    name = 'event_title'
    description = _("The title of the event")

    @classmethod
    def render(cls, event, survey, **kwargs):
        return event.title


class SurveyTitlePlaceholder(Placeholder):
    name = 'survey_title'
    description = _("The title of the survey")

    @classmethod
    def render(cls, event, survey, **kwargs):
        return survey.title


class SurveyLinkPlaceholder(Placeholder):
    name = 'survey_link'
    description = _("Link to the survey")
    required = True

    @classmethod
    def render(cls, event, survey, **kwargs):
        url = url_for('.display_survey_form', survey, survey.locator.token, _external=True)
        return Markup('<a href="{url}" title="{title}">{url}</a>'.format(url=url, title=escape(survey.title)))
