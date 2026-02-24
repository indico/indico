# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import redirect, session
from flask.helpers import flash

from indico.core.db import db
from indico.modules.categories.views import WPCategoryManageRegistrationForm
from indico.modules.events import EventLogRealm
from indico.modules.events.registration.views import WPEventManageRegistrationForm
from indico.modules.formify.controllers.management.regforms import ManageRegistrationFormsAreaMixin
from indico.modules.formify.forms import RegistrationPrivacyForm
from indico.modules.logs.models.entries import CategoryLogRealm, LogKind
from indico.modules.logs.util import make_diff_log
from indico.util.i18n import _
from indico.web.flask.util import url_for


class RHRegistrationPrivacyMixin(ManageRegistrationFormsAreaMixin):
    """Mixin to change the privacy settings of a registration form."""

    _log_fields = {
        'publish_registrations_participants': {'title': 'Visibility to participants'},
        'publish_registrations_public': {'title': 'Visibility to everyone'},
        'publish_registrations_duration': {'title': 'Visibility duration', 'default': 'Indefinite'},
        'retention_period': {'title': 'Retention period', 'default': 'Indefinite'},
        'require_privacy_policy_agreement': {'title': 'Privacy policy'},
    }

    def _process(self):
        form = RegistrationPrivacyForm(
            target=self.target,
            regform=self.regform,
            retention_period=self.regform.retention_period,
            require_privacy_policy_agreement=self.regform.require_privacy_policy_agreement,
            visibility=[
                self.regform.publish_registrations_participants.name,
                self.regform.publish_registrations_public.name,
                (self.regform.publish_registrations_duration.days // 7
                 if self.regform.publish_registrations_duration is not None else None)
            ]
        )
        if form.validate_on_submit():
            changes = self.regform.populate_from_dict(form.data)
            db.session.flush()
            if self.object_type == 'event':
                self.event.log(EventLogRealm.management, LogKind.change, 'Privacy',
                            f'Privacy settings for "{self.regform.title}" modified', session.user,
                            data={'Changes': make_diff_log(changes, self._log_fields)})
            else:
                self.category.log(CategoryLogRealm.management, LogKind.change, 'Privacy',
                            f'Privacy settings for "{self.regform.title}" modified', session.user,
                            data={'Changes': make_diff_log(changes, self._log_fields)})
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.manage_registration_privacy_settings', self.regform))
        view_class = (WPCategoryManageRegistrationForm if self.object_type == 'category'
                      else WPEventManageRegistrationForm)
        return view_class.render_template('management/regform_privacy.html', self.target,
                                                    regform=self.regform, form=form)
