# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

from flask import redirect, session
from flask.helpers import flash
from marshmallow_enum import EnumField

from indico.core.db import db
from indico.modules.events import EventLogRealm
from indico.modules.events.registration.controllers.display import RHRegistrationFormRegistrationBase
from indico.modules.events.registration.controllers.management import RHManageRegFormBase
from indico.modules.events.registration.forms import RegistrationPrivacyForm
from indico.modules.events.registration.models.registrations import PublishRegistrationsMode, RegistrationVisibility
from indico.modules.events.registration.util import update_registration_consent_to_publish
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.logs.models.entries import LogKind
from indico.modules.logs.util import make_diff_log
from indico.util.i18n import _
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for


class RHRegistrationPrivacy(RHManageRegFormBase):
    """Change privacy settings of a registration form."""

    def _get_changes(self, participant_visibility, public_visibility, visibility_duration, retention_period):
        log_fields = {
            'participant_visibility': {'title': 'Visibility to participants'},
            'public_visibility': {'title': 'Visibility to everyone'},
            'visibility_duration': {'title': 'Visibility duration', 'default': 'Indefinite'},
            'retention_period': {'title': 'Retention period', 'default': 'Indefinite'},
        }

        changes = {
            'participant_visibility': (self.regform.publish_registrations_participants,
                                       PublishRegistrationsMode[participant_visibility]),
            'public_visibility': (self.regform.publish_registrations_public,
                                  PublishRegistrationsMode[public_visibility]),
            'visibility_duration': (self.regform.publish_registrations_duration
                                    if self.regform.publish_registrations_duration is not None else None,
                                    visibility_duration if visibility_duration is not None else None),
            'retention_period': (self.regform.retention_period
                                 if self.regform.retention_period is not None else None,
                                 retention_period if retention_period is not None else None),
        }
        changes = {key: (old, new) for key, (old, new) in changes.items() if old != new}
        return make_diff_log(changes, log_fields)

    def _process(self):
        form = RegistrationPrivacyForm(event=self.event, regform=self.regform, visibility=[
            self.regform.publish_registrations_participants.name,
            self.regform.publish_registrations_public.name,
            (self.regform.publish_registrations_duration.days // 7
             if self.regform.publish_registrations_duration is not None else None)
        ], retention_period=self.regform.retention_period)
        if form.validate_on_submit():
            participant_visibility, public_visibility, visibility_duration = form.visibility.data
            visibility_duration = timedelta(weeks=visibility_duration) if visibility_duration is not None else None
            changes = self._get_changes(participant_visibility, public_visibility,
                                        visibility_duration, form.retention_period.data)
            self.regform.retention_period = form.retention_period.data
            self.regform.publish_registrations_participants = PublishRegistrationsMode[participant_visibility]
            self.regform.publish_registrations_public = PublishRegistrationsMode[public_visibility]
            self.regform.publish_registrations_duration = visibility_duration
            db.session.flush()
            self.event.log(EventLogRealm.management, LogKind.change, 'Privacy',
                           f'Participant visibility for "{self.regform.title}" modified', session.user,
                           data={'Changes': changes})
            flash(_('Settings saved'), 'success')
            return redirect(url_for('.manage_registration_privacy_settings', self.regform))

        return WPManageRegistration.render_template('management/regform_privacy.html', self.event,
                                                    regform=self.regform, form=form)


class RHAPIRegistrationChangeConsent(RHRegistrationFormRegistrationBase):
    """Internal API to change registration consent to publish."""

    @use_kwargs({'consent_to_publish': EnumField(RegistrationVisibility)})
    def _process_POST(self, consent_to_publish):
        update_registration_consent_to_publish(self.registration, consent_to_publish)
        return '', 204
