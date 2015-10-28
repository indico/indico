# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.events.features.util import is_feature_enabled
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.form_fields import RegistrationFormFieldData
from indico.modules.events.registration.models.items import RegistrationFormItem, RegistrationFormSection
from indico.modules.events.registration.models.registrations import Registration, RegistrationData
from indico.util.i18n import _

from MaKaC.conference import EventCloner


class RegistrationFormCloner(EventCloner):
    def __init__(self, *args, **kwargs):
        super(RegistrationFormCloner, self).__init__(*args, **kwargs)
        self._field_data_map = {}
        self._clone_with_registrations = False

    def get_options(self):
        if not is_feature_enabled(self.event, 'registration'):
            return {}
        forms_cloner_enabled = bool(self._find_registration_forms().count())
        regs_cloner_enabled = bool(self._find_registration_forms()
                                   .filter(RegistrationForm.registrations.any(Registration.is_active))
                                   .count())
        selected = self.event.getType() == 'meeting'
        return {
            'form': (_('Registration forms'), forms_cloner_enabled, False),
            'registrations': (_('Registrations'), regs_cloner_enabled, selected)
        }

    def _find_registration_forms(self):
        return RegistrationForm.find(~RegistrationForm.is_deleted,
                                     RegistrationForm.event_id == int(self.event.id))

    def clone(self, new_event, options):
        if not options:
            return
        self._clone_with_registrations = 'registrations' in options
        attrs = get_simple_column_attrs(RegistrationForm) - {'start_dt', 'end_dt', 'modification_end_dt'}
        with db.session.no_autoflush:
            for old_form in self._find_registration_forms():
                new_form = RegistrationForm(event_new=new_event.as_event,
                                            **{attr: getattr(old_form, attr) for attr in attrs})
                self._clone_form_items(old_form, new_form)
                if self._clone_with_registrations:
                    self._clone_registrations(old_form, new_form, new_event)
                db.session.add(new_form)
                db.session.flush()

    def _clone_form_items(self, old_form, new_form):
        old_sections = RegistrationFormSection.find(RegistrationFormSection.registration_form_id == old_form.id)
        items_attrs = get_simple_column_attrs(RegistrationFormSection)
        for old_section in old_sections:
            new_section = RegistrationFormSection(registration_form=new_form, **{attr: getattr(old_section, attr)
                                                                                 for attr in items_attrs})
            for old_item in old_section.children:
                new_item = RegistrationFormItem(parent=new_section, registration_form=new_form,
                                                **{attr: getattr(old_item, attr) for attr in items_attrs})
                if new_item.is_field:
                    if self._clone_with_registrations:
                        self._clone_all_field_versions(old_item, new_item)
                    else:
                        field_data = RegistrationFormFieldData(field=new_item,
                                                               versioned_data=old_item.versioned_data)
                        new_item.current_data = field_data
                new_section.children.append(new_item)
            db.session.add(new_section)
            db.session.flush()

    def _clone_all_field_versions(self, old_item, new_item):
        for old_version in old_item.data_versions:
            new_version = RegistrationFormFieldData(versioned_data=old_version.versioned_data, field=new_item)
            if old_version.id == old_item.current_data_id:
                new_item.current_data = new_version
            new_item.data_versions.append(new_version)
            self._field_data_map[old_version] = new_version

    def _clone_registrations(self, old_form, new_form, new_event):
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
                new_registration_data.field_data = self._field_data_map[old_registration_data.field_data]
                if old_registration_data.storage_file_id is not None:
                    with old_registration_data.open() as fd:
                        new_registration_data.save(fd)
            db.session.flush()
            self._synchronize_registration_friendly_id(new_event)

    def _synchronize_registration_friendly_id(self, new_event):
        new_event.as_event._last_friendly_registration_id = (
            db.session
            .query(db.func.max(Registration.friendly_id))
            .filter(Registration.event_id == new_event.id)
            .one()[0] or 0
        )
