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

from wtforms.fields import StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired

from indico.modules.events.evaluation.models.evaluations import Evaluation
from indico.web.forms.base import IndicoForm
from indico.web.forms.widgets import SwitchWidget
from indico.web.forms.validators import HiddenUnless, ValidationError
from indico.util.i18n import _


class EvaluationForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()], description=_('The title of the evaluation'))
    description = TextAreaField(_('Description'), description=_('The description of the room'))
    anonymous = BooleanField(_("Anonymous submissions"),
                             description=_('User information will not be attached to submissions'),
                             widget=SwitchWidget())
    require_user = BooleanField(_("Only logged users"), [HiddenUnless('anonymous')],
                                description=_('Still require users to be logged in for submitting the evaluation'),
                                widget=SwitchWidget())

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super(IndicoForm, self).__init__(*args, **kwargs)

    def validate_title(self, field):
        query = Evaluation.find(Evaluation.event_id == self.event.id,
                                Evaluation.title == field.data,
                                Evaluation.title != field.object_data)
        if query.count():
            raise ValidationError(_("There is already an evaluation named {} on this event".format(field.data)))

    def validate_require_user(self, field):
        if not field.data and not self.anonymous.data:
            raise ValidationError(_("Guests can't submit evaluations if submissions are not anonymous"))
