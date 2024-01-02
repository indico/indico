# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, redirect

from indico.core.db import db
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.management.forms import EventPrivacyForm
from indico.modules.events.management.settings import privacy_settings
from indico.modules.events.management.views import WPEventPrivacy
from indico.modules.events.operations import update_event_privacy
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHEventPrivacy(RHManageEventBase):
    """Show event privacy dashboard."""

    def _process(self):
        form = EventPrivacyForm(obj=FormDefaults(**privacy_settings.get_all(self.event)), event=self.event)
        if form.validate_on_submit():
            update_event_privacy(self.event, form.data)
            flash(_('Privacy settings have been updated'), 'success')
            return redirect(url_for('.privacy_dashboard', self.event))
        regforms = (RegistrationForm.query
                    .with_parent(self.event)
                    .order_by(db.func.lower(RegistrationForm.title))
                    .all())
        return WPEventPrivacy.render_template('privacy_dashboard.html', self.event, 'privacy_dashboard', form=form,
                                              regforms=regforms)
