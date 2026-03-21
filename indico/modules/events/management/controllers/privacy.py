# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, redirect

from indico.core.db import db
from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.management.forms import EventPrivacyForm
from indico.modules.events.management.views import WPEventPrivacy
from indico.modules.events.operations import get_event_privacy, update_event_privacy
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class RHEventPrivacy(RHManageEventBase):
    """Show event privacy dashboard."""

    def _process(self):
        event_privacy, inherited = get_event_privacy(self.event)
        lock_privacy_settings = False
        if inherited:
            lock_privacy_settings = bool(event_privacy.get('lock_privacy_data'))
        form = EventPrivacyForm(obj=FormDefaults(**event_privacy), event=self.event)
        if form.validate_on_submit():
            if lock_privacy_settings:
                flash(_('The privacy settings is locked in a parent category and cannot be modified here.'), 'error')
                return redirect(url_for('.privacy_dashboard', self.event))
            update_event_privacy(self.event, form.data)
            flash(_('Privacy settings have been updated'), 'success')
            return redirect(url_for('.privacy_dashboard', self.event))
        regforms = (RegistrationForm.query
                    .with_parent(self.event)
                    .order_by(db.func.lower(RegistrationForm.title))
                    .all())
        return WPEventPrivacy.render_template('privacy_dashboard.html', self.event, 'privacy_dashboard', form=form,
                                              regforms=regforms, inherited=inherited,
                                              lock_privacy_settings=lock_privacy_settings)
