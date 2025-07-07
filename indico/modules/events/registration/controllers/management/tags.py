# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, redirect, request, session

from indico.core.db import db
from indico.modules.events.registration import logger
from indico.modules.events.registration.controllers.management import RHManageRegFormsBase
from indico.modules.events.registration.controllers.management.reglists import RHRegistrationsActionBase
from indico.modules.events.registration.forms import RegistrationTagForm, RegistrationTagsAssignForm
from indico.modules.events.registration.models.tags import RegistrationTag
from indico.modules.events.registration.views import WPManageRegistration
from indico.util.i18n import _
from indico.util.marshmallow import ModelList
from indico.web.args import use_rh_kwargs
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


def _assign_registration_tags(registrations, add, remove):
    for reg in registrations:
        reg.tags |= add
        reg.tags -= remove


class RHRegistrationTagsAssign(RHRegistrationsActionBase):
    """Assign and remove registration tags."""

    def _process(self):
        form = RegistrationTagsAssignForm(event=self.event, registration_id=[reg.id for reg in self.registrations])

        if form.validate_on_submit():
            _assign_registration_tags(self.registrations, form.add.data, form.remove.data)
            return jsonify_data()

        return jsonify_form(form, form_header_kwargs={'classes': 'registration-tags-assign-form'})


class RHAPIRegistrationTagsAssign(RHRegistrationsActionBase):
    """Internal API to assign and remove registration tags."""

    @use_rh_kwargs({
        'add': ModelList(RegistrationTag,
                         get_query=lambda m, ctx: m.query.with_parent(ctx['event']),
                         collection_class=set,
                         load_default=lambda: set()),
        'remove': ModelList(RegistrationTag,
                            get_query=lambda m, ctx: m.query.with_parent(ctx['event']),
                            collection_class=set,
                            load_default=lambda: set())
    }, rh_context=('event',))
    def _process_POST(self, add, remove):
        _assign_registration_tags(self.registrations, add, remove)
        return '', 204
