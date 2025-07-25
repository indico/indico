# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core import signals
from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.cloning import EventCloner, get_attrs_to_clone
from indico.modules.events.features.util import is_feature_enabled
from indico.modules.events.models.events import EventType
from indico.modules.events.registration.models.form_fields import RegistrationFormFieldData
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.items import RegistrationFormItem, RegistrationFormSection
from indico.modules.events.registration.models.registrations import Registration, RegistrationData
from indico.modules.events.registration.models.tags import RegistrationTag
from indico.util.i18n import _


class RegistrationTagCloner(EventCloner):
    name = 'registration_tags'
    friendly_name = _('Registration tags')
    is_internal = True

    # We do not override `is_available` as we have cloners depending
    # on this internal cloner even if it won't clone anything.

    def get_conflicts(self, target_event):
        if target_event.registration_tags:
            return [_('The target event already has registration tags')]

    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._tag_map = {}
        self._clone_tags(new_event)
        db.session.flush()
        return {'tag_map': self._tag_map}

    def _clone_tags(self, new_event):
        attrs = get_attrs_to_clone(RegistrationTag)
        for old_tag in self.old_event.registration_tags:
            tag = RegistrationTag(event=new_event)
            tag.populate_from_attrs(old_tag, attrs)
            self._tag_map[old_tag] = tag


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


class RegistrationCloner(EventCloner):
    name = 'registrations'
    friendly_name = _('Registrations')
    requires = {'registration_forms', 'registration_tags'}
    uses = {'sessions'}

    @property
    def is_visible(self):
        return is_feature_enabled(self.old_event, 'registration')

    @property
    def is_available(self):
        return self._has_content(self.old_event)

    @property
    def is_default(self):
        return self.old_event.type_ == EventType.meeting

    def get_conflicts(self, target_event):
        if self._has_content(target_event):
            return [_('The target event already has registrations')]

    def run(self, new_event, cloners, shared_data, event_exists=False):
        if event_exists:
            self._delete_orphaned_registrations(new_event)
        form_map = shared_data['registration_forms']['form_map']
        field_data_map = shared_data['registration_forms']['field_data_map']
        block_map = shared_data['sessions']['session_block_map'] if 'sessions' in shared_data else None
        tag_map = shared_data['registration_tags']['tag_map']
        for old_form, new_form in form_map.items():
            self._clone_registrations(old_form, new_form, field_data_map, block_map, tag_map)
        self._synchronize_registration_friendly_id(new_event)
        db.session.flush()

    def _has_content(self, event):
        return (RegistrationForm.query.with_parent(event)
                .filter(RegistrationForm.registrations.any(Registration.is_active))
                .has_rows())

    def _clone_registrations(self, old_form, new_form, field_data_map, session_blocks_map, tag_map):
        registration_attrs = get_attrs_to_clone(Registration, skip={
            'uuid',
            'ticket_uuid',
            'checked_in',
            'checked_in_dt',
        })
        for old_registration in old_form.registrations:
            if old_registration.is_deleted:
                continue
            new_registration = Registration(user=old_registration.user, registration_form=new_form,
                                            **{attr: getattr(old_registration, attr) for attr in registration_attrs})
            new_registration.tags = {tag_map[tag] for tag in old_registration.tags}
            reg_data_attrs = get_attrs_to_clone(RegistrationData, skip={'storage_file_id', 'storage_backend', 'size'})
            for old_registration_data in old_registration.data:
                new_registration_data = RegistrationData(registration=new_registration,
                                                         **{attr: getattr(old_registration_data, attr)
                                                            for attr in reg_data_attrs})
                new_registration_data.field_data = field_data_map[old_registration_data.field_data]
                if old_registration_data.storage_file_id is not None:
                    with old_registration_data.open() as fd:
                        new_registration_data.save(fd)
                # Assigns the mapped session blocks for cloned event to the cloned registration.
                if new_registration_data.field_data.field.input_type == 'sessions':
                    if not session_blocks_map:
                        # If timetable/sessions are not cloned, we cannot preserve data in this field as
                        # it would reference Ids from the old event
                        new_registration_data.data = []
                    else:
                        new_registration_data.data = [
                            new_block_id
                            for old_block_id in new_registration_data.data
                            if (
                                new_block_id := next(
                                    (
                                        session_blocks_map[block].id
                                        for block in session_blocks_map
                                        if block.id == old_block_id
                                    ),
                                    None,
                                )
                            )
                        ]
            db.session.flush()
            signals.event.registration_state_updated.send(new_registration, previous_state=None)

    def _synchronize_registration_friendly_id(self, new_event):
        new_event._last_friendly_registration_id = (
            db.session
            .query(db.func.max(Registration.friendly_id))
            .filter(Registration.event_id == new_event.id)
            .scalar() or 0
        )

    def _delete_orphaned_registrations(self, event):
        # Avoid friendly ID conflicts with registrations in deleted regforms
        Registration.query.with_parent(event).filter(
            Registration.registration_form.has(is_deleted=True)
        ).update({Registration.is_deleted: True}, synchronize_session='fetch')
