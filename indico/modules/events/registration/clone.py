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
from indico.util.i18n import _

from MaKaC.conference import EventCloner


class RegistrationFormCloner(EventCloner):
    def get_options(self):
        if not is_feature_enabled(self.event, 'registration'):
            return {}
        enabled = bool(self._find_registration_forms().count())
        return {'form': (_('Registration forms'), enabled, False)}

    def clone(self, new_event, options):
        if 'form' not in options:
            return
        attrs = get_simple_column_attrs(RegistrationForm) - {'start_dt', 'end_dt'}
        for old_form in self._find_registration_forms():
            new_form = RegistrationForm(event_id=new_event.id, **{attr: getattr(old_form, attr) for attr in attrs})
            self._clone_form_items(old_form, new_form)
            db.session.add(new_form)
            db.session.flush()

    def _find_registration_forms(self):
        return RegistrationForm.find(~RegistrationForm.is_deleted,
                                     RegistrationForm.event_id == int(self.event.id))

    def _clone_form_items(self, old_form, new_form):
        old_sections = RegistrationFormSection.find(RegistrationFormSection.registration_form_id == old_form.id,
                                                    ~RegistrationFormSection.is_deleted)
        section_attrs = get_simple_column_attrs(RegistrationFormSection) - {'registration_form_id'}
        for old_section in old_sections:
            new_section = RegistrationFormSection(registration_form=new_form, **{attr: getattr(old_section, attr)
                                                                                 for attr in section_attrs})
            old_section_items = RegistrationFormItem.find(~RegistrationFormItem.is_deleted, parent=old_section)
            items_attrs = get_simple_column_attrs(RegistrationFormItem) | {'parent_id'}
            for old_item in old_section_items:
                new_item = RegistrationFormItem(parent=new_section, registration_form=new_form,
                                                **{attr: getattr(old_item, attr) for attr in items_attrs})
                field_data = RegistrationFormFieldData(field=new_item,
                                                       versioned_data=getattr(old_item, 'versioned_data'))
                new_item.current_data = field_data
                new_section.children.append(new_item)
            db.session.add(new_section)
            db.session.flush()
