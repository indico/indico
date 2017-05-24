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

from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired

from indico.modules.designer.models.templates import TemplateType
from indico.modules.events.models.events import Event
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoEnumSelectField
from indico.web.forms.widgets import SwitchWidget


class AddTemplateForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()])
    type = IndicoEnumSelectField(_('Template'), enum=TemplateType, default=TemplateType.poster)
    is_clonable = BooleanField(_('Allow cloning'), widget=SwitchWidget(), default=True,
                               description=_("Allow event managers to clone this template."))

    def __init__(self,  *args, **kwargs):
        target = kwargs.pop('target')
        super(AddTemplateForm, self).__init__(*args, **kwargs)
        if isinstance(target, Event):
            del self.is_clonable
