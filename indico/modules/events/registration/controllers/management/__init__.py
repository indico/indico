# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request, session
from sqlalchemy.orm import contains_eager, defaultload
from werkzeug.exceptions import Forbidden

from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.registration.controllers import RegistrationFormMixin
from indico.modules.events.registration.lists import RegistrationListGenerator
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.util import check_event_locked
from indico.util.i18n import _


def _can_manage_registration(event, user):
    """Check if the user has any registration-related management permission."""
    return any(event.can_manage(user, permission=p)
               for p in ('registration', 'registration_moderation', 'registration_checkin'))


class _RegistrationAccessMixin:
    """Mixin granting access to users with any registration management permission."""

    def _check_access(self):
        self._require_user()
        if not _can_manage_registration(self.event, session.user):
            raise Forbidden(_('You are not authorized to manage this event.'))
        check_event_locked(self, self.event)


class _ModerationAccessMixin:
    """Mixin granting access to users with 'registration' or 'registration_moderation' permission."""

    def _check_access(self):
        self._require_user()
        if not (self.event.can_manage(session.user, permission='registration') or
                self.event.can_manage(session.user, permission='registration_moderation')):
            raise Forbidden(_('You are not authorized to manage this event.'))
        check_event_locked(self, self.event)


class _CheckinAccessMixin:
    """Mixin granting access to users with 'registration' or 'registration_checkin' permission."""

    def _check_access(self):
        self._require_user()
        if not (self.event.can_manage(session.user, permission='registration') or
                self.event.can_manage(session.user, permission='registration_checkin')):
            raise Forbidden(_('You are not authorized to manage this event.'))
        check_event_locked(self, self.event)


class RHManageRegFormsBase(RHManageEventBase):
    """Base class for all registration management RHs."""

    PERMISSION = 'registration'


class RHManageRegFormBase(RegistrationFormMixin, RHManageRegFormsBase):
    """Base class for a specific registration form."""

    def _process_args(self):
        RHManageRegFormsBase._process_args(self)
        RegistrationFormMixin._process_args(self)
        self.list_generator = RegistrationListGenerator(regform=self.regform)


class RHManageRegistrationBase(RHManageRegFormBase):
    """Base class for a specific registration."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.registration
        }
    }

    def _process_args(self):
        RHManageRegFormBase._process_args(self)
        self.registration = (Registration.query
                             .filter(Registration.id == request.view_args['registration_id'],
                                     ~Registration.is_deleted,
                                     ~RegistrationForm.is_deleted)
                             .join(Registration.registration_form)
                             .options(contains_eager(Registration.registration_form)
                                      .defaultload('form_items')
                                      .joinedload('children'))
                             .options(defaultload(Registration.data)
                                      .joinedload('field_data'))
                             .one())


class RHManageRegistrationFieldActionBase(RHManageRegFormBase):
    """Base class for a specific registration field."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.field
        },
        'skipped_args': {'section_id'}
    }

    def _process_args(self):
        RHManageRegFormBase._process_args(self)
        self.field = (RegistrationFormField.query
                      .filter(RegistrationFormField.id == request.view_args['field_id'],
                              RegistrationFormField.registration_form == self.regform,
                              RegistrationFormField.is_enabled,
                              ~RegistrationFormField.is_deleted)
                      .one())
