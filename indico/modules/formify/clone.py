# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.cloning import EventCloner, get_attrs_to_clone
from indico.modules.events.features.util import is_feature_enabled
from indico.modules.formify.models.form_fields import RegistrationFormFieldData
from indico.modules.formify.models.forms import RegistrationForm
from indico.modules.formify.models.items import RegistrationFormItem, RegistrationFormSection
from indico.util.i18n import _


class RegistrationFormCloner(EventCloner):
    name = 'registration_forms'
    friendly_name = _('Registration forms')
    requires = {'registration_tags'}

    @property
    def is_visible(self):
        return is_feature_enabled(self.old_event, 'registration')

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    def get_conflicts(self, target_event):
        if self._has_content(target_event):
            return [_('The target event already has registration forms')]

    @no_autoflush
    def run(self, new_event, cloners, shared_data, event_exists=False):
        # if the registration cloner is also enabled, we have to keep
        # all revisions since they are likely to be in use
        clone_all_revisions = 'registrations' in cloners
        attrs = get_attrs_to_clone(RegistrationForm,
                                   skip={'start_dt', 'end_dt', 'modification_end_dt', 'is_purged', 'uuid'})
        self._field_data_map = {}
        self._form_map = {}
        self._item_map = {}
        for old_form in self.old_event.registration_forms:
            new_form = RegistrationForm(**{attr: getattr(old_form, attr) for attr in attrs})
            self._clone_form_items(old_form, new_form, clone_all_revisions)
            new_event.registration_forms.append(new_form)
            signals.event.registration.after_registration_form_clone.send(old_form, new_form=new_form)
            db.session.flush()
            self._form_map[old_form] = new_form
        return {'form_map': self._form_map,
                'item_map': self._item_map,
                'field_data_map': self._field_data_map}

    def _has_content(self, event):
        return bool(event.registration_forms)

    def _clone_form_items(self, old_form, new_form, clone_all_revisions):
        old_sections = RegistrationFormSection.query.filter(RegistrationFormSection.registration_form_id == old_form.id)
        items_attrs = get_attrs_to_clone(RegistrationFormSection, skip={'is_purged'})
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
                self._item_map[old_item] = new_item
            new_form.form_items.append(new_section)
            db.session.flush()
        # link conditional fields to the new fields
        for old_item, new_item in self._item_map.items():
            if old_item.show_if_field:
                new_item.show_if_field = self._item_map[old_item.show_if_field]
        db.session.flush()

    def _clone_all_field_versions(self, old_item, new_item):
        for old_version in old_item.data_versions:
            new_version = RegistrationFormFieldData(versioned_data=old_version.versioned_data, field=new_item)
            if old_version.id == old_item.current_data_id:
                new_item.current_data = new_version
            new_item.data_versions.append(new_version)
            self._field_data_map[old_version] = new_version

    @classmethod
    @no_autoflush
    def create_from_template(cls, event, regform, title):
        """Create a regform from one in a category to the given event.

        :param event: The `Event` into which the regform will be created
        :param regform: The `RegistrationForm` to copy from
        :param title: The title of the new RegistrationForm
        :return: The newly created RegistrationForm
        """
        attrs = get_attrs_to_clone(RegistrationForm,
                                   skip={'start_dt', 'end_dt', 'modification_end_dt', 'is_purged', 'uuid', 'title',
                                         'template_id'})
        cloner = cls(None)
        cloner._field_data_map = {}
        cloner._item_map = {}
        new_form = RegistrationForm(event=event, title=title, template=regform,
                                    **{attr: getattr(regform, attr) for attr in attrs})
        cloner._clone_form_items(regform, new_form, False)
        signals.event.registration.after_registration_form_clone.send(regform, new_form=new_form)
        db.session.flush()
        return new_form
