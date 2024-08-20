# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import jsonify, request, session
from sqlalchemy.orm import defaultload
from werkzeug.exceptions import UnprocessableEntity

from indico.modules.events.payment import payment_event_settings
from indico.modules.events.registration.fields.simple import KEEP_EXISTING_FILE_UUID
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.util import (check_registration_email, get_flat_section_submission_data,
                                                     get_form_registration_data, make_registration_schema,
                                                     modify_registration, process_registration_picture)
from indico.modules.files.controllers import UploadFileMixin
from indico.util.marshmallow import LowercaseString, UUIDString, not_empty
from indico.web.args import parser, use_kwargs


class RegistrationFormMixin:
    """Mixin for single registration form RH."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.regform
        }
    }

    def _process_args(self):
        self.regform = (RegistrationForm.query
                        .filter_by(id=request.view_args['reg_form_id'], is_deleted=False)
                        .options(defaultload('form_items').joinedload('children').joinedload('current_data'))
                        .one())


class RegistrationEditMixin:
    def _get_file_data(self):
        locator_name = 'file' if self.management else 'registrant_file'
        return {r.field_data.field.html_field_name: {'filename': r.filename, 'size': r.size,
                                                     'uuid': KEEP_EXISTING_FILE_UUID,
                                                     'locator': getattr(r.locator, locator_name)}
                for r in self.registration.data
                if r.field_data.field.field_impl.is_file_field and r.storage_file_id is not None}

    def _get_optional_fields(self):
        """Get fields for which we already have a value and thus are not required."""
        if self.management:
            # In management mode, all fields are optional
            return True

        data_by_field = self.registration.data_by_field
        return [form_item.html_field_name for form_item in self.regform.active_fields
                if data_by_field.get(form_item.id) is not None]

    def _process_POST(self):
        optional_fields = self._get_optional_fields()
        schema = make_registration_schema(
            self.regform,
            management=self.management,
            registration=self.registration,
            override_required=self.management
        )(partial=optional_fields)
        form_data = parser.parse(schema)

        notify_user = not self.management or form_data.pop('notify_user', False)
        if self.management:
            session['registration_notify_user_default'] = notify_user
        modify_registration(self.registration, form_data, management=self.management, notify_user=notify_user)
        return jsonify({'redirect': self.success_url})

    def _process_GET(self):
        form_data = get_flat_section_submission_data(self.regform, management=self.management,
                                                     registration=self.registration)
        registration_data = get_form_registration_data(self.regform, self.registration, management=self.management)
        return self.view_class.render_template(self.template_file, self.event,
                                               regform=self.regform,
                                               form_data=form_data,
                                               payment_conditions=payment_event_settings.get(self.event, 'conditions'),
                                               payment_enabled=self.event.has_feature('payment'),
                                               registration=self.registration,
                                               management=self.management,
                                               paid=self.registration.is_paid,
                                               registration_data=registration_data,
                                               file_data=self._get_file_data())


class CheckEmailMixin:
    """Check how an email will affect the registration."""

    @use_kwargs({
        'email': LowercaseString(required=True, validate=not_empty),
        'update': UUIDString(load_default=None),
    }, location='query')
    def _process_args(self, email, update):
        self.email = email
        self.update = update
        self.existing_registration = self.regform.get_registration(uuid=self.update) if self.update else None

    def _check_email(self, *, management=False):
        if self.update:
            return jsonify(check_registration_email(self.regform, self.email, self.existing_registration,
                                                    management=management))
        else:
            return jsonify(check_registration_email(self.regform, self.email, management=management))


class UploadRegistrationFileMixin(UploadFileMixin):
    """Upload a file from a registration form.

    Regform file fields do not wait for the regform to be submitted,
    but upload the selected files immediately, saving just the generated uuid.
    Only this uuid is then sent when the regform is submitted.
    """

    def get_file_context(self):
        return 'event', self.event.id, 'regform', self.regform.id, 'registration'


class UploadRegistrationPictureMixin:
    """Perform additional validation for regform picture uploads.

    This mixin must be used in addition to `UploadRegistrationFileMixin`.
    """

    def _save_file(self, file, stream):
        if not (resized_image_stream := process_registration_picture(stream)):
            raise UnprocessableEntity('Could not process image, it may be corrupted or too big')
        return super()._save_file(file, resized_image_stream)

    def get_file_metadata(self):
        return {'registration_picture_checked': True}
