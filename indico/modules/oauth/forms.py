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

from wtforms.fields import StringField, TextAreaField
from wtforms.validators import DataRequired, ValidationError

from indico.modules.oauth.models.clients import OAuthClient
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm


class OAuthAdminAddApplicationForm(IndicoForm):
    name = StringField(_("Name"), [DataRequired()])
    description = TextAreaField(_("Description"))

    def validate_name(self, field):
        if OAuthClient.find(name=field.data).count():
            raise ValidationError(_("There is already an application with this name"))
