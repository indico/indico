# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, request, session
from webargs import fields
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.core.errors import NoReportError
from indico.modules.events import EventLogRealm
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management import RHManageRegFormsBase, RHManageRegistrationBase
from indico.modules.events.registration.controllers.management.reglists import (RHRegistrationsActionBase,
                                                                                _render_registration_details)
from indico.modules.events.registration.forms import RegistrationChecksAssignForm, RegistrationCheckTypeForm
from indico.modules.events.registration.models.checks import RegistrationCheck, RegistrationCheckType
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.modules.events.registration.util import (create_registration_check, create_registration_check_type,
                                                     delete_registration_check_type, update_registration_check_type)
from indico.modules.events.registration.views import WPManageRegistration
from indico.modules.logs import LogKind
from indico.util.i18n import _
from indico.web.args import use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


def _render_registration_check_types(event):
    tpl = get_template_module('events/registration/management/_registration_check_type_list.html')
    return tpl.render_check_types(event.check_types, event)


class RHManageRegistrationCheckTypeBase(RHManageRegFormsBase):
    """Base class for a specific registration check type."""

    def _process_args(self):
        RHManageRegFormsBase._process_args(self)
        self.check_type = RegistrationCheckType.query.with_parent(self.event, 'check_types').filter(
            RegistrationCheckType.id == request.view_args['check_type_id']
        ).first_or_404()


class RHManageRegistrationCheckTypes(RHManageRegFormsBase):
    """List all check types for an event."""

    def _process(self):
        system_check_types = (RegistrationCheckType.query
                              .filter(RegistrationCheckType.is_system_defined)
                              .order_by(db.func.lower(RegistrationCheckType.title))
                              .all())
        return WPManageRegistration.render_template('management/registration_check_types.html', self.event,
                                                    system_check_types=system_check_types)


class RHRegistrationCheckTypeAdd(RHManageRegFormsBase):
    """Add a new registration check type."""

    def _process(self):
        form = RegistrationCheckTypeForm(event=self.event)
        if form.validate_on_submit():
            check_type = create_registration_check_type(form.data, self.event)
            flash(_('A new check type "{}" has been created.').format(check_type.title), 'success')
            return jsonify_data(html=_render_registration_check_types(self.event))
        return jsonify_form(form)


class RHRegistrationCheckTypeDelete(RHManageRegistrationCheckTypeBase):
    """Delete a registration check type."""

    def _process(self):
        if self.check_type == self.event.default_check_type:
            raise BadRequest(_('Cannot delete the current default check type of this event.'))
        delete_registration_check_type(self.check_type)
        flash(_('Check type "{}" has been deleted.').format(self.check_type.title), 'success')
        return jsonify_data(html=_render_registration_check_types(self.event))


class RHRegistrationCheckTypeEdit(RHManageRegistrationCheckTypeBase):
    """Modify an existing registration check type."""

    def _process(self):
        form = RegistrationCheckTypeForm(obj=self.check_type, event=self.event, check_type=self.check_type)
        if form.validate_on_submit():
            update_registration_check_type(self.check_type, form.data)
            flash(_('Check type "{}" has been modified.').format(self.check_type.title), 'success')
            return jsonify_data(html=_render_registration_check_types(self.event))
        return jsonify_form(form)


class RHRegistrationCheckTypeToggleDefault(RHManageRegFormsBase):
    """Toggle the default registration check type of the event."""

    @use_kwargs({
        'check_type_id': fields.Integer(),
    }, location='query')
    def _process(self, check_type_id):
        check_type = RegistrationCheckType.get_or_404(check_type_id)
        if not check_type.is_system_defined and check_type not in self.event.check_types:
            raise Exception('Invalid check type')
        if check_type != self.event.default_check_type:
            self.event.default_check_type = check_type
        return jsonify_data(flash=False)


class RHRegistrationChecks(RHManageRegistrationBase):
    def _process(self):
        return jsonify_template('events/registration/management/registration_checks.html',
                                registration=self.registration)


class RHRegistrationChecksAdd(RHManageRegistrationBase):
    """Set checked state of a registration."""

    @use_kwargs({
        'is_check_out': fields.Bool(load_default=False),
    }, location='query')
    def _process(self, is_check_out):
        action = 'Checked-out' if is_check_out else 'Checked-in'
        if self.registration.state not in (RegistrationState.complete, RegistrationState.unpaid):
            raise BadRequest(_('This registration cannot be marked as checked-in/checked-out'))
        try:
            create_registration_check(self.registration, is_check_out=is_check_out, checked_by_user=session.user)
        except ValueError as e:
            raise NoReportError(e)
        flash(_('Registration {} successfully.').format(action), 'success')
        return jsonify_data(html=_render_registration_details(self.registration))


class RHRegistrationChecksDelete(RHManageRegistrationBase):

    normalize_url_spec = {
        'locators': {
            lambda self: self.check
        }
    }

    def _process_args(self):
        self.check = RegistrationCheck.query.filter_by(id=request.view_args['check_id']).one()
        RHManageRegistrationBase._process_args(self)

    def _process(self):
        check_type = self.check.check_type
        self.registration.checks.remove(self.check)
        log_text = 'Previous registration check "{}" has been deleted for "{}"'
        self.registration.log(EventLogRealm.participants, LogKind.change, 'Registration',
                              log_text.format(check_type.title, self.registration.full_name), session.user)
        flash(_('Registration check deleted successfully.'), 'success')
        logger.info('Registration %s check "%s" deleted by %s', self.registration, check_type.title, session.user)
        return '', 204


class RHRegistrationChecksReset(RHManageRegistrationBase):

    def _process(self):
        self.registration.checks.clear()
        log_text = 'All previous registration checks has been deleted for "{}"'
        self.registration.log(EventLogRealm.participants, LogKind.change, 'Registration',
                              log_text.format(self.registration.full_name), session.user)
        flash(_('Registration checks reset successfully.'), 'success')
        logger.info('Registration %s checks reset by %s', self.registration, session.user)
        return '', 204


class RHRegistrationBulkCheck(RHRegistrationsActionBase):
    """Bulk apply check-in/check-out state to registrations."""

    @use_kwargs({
        'is_check_out': fields.Bool(load_default=False),
    }, location='query')
    def _process(self, is_check_out):
        form = RegistrationChecksAssignForm(self.event, check_type_id=self.event.default_check_type_id,
                                            registration_id=[r.id for r in self.registrations])
        submit_text = _('Check-out') if is_check_out else _('Check-in')
        if form.validate_on_submit():
            action = 'Checked-out' if is_check_out else 'Checked-in'
            check_type = RegistrationCheckType.query.get_or_404(form.check_type_id.data)
            for registration in self.registrations:
                if registration.state not in (RegistrationState.complete, RegistrationState.unpaid):
                    continue
                try:
                    create_registration_check(registration, check_type=check_type, is_check_out=is_check_out,
                                              checked_by_user=session.user)
                except ValueError:
                    pass
            flash(_('Selected registrations marked as {} successfully.').format(action), 'success')
            return jsonify_data(**self.list_generator.render_list())
        return jsonify_form(form, disabled_until_change=False, submit=submit_text)
