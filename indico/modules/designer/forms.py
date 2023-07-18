# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms import BooleanField, StringField
from wtforms.validators import DataRequired

from indico.modules.categories.fields import CategoryField
from indico.modules.designer.models.templates import TemplateType
from indico.util.i18n import _
from indico.web.forms.base import IndicoForm
from indico.web.forms.fields import IndicoEnumSelectField
from indico.web.forms.widgets import SwitchWidget


class AddTemplateForm(IndicoForm):
    title = StringField(_('Title'), [DataRequired()])
    type = IndicoEnumSelectField(_('Template'), enum=TemplateType, default=TemplateType.poster)
    is_clonable = BooleanField(_('Allow cloning'), widget=SwitchWidget(), default=True,
                               description=_('Allow cloning this template in subcategories and events'))


class CloneTemplateForm(IndicoForm):
    category = CategoryField(_('Category'), [DataRequired()], require_category_management_rights=True,
                             show_warning_message=False)
