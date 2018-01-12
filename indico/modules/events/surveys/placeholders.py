# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
