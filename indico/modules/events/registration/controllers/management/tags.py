# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, redirect, request, session
from webargs import fields

from indico.core.db import db
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management import RHManageRegFormsBase
from indico.modules.events.registration.controllers.management.reglists import RHRegistrationsActionBase
from indico.modules.events.registration.forms import RegistrationTagForm, RegistrationTagsAssignForm
from indico.modules.events.registration.models.tags import RegistrationTag
from indico.modules.events.registration.views import WPManageRegistration
from indico.util.i18n import _
from indico.util.string import natural_sort_key
from indico.web.args import use_kwargs
from indico.web.flask.util import url_for
from indico.web.util import jsonify_data, jsonify_form


class RHManageRegistrationTagBase(RHManageRegFormsBase):
    """Base class for a specific registration tag."""

    def _process_args(self):
        RHManageRegFormsBase._process_args(self)
        self.tag = RegistrationTag.query.with_parent(self.event).filter(
            RegistrationTag.id == request.view_args['tag_id']
        ).first_or_404()


class RHManageRegistrationTags(RHManageRegFormsBase):
    """List all registration tags for an event."""

    def _process(self):
        return WPManageRegistration.render_template('management/registration_tags.html', self.event)


class RHRegistrationTagAdd(RHManageRegFormsBase):
    """Add a new registration tag."""

    def _process(self):
        form = RegistrationTagForm(event=self.event)
        if form.validate_on_submit():
            tag = RegistrationTag(event=self.event)
            form.populate_obj(tag, existing_only=True)
            db.session.flush()
            logger.info('Registration tag created by %s: %s', session.user, tag)
            flash(_('A new tag has been created.'), 'success')
            return jsonify_data(flash=False)

        return jsonify_form(form)


class RHRegistrationTagDelete(RHManageRegistrationTagBase):
    """Delete a registration tag."""

    def _process(self):
        db.session.delete(self.tag)
        logger.info('Registration tag deleted by %s: %s', session.user, self.tag)
        flash(_('Tag {} has been deleted.').format(self.tag.title), 'success')
        return redirect(url_for('.manage_registration_tags', self.event))


class RHRegistrationTagEdit(RHManageRegistrationTagBase):
    """Modify an existing registration tag."""

    def _process(self):
        form = RegistrationTagForm(obj=self.tag, event=self.event, tag=self.tag)
        if form.validate_on_submit():
            form.populate_obj(self.tag, existing_only=True)
            logger.info('Registration tag modified by %s: %s', session.user, self.tag)
            flash(_('Tag {} has been modified.').format(self.tag.title), 'success')
            return jsonify_data(flash=False)

        return jsonify_form(form)


def _assign_registration_tags(event, registrations, add, remove):
    add_ids = [int(id) for id in add]
    remove_ids = [int(id) for id in remove]
    add_tags = set(RegistrationTag.query.with_parent(event).filter(RegistrationTag.id.in_(add_ids)).all())
    remove_tags = set(RegistrationTag.query.with_parent(event).filter(RegistrationTag.id.in_(remove_ids)).all())

    for reg in registrations:
        reg.tags |= add_tags
        reg.tags -= remove_tags


class RHRegistrationTagsAssign(RHRegistrationsActionBase):
    """Assign and remove registration tags."""

    def _process(self):
        tags = sorted(self.event.registration_tags, key=lambda tag: natural_sort_key(tag.title))
        choices = [(str(tag.id), (tag.title, tag.color)) for tag in tags]

        form = RegistrationTagsAssignForm(regform=self.regform, registration_id=[reg.id for reg in self.registrations])
        form.add.choices = choices
        form.remove.choices = choices

        if form.validate_on_submit():
            _assign_registration_tags(self.event, self.registrations, form.add.data, form.remove.data)
            return jsonify_data()

        return jsonify_form(form, form_header_kwargs={'classes': 'registration-tags-assign-form'})


class RHAPIRegistrationTagsAssign(RHRegistrationsActionBase):
    """Internal API to assign and remove registration tags."""

    @use_kwargs({
        'add': fields.List(fields.Integer(), load_default=lambda: []),
        'remove': fields.List(fields.Integer(), load_default=lambda: [])
    })
    def _process_POST(self, add, remove):
        _assign_registration_tags(self.event, self.registrations, add, remove)
        return '', 204
