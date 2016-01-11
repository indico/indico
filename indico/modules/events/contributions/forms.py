# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from datetime import timedelta

from wtforms.fields import StringField, TextAreaField
from wtforms.validators import DataRequired

from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import TimeDeltaField
from indico.util.i18n import _


class ContributionForm(IndicoForm):
    title = StringField(_("Title"), [DataRequired()])
    description = TextAreaField(_("Description"))
    duration = TimeDeltaField(_("Duration"), [DataRequired()], default=timedelta(minutes=20),
                              units=('minutes', 'hours'),
                              description=_("The duration of the contribution"))
