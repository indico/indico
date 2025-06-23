# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash

from indico.modules.events.registration.controllers.management import RHManageRegFormsBase
from indico.modules.events.registration.settings import event_settings
from indico.util.i18n import _
from indico.web.forms.base import FormDefaults, IndicoForm
from indico.web.forms.fields import IndicoMarkdownField
from indico.web.util import jsonify_data, jsonify_template


class RegistrationDescriptionForm(IndicoForm):
    description = IndicoMarkdownField('Registration Description', render_kw={'rows': 10})


class RHManageRegistrationDescription(RHManageRegFormsBase):
    """Manage registration description."""

    def _process(self):
        form = RegistrationDescriptionForm(
            obj=FormDefaults(
                description=event_settings.get(self.event, 'registration_description')
            )
        )
        if form.validate_on_submit():
            event_settings.set(self.event, 'registration_description', form.description.data)
            flash(_('Registration description has been saved'), 'success')
            return jsonify_data()
        return jsonify_template(
            'events/registration/management/registration_description.html',
            form=form,
            event=self.event
        )
