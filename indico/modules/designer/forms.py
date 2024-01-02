# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from wtforms import BooleanField, StringField
from wtforms.validators import DataRequired, ValidationError

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
    category = CategoryField(_('Category'), [DataRequired()], require_category_management_rights=True)

    def validate_category(self, field):
        if not field.data.can_manage(session.user):
            # only happens if someone tampers with the client-side check in the category picker
            raise ValidationError('Not a manager')
