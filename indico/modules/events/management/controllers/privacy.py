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


class RHPrivacyMixin:
    """Mixix for event/category privacy dashboard."""

    ERROR_FLASH_MESSAGE = _('The privacy settings is locked in a parent category and cannot be modified here.')
    SUCCESS_FLASH_MESSAGE = _('Privacy settings have been updated')

    def _get_privacy_data(self):
        raise NotImplementedError

    def _update_privacy(self, *args):
        raise NotImplementedError

    def _get_form(self):
        raise NotImplementedError

    def _render_template(self, **kwargs):
        raise NotImplementedError

    def _redirect_url(self):
        raise NotImplementedError

    def _process(self):
        privacy_data, inherited = self._get_privacy_data()
        lock_privacy_settings = privacy_data.get('lock_privacy_data', False) if inherited else False
        form = self._get_form(**privacy_data)
        if form.validate_on_submit():
            if lock_privacy_settings:
                flash(self.ERROR_FLASH_MESSAGE, 'error')
                return redirect(self._redirect_url())
            self._update_privacy(form.data)
            flash(self.SUCCESS_FLASH_MESSAGE, 'success')
            return redirect(self._redirect_url())
        return self._render_template(form=form, inherited=inherited, lock_privacy_settings=lock_privacy_settings)


class RHEventPrivacy(RHPrivacyMixin, RHManageEventBase):
    """Show event privacy dashboard."""

    def _get_privacy_data(self):
        return get_event_privacy(self.event)

    def _update_privacy(self, data):
        update_event_privacy(self.event, data)

    def _get_form(self, **kwargs):
        return EventPrivacyForm(obj=FormDefaults(**kwargs), event=self.event)

    def _redirect_url(self):
        return url_for('.privacy_dashboard', self.event)

    def _render_template(self, **kwargs):
        regforms = (RegistrationForm.query
                    .with_parent(self.event)
                    .order_by(db.func.lower(RegistrationForm.title))
                    .all())
        return WPEventPrivacy.render_template('privacy_dashboard.html', self.event, 'privacy_dashboard',
                                              regforms=regforms, **kwargs)
