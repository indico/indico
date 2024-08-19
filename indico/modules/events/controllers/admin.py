# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, redirect, request
from webargs import fields

from indico.core.db import db
from indico.modules.admin import RHAdminBase
from indico.modules.events.forms import (DataRetentionSettingsForm, EventKeywordsForm, EventLabelForm,
                                         ReferenceTypeForm, UnlistedEventsForm)
from indico.modules.events.management.settings import global_event_settings
from indico.modules.events.models.labels import EventLabel
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.operations import (create_event_label, create_reference_type, delete_event_label,
                                              delete_reference_type, update_event_label, update_reference_type)
from indico.modules.events.schemas import AutoLinkerRuleSchema
from indico.modules.events.settings import autolinker_settings, data_retention_settings, unlisted_events_settings
from indico.modules.events.views import WPEventAdmin
from indico.util.i18n import _
from indico.util.string import natural_sort_key
from indico.web.args import use_kwargs
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form


def _get_all_reference_types():
    return ReferenceType.query.order_by(db.func.lower(ReferenceType.name)).all()


def _render_reference_type_list():
    tpl = get_template_module('events/admin/_reference_type_list.html')
    return tpl.render_reference_type_list(_get_all_reference_types())


class RHManageReferenceTypeBase(RHAdminBase):
    """Base class for a specific reference type."""

    def _process_args(self):
        RHAdminBase._process_args(self)
        self.reference_type = ReferenceType.query.filter_by(id=request.view_args['reference_type_id']).one()


class RHReferenceTypes(RHAdminBase):
    """Manage reference types in server admin area."""

    def _process(self):
        types = _get_all_reference_types()
        return WPEventAdmin.render_template('admin/reference_types.html', 'reference_types', reference_types=types)


class RHCreateReferenceType(RHAdminBase):
    """Create a new reference type."""

    def _process(self):
        form = ReferenceTypeForm()
        if form.validate_on_submit():
            reference_type = create_reference_type(form.data)
            flash(_("External ID type '{}' created successfully").format(reference_type.name), 'success')
            return jsonify_data(html=_render_reference_type_list())
        return jsonify_form(form)


class RHEditReferenceType(RHManageReferenceTypeBase):
    """Edit an existing reference type."""

    def _process(self):
        form = ReferenceTypeForm(obj=FormDefaults(self.reference_type), reference_type=self.reference_type)
        if form.validate_on_submit():
            update_reference_type(self.reference_type, form.data)
            flash(_("External ID type '{}' successfully updated").format(self.reference_type.name), 'success')
            return jsonify_data(html=_render_reference_type_list())
        return jsonify_form(form)


class RHDeleteReferenceType(RHManageReferenceTypeBase):
    """Delete an existing reference type."""

    def _process_DELETE(self):
        delete_reference_type(self.reference_type)
        flash(_("External ID type '{}' successfully deleted").format(self.reference_type.name), 'success')
        return jsonify_data(html=_render_reference_type_list())


def _get_all_event_labels():
    return EventLabel.query.order_by(db.func.lower(EventLabel.title)).all()


def _render_event_label_list():
    tpl = get_template_module('events/admin/_event_label_list.html')
    return tpl.render_event_label_list(_get_all_event_labels())


class RHManageEventLabelBase(RHAdminBase):
    """Base class for a specific event label."""

    def _process_args(self):
        RHAdminBase._process_args(self)
        self.event_label = EventLabel.get_or_404(request.view_args['event_label_id'])


class RHEventLabels(RHAdminBase):
    """Manage event labels in server admin area."""

    def _process(self):
        labels = _get_all_event_labels()
        return WPEventAdmin.render_template('admin/event_labels.html', 'event_labels', labels=labels)


class RHCreateEventLabel(RHAdminBase):
    """Create a new event label."""

    def _process(self):
        form = EventLabelForm()
        if form.validate_on_submit():
            event_label = create_event_label(form.data)
            flash(_("Event label '{}' created successfully").format(event_label.title), 'success')
            return jsonify_data(html=_render_event_label_list())
        return jsonify_form(form)


class RHUpdateEventKeywords(RHAdminBase):
    """Update event keywords."""

    def _process(self):
        form = EventKeywordsForm(keywords=global_event_settings.get('allowed_keywords'))
        if form.validate_on_submit():
            keywords = sorted(set(form.data.get('keywords', [])), key=natural_sort_key)
            global_event_settings.set('allowed_keywords', keywords)
            flash(_('Allowed keywords have been saved'), 'success')
            return redirect(url_for('.event_keywords'))
        return WPEventAdmin.render_template('admin/event_keywords.html', 'event_keywords', form=form)


class RHEditEventLabel(RHManageEventLabelBase):
    """Edit an existing event label."""

    def _process(self):
        form = EventLabelForm(obj=FormDefaults(self.event_label), event_label=self.event_label)
        if form.validate_on_submit():
            update_event_label(self.event_label, form.data)
            flash(_("Event label '{}' successfully updated").format(self.event_label.title), 'success')
            return jsonify_data(html=_render_event_label_list())
        return jsonify_form(form)


class RHDeleteEventLabel(RHManageEventLabelBase):
    """Delete an existing event label."""

    def _process_DELETE(self):
        delete_event_label(self.event_label)
        flash(_("Event label '{}' successfully deleted").format(self.event_label.title), 'success')
        return jsonify_data(html=_render_event_label_list())


class RHUnlistedEvents(RHAdminBase):
    """Manage unlisted events in the server admin area."""

    def _process(self):
        form = UnlistedEventsForm(obj=FormDefaults(**unlisted_events_settings.get_all()))
        if form.validate_on_submit():
            unlisted_events_settings.set_multi(form.data)
            flash(_('Settings have been saved'), 'success')
            return redirect(url_for('events.unlisted_events'))
        return WPEventAdmin.render_template('admin/unlisted_events.html', 'unlisted_events', form=form)


class RHAutoLinker(RHAdminBase):
    """Manage patterns which are automatically linked in notes."""

    def _process(self):
        return WPEventAdmin.render_template('admin/autolinker.html', 'autolinker')


class RHAutoLinkerConfig(RHAdminBase):
    """Update configuration of the auto-linker."""

    @use_kwargs({
        'rules': fields.Nested(AutoLinkerRuleSchema(many=True))
    })
    def _process(self, rules):
        autolinker_settings.set('rules', rules)


class RHDataRetentionSettings(RHAdminBase):
    """Manage minimun and maximum data retention period in the admin area."""

    def _process(self):
        form = DataRetentionSettingsForm(obj=FormDefaults(**data_retention_settings.get_all()))
        if form.validate_on_submit():
            data_retention_settings.set_multi(form.data)
            flash(_('Settings have been saved'), 'success')
            return redirect(url_for('events.data_retention'))
        return WPEventAdmin.render_template('admin/data_retention.html', 'data_retention', form=form)
