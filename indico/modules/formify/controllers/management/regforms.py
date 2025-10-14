# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import timedelta

from flask import flash, redirect, request, session
from sqlalchemy.orm import undefer

from indico.core import signals
from indico.core.db import db
from indico.modules.categories.models.categories import Category
from indico.modules.categories.views import WPCategoryManageRegistrationForm
from indico.modules.events.models.events import Event, EventType
from indico.modules.events.payment import payment_settings
from indico.modules.events.registration.models.registrations import PublishRegistrationsMode
from indico.modules.events.registration.util import create_personal_data_fields, get_flat_section_setup_data
from indico.modules.events.registration.views import WPEventManageRegistrationForm
from indico.modules.events.settings import data_retention_settings
from indico.modules.formify import logger
from indico.modules.formify.forms import RegistrationFormCreateForm, RegistrationFormEditForm
from indico.modules.formify.models.forms import RegistrationForm
from indico.modules.formify.operations import update_registration_form_settings
from indico.modules.logs.models.entries import CategoryLogRealm, EventLogRealm, LogKind
from indico.modules.users.models.affiliations import Affiliation
from indico.util.date_time import format_human_timedelta
from indico.util.i18n import _, force_locale, orig_string
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults


class ManageRegistrationFormsAreaMixin:
    """Basic class for all registration form mixins.

    It resolves the target object type from the blueprint URL.
    """

    @property
    def object_type(self):
        """Figure out whether we're targetting an event or category, based on URL info."""
        return request.view_args['object_type']

    @property
    def target_dict(self):
        return {'event': self.target} if self.object_type == 'event' else {'category': self.target}

    @property
    def target(self):
        event_id = request.view_args.get('event_id')
        categ_id = request.view_args.get('category_id')
        return Event.get_or_404(event_id) if self.object_type == 'event' else Category.get_or_404(categ_id)


class ManageRegistrationFormsMixin(ManageRegistrationFormsAreaMixin):
    """List all registration forms for a taget event or category."""

    view_class = None

    def _process(self):
        regforms = (RegistrationForm.query
                    .with_parent(self.target)
                    .options(undefer('active_registration_count'))
                    .order_by(db.func.lower(RegistrationForm.title)).all())
        return self.view_class.render_template('management/regform_list.html', self.target,
                                                'registration', target=self.target, regforms=regforms)


class RegistrationFormCreateMixin(ManageRegistrationFormsAreaMixin):
    def _get_form_defaults(self):
        participant_visibility = (PublishRegistrationsMode.hide_all
                                  if isinstance(self.target, Event) and self.event.type_ == EventType.conference
                                  else PublishRegistrationsMode.show_all)
        public_visibility = PublishRegistrationsMode.hide_all
        return FormDefaults(visibility=[participant_visibility.name, public_visibility.name, None])

    def _process(self):
        form = RegistrationFormCreateForm(obj=self._get_form_defaults())
        if form.validate_on_submit():
            regform = RegistrationForm(currency=payment_settings.get('currency'), **self.target_dict)
            create_personal_data_fields(regform)
            form.populate_obj(regform, skip=['visibility'])
            participant_visibility, public_visibility, visibility_duration = form.visibility.data
            regform.publish_registrations_participants = PublishRegistrationsMode[participant_visibility]
            regform.publish_registrations_public = PublishRegistrationsMode[public_visibility]
            regform.publish_registrations_duration = (timedelta(weeks=visibility_duration)
                                                      if visibility_duration is not None else None)
            db.session.add(regform)
            db.session.flush()
            signals.event.registration_form_created.send(regform)
            flash(_('Registration form has been successfully created'), 'success')
            regform.log(EventLogRealm.management if self.object_type == 'event' else CategoryLogRealm.management,
                        LogKind.positive, 'Registration',
                        f'Registration form "{regform.title}" has been created', session.user,
                        data=_get_regform_creation_log_data(regform))
            return redirect(url_for('.manage_regform', regform))
        if self.object_type == 'event':
            return WPEventManageRegistrationForm.render_template('management/regform_create.html', self.event,
                                                             form=form, target=self.target, regform=None)
        else:
            return WPCategoryManageRegistrationForm.render_template('management/regform_create.html', self.category,
                                                                'registration', form=form, target=self.target,
                                                                regform=None)


def _get_regform_creation_log_data(regform):
    with force_locale(None, default=False):
        return {
            'Visibility to participants': orig_string(regform.publish_registrations_participants.title),
            'Visibility to everyone': orig_string(regform.publish_registrations_public.title),
            'Visibility duration': (format_human_timedelta(regform.publish_registrations_duration)
                                    if regform.publish_registrations_duration else 'Indefinite'),
            'Retention period': (format_human_timedelta(regform.retention_period)
                                 if regform.retention_period else 'Indefinite'),
        }


class RegistrationFormEditMixin(ManageRegistrationFormsAreaMixin):
    """Mixin to edit a registration form."""

    def _get_form_defaults(self):
        return FormDefaults(self.regform, limit_registrations=self.regform.registration_limit is not None)

    def _process(self):
        form = RegistrationFormEditForm(obj=self._get_form_defaults(), target=self.target, regform=self.regform)
        if form.validate_on_submit():
            update_registration_form_settings(self.regform, form.data, skip={'limit_registrations'})
            flash(_('Registration form has been successfully modified'), 'success')
            return redirect(url_for('.manage_regform', self.regform))
        view_class = (WPCategoryManageRegistrationForm if self.object_type == 'category'
                      else WPEventManageRegistrationForm)
        return view_class.render_template('management/regform_edit.html', self.target, form=form,
                                          regform=self.regform)


class RegistrationFormDeleteMixin(ManageRegistrationFormsAreaMixin):
    """Mixin to delete a registration form."""

    def _process(self):
        rels = ('in_attachment_acls', 'in_attachment_folder_acls', 'in_contribution_acls', 'in_event_acls',
                'in_session_acls')
        for rel in rels:
            getattr(self.regform, rel).delete()
        self.regform.is_deleted = True
        signals.event.registration_form_deleted.send(self.regform)
        flash(_('Registration form deleted'), 'success')
        logger.info('Registration form %s deleted by %s', self.regform, session.user)
        self.regform.log(EventLogRealm.management if self.object_type == 'event' else CategoryLogRealm.management,
                         LogKind.negative, 'Registration',
                         f'Registration form "{self.regform.title}" was deleted', session.user)
        return redirect(url_for('.manage_regform_list', self.target))


class RegistrationFormModifyMixin(ManageRegistrationFormsAreaMixin):
    """Mixin to modify the form of a registration form."""

    def _process(self):
        min_data_retention = data_retention_settings.get('minimum_data_retention')
        max_data_retention = data_retention_settings.get('maximum_data_retention') or timedelta(days=3650)
        regform_retention_weeks = self.regform.retention_period.days // 7 if self.regform.retention_period else None
        view_class = (WPCategoryManageRegistrationForm if self.object_type == 'category'
                      else WPEventManageRegistrationForm)
        return view_class.render_template('management/regform_modify.html', self.target,
                                          target_locator=self.target.locator,
                                          form_data=get_flat_section_setup_data(self.regform),
                                          regform=self.regform,
                                          data_retention_range={'min': min_data_retention.days // 7,
                                                                'max': max_data_retention.days // 7,
                                                                'regform': regform_retention_weeks},
                                          has_predefined_affiliations=Affiliation.query.has_rows())
