# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
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
from indico.modules.events.registration.models.registrations import RegistrationTag
from indico.modules.events.registration.views import WPManageRegistration
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.util import jsonify_data, jsonify_template


class RHManageRegistrationTags(RHManageRegFormsBase):
    """List all registration tags for an event."""

    def _process(self):
        tags = self.event.registration_tags.all()
        return WPManageRegistration.render_template('management/registration_tags.html', self.event, tags=tags)


class RHRegistrationTagAdd(RHManageRegFormsBase):
    """Add a new registration tag."""

    def _process(self):
        form = RegistrationTagForm()
        if form.validate_on_submit():
            tag = RegistrationTag(event=self.event)
            form.populate_obj(tag, existing_only=True)
            db.session.flush()
            logger.info('Registration tag created by %s: %s', session.user, tag)
            flash(_('A new tag has been created.'), 'success')
            return jsonify_data(flash=False)

        return jsonify_template('events/registration/management/registration_tag_edit.html',
                                event=self.event, form=form, tag=None)


class RHRegistrationTagDelete(RHManageRegFormsBase):
    """Delete a registration tag."""

    def _process(self):
        tag = RegistrationTag.get_or_404(request.view_args['tag_id'])
        db.session.delete(tag)
        logger.info('Registration tag deleted by %s: %s', session.user, tag)
        flash(_('Tag {} has been deleted.').format(tag.name), 'success')
        return redirect(url_for('.manage_registration_tags', self.event))


class RHRegistrationTagEdit(RHManageRegFormsBase):
    """Modify an existing registration tag."""

    def _process(self):
        tag = RegistrationTag.get_or_404(request.view_args['tag_id'])
        form = RegistrationTagForm(obj=tag)
        if form.validate_on_submit():
            form.populate_obj(tag, existing_only=True)
            logger.info('Registration tag modified by %s: %s', session.user, tag)
            flash(_('Tag {} has been modified.').format(tag.name), 'success')
            return jsonify_data(flash=False)

        return jsonify_template('events/registration/management/registration_tag_edit.html',
                                event=self.event, form=form, tag=tag)


class RHRegistrationTagsAssign(RHRegistrationsActionBase):
    """Assign/Remove registration tags to/from registrations."""

    def _process(self):
        tags = RegistrationTag.query.with_parent(self.event).all()
        choices = [(str(tag.id), tag.name) for tag in tags]

        registration_ids = request.form.getlist('registration_id')
        form = RegistrationTagsAssignForm(regform=self.regform, registration_id=registration_ids)
        form.add.choices = choices
        form.remove.choices = choices

        if form.validate_on_submit():
            add = [int(id) for id in form.add.data]
            remove = [int(id) for id in form.remove.data]

            for reg in self.registrations:
                for id in add:
                    tag = RegistrationTag.get(id)
                    if tag not in reg.registration_tags:
                        reg.registration_tags.append(RegistrationTag.get(id))
                for id in remove:
                    tag = RegistrationTag.get(id)
                    if tag in reg.registration_tags:
                        reg.registration_tags.remove(RegistrationTag.get(id))

            return jsonify_data()

        return jsonify_template('events/registration/management/registration_tag_assign.html',
                                event=self.event, form=form, regform=self.regform)
