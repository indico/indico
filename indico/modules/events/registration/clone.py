# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.cloning import EventCloner
from indico.modules.events.features.util import is_feature_enabled
from indico.modules.events.models.events import EventType
from indico.modules.events.registration.models.form_fields import RegistrationFormFieldData
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.items import RegistrationFormItem, RegistrationFormSection
from indico.modules.events.registration.models.registrations import Registration, RegistrationData
from indico.util.i18n import _


class RegistrationFormCloner(EventCloner):
    name = 'registration_forms'
    friendly_name = _('Registration forms')

    @property
    def is_visible(self):
        return is_feature_enabled(self.old_event, 'registration')

    @property
    def is_available(self):
        return bool(self.old_event.registration_forms)

    @no_autoflush
    def run(self, new_event, cloners, shared_data):
        # if the registration cloner is also enabled, we have to keep
        # all revisions since they are likely to be in use
        clone_all_revisions = 'registrations' in cloners
        attrs = get_simple_column_attrs(RegistrationForm) - {'start_dt', 'end_dt', 'modification_end_dt'}
        self._field_data_map = {}
        self._form_map = {}
        for old_form in self.old_event.registration_forms:
            new_form = RegistrationForm(**{attr: getattr(old_form, attr) for attr in attrs})
            self._clone_form_items(old_form, new_form, clone_all_revisions)
            new_event.registration_forms.append(new_form)
            db.session.flush()
            self._form_map[old_form] = new_form
        return {'form_map': self._form_map,
                'field_data_map': self._field_data_map}

    def _clone_form_items(self, old_form, new_form, clone_all_revisions):
        old_sections = RegistrationFormSection.find(RegistrationFormSection.registration_form_id == old_form.id)
        items_attrs = get_simple_column_attrs(RegistrationFormSection)
        for old_section in old_sections:
            new_section = RegistrationFormSection(**{attr: getattr(old_section, attr) for attr in items_attrs})
            for old_item in old_section.children:
                new_item = RegistrationFormItem(parent=new_section, registration_form=new_form,
                                                **{attr: getattr(old_item, attr) for attr in items_attrs})
                if new_item.is_field:
                    if clone_all_revisions:
                        self._clone_all_field_versions(old_item, new_item)
                    else:
                        field_data = RegistrationFormFieldData(field=new_item,
                                                               versioned_data=old_item.versioned_data)
                        new_item.current_data = field_data
                        self._field_data_map[old_item.current_data] = field_data
                new_section.children.append(new_item)
            new_form.form_items.append(new_section)
            db.session.flush()

    def _clone_all_field_versions(self, old_item, new_item):
        for old_version in old_item.data_versions:
            new_version = RegistrationFormFieldData(versioned_data=old_version.versioned_data, field=new_item)
            if old_version.id == old_item.current_data_id:
                new_item.current_data = new_version
            new_item.data_versions.append(new_version)
            self._field_data_map[old_version] = new_version


class RegistrationCloner(EventCloner):
    name = 'registrations'
    friendly_name = _('Registrations')
    requires = {'registration_forms'}

    @property
    def is_visible(self):
        return is_feature_enabled(self.old_event, 'registration')

    @property
    def is_available(self):
        return (RegistrationForm.query.with_parent(self.old_event)
                .filter(RegistrationForm.registrations.any(Registration.is_active))
                .has_rows())

    @property
    def is_default(self):
        return self.old_event.type_ == EventType.meeting

    def run(self, new_event, cloners, shared_data):
        form_map = shared_data['registration_forms']['form_map']
        field_data_map = shared_data['registration_forms']['field_data_map']
        for old_form, new_form in form_map.iteritems():
            self._clone_registrations(old_form, new_form, field_data_map)
        self._synchronize_registration_friendly_id(new_event)
        db.session.flush()

    def _clone_registrations(self, old_form, new_form, field_data_map):
        registration_attrs = get_simple_column_attrs(Registration) - {'uuid', 'ticket_uuid'}
        for old_registration in old_form.registrations:
            if old_registration.is_deleted:
                continue
            new_registration = Registration(user=old_registration.user, registration_form=new_form,
                                            **{attr: getattr(old_registration, attr) for attr in registration_attrs})
            reg_data_attrs = get_simple_column_attrs(RegistrationData) - {'storage_file_id', 'storage_backend', 'size'}
            for old_registration_data in old_registration.data:
                new_registration_data = RegistrationData(registration=new_registration,
                                                         **{attr: getattr(old_registration_data, attr)
                                                            for attr in reg_data_attrs})
                new_registration_data.field_data = field_data_map[old_registration_data.field_data]
                if old_registration_data.storage_file_id is not None:
                    with old_registration_data.open() as fd:
                        new_registration_data.save(fd)
            db.session.flush()
            signals.event.registration_state_updated.send(new_registration, previous_state=None)

    def _synchronize_registration_friendly_id(self, new_event):
        new_event._last_friendly_registration_id = (
            db.session
            .query(db.func.max(Registration.friendly_id))
            .filter(Registration.event_id == new_event.id)
            .scalar() or 0
        )
