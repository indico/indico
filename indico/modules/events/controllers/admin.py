# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, request

from indico.core.db import db
from indico.modules.admin import RHAdminBase
from indico.modules.events.forms import EventLabelForm, ReferenceTypeForm
from indico.modules.events.models.labels import EventLabel
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.operations import (create_event_label, create_reference_type, delete_event_label,
                                              delete_reference_type, update_event_label, update_reference_type)
from indico.modules.events.views import WPEventAdmin
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
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
        self.reference_type = ReferenceType.find_one(id=request.view_args['reference_type_id'])


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
