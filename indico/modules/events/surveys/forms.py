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

from __future__ import unicode_literals

from markupsafe import escape
from wtforms.fields import StringField, TextAreaField, BooleanField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import DataRequired, Optional, NumberRange

from indico.core.db import db
from indico.modules.events.surveys.models.surveys import Survey
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoDateTimeField
from indico.web.forms.widgets import SwitchWidget
from indico.web.forms.validators import HiddenUnless, ValidationError, DateTimeRange, LinkedDateTime
from indico.util.i18n import _


class SurveyForm(IndicoForm):
    title = StringField(_("Title"), [DataRequired()], description=_("The title of the survey"))
    description = TextAreaField(_("Description"), [DataRequired()], description=_("The description of the survey"))
    introduction = TextAreaField(_("Introduction"), description=_("An introduction to be displayed before the survey"))
    anonymous = BooleanField(_("Anonymous submissions"), widget=SwitchWidget(),
                             description=_("User information will not be attached to submissions"))
    require_user = BooleanField(_("Only logged users"), [HiddenUnless('anonymous')], widget=SwitchWidget(),
                                description=_("Still require users to be logged in for submitting the survey"))
    limit_submissions = BooleanField(_("Limit submissions"), widget=SwitchWidget(),
                                     description=_("Whether there is a submission cap"))
    submission_limit = IntegerField(_("Capacity"),
                                    [HiddenUnless('limit_submissions'), DataRequired(), NumberRange(min=1)],
                                    description=_("Maximum number of submissions accepted"))

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super(IndicoForm, self).__init__(*args, **kwargs)

    def validate_title(self, field):
        query = Survey.find(Survey.event_id == self.event.id,
                            db.func.lower(Survey.title) == field.data.lower(),
                            Survey.title != field.object_data)
        if query.count():
            raise ValidationError(_("There is already an survey named \"{}\" on this event".format(escape(field.data))))

    def validate_require_user(self, field):
        if not field.data and not self.anonymous.data:
            raise ValidationError(_("Guests can't submit surveys if submissions are not anonymous"))


class ScheduleSurveyForm(IndicoForm):
    start_dt = IndicoDateTimeField(_("Start"), [DataRequired(), DateTimeRange(earliest='now')],
                                   description=_("Moment when the survey will open for submissions"))
    end_dt = IndicoDateTimeField(_("End"), [Optional(), LinkedDateTime('start_dt')],
                                 description=_("Moment when the survey will close"))

    def __init__(self, *args, **kwargs):
        self.survey = kwargs.pop('survey', None)
        self.timezone = self.survey.event.getTimezone()
        super(IndicoForm, self).__init__(*args, **kwargs)
