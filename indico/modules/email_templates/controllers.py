# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from copy import deepcopy

from flask import flash, request, session
from markupsafe import Markup
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.db import db
from indico.modules.categories import Category
from indico.modules.categories.controllers.base import RHManageCategoryBase
from indico.modules.designer.forms import CloneTemplateForm
from indico.modules.email_templates.forms import CreateEmailTemplatesForm, EditEmailTemplatesForm
from indico.modules.email_templates.models.email_templates import EmailTemplate
from indico.modules.email_templates.util import get_inherited_templates
from indico.modules.email_templates.views import WPCategoryManagementEmailTemplate, WPEventManagementEmailTemplate
from indico.modules.events import Event
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.util import check_event_locked
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.rh import RHProtected
from indico.web.util import jsonify_data, jsonify_form


def _render_template_list(target, event=None):
    tpl = get_template_module('email_templates/_list.html')
    return tpl.render_email_template_list(target.email_templates, target, event=event,
                                          inherited_templates=get_inherited_templates(target))


class EmailTemplateMixin:
    """Basic class for all template designer mixins.

    It resolves the target object type from the blueprint URL.
    """

    @property
    def object_type(self):
        """Figure out whether we're targeting an event or category, based on URL info."""
        return request.view_args['object_type']

    @property
    def event_or_none(self):
        return self.target if self.object_type == 'event' else None

    def _render_template(self, tpl_name, **kwargs):
        view_class = (WPEventManagementEmailTemplate
                      if self.object_type == 'event' else WPCategoryManagementEmailTemplate)
        return view_class.render_template(tpl_name, self.target, 'email_templates',
                                          target=self.target, **kwargs)


class SpecificEmailTemplateMixin(EmailTemplateMixin):
    """Mixin that accepts a target template passed in the URL.

    The target category/event will be the owner of that template.
    """

    normalize_url_spec = {
        'locators': {
            lambda self: self.email_tpl
        }
    }

    @property
    def target(self):
        return self.email_tpl.owner

    def _check_access(self):
        self._require_user()
        if not self.target.can_manage(session.user):
            raise Forbidden
        elif isinstance(self.target, Event):
            check_event_locked(self, self.target)

    def _process_args(self):
        self.email_tpl = EmailTemplate.get_or_404(request.view_args['email_template_id'])
        if self.target.is_deleted:
            raise NotFound


class TargetFromURLMixin(EmailTemplateMixin):
    """Mixin that takes the target event/category from the URL that is passed."""

    @property
    def target_dict(self):
        return {'event': self.event} if self.object_type == 'event' else {'category': self.category}

    @property
    def target(self):
        return self.event if self.object_type == 'event' else self.category


class EmailTemplateListMixin(TargetFromURLMixin):
    def _process(self):
        inherited_templates = get_inherited_templates(self.target)
        return self._render_template('list.html', inherited_templates=inherited_templates)


class AddEmailTemplateMixin(TargetFromURLMixin):
    def _check_access(self):
        if not self.target.can_manage(session.user):
            raise Forbidden

    def _process(self):
        form = CreateEmailTemplatesForm(target=self.target)
        if form.validate_on_submit():
            new_email_tpl = EmailTemplate(**self.target_dict)
            new_email_tpl.rules = {'status': form.status.data}
            form.populate_obj(new_email_tpl)
            flash(_("Added a new email template '{}'").format(new_email_tpl.title), 'success')
            return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))
        return jsonify_form(form, disabled_until_change=False)


class RHListEventEmailTemplates(EmailTemplateListMixin, RHManageEventBase):
    pass


class RHListCategoryEmailTemplates(EmailTemplateListMixin, RHManageCategoryBase):
    pass


class RHAddEventEmailTemplate(AddEmailTemplateMixin, RHManageEventBase):
    pass


class RHAddCategoryEmailTemplate(AddEmailTemplateMixin, RHManageCategoryBase):
    pass


class RHModifyEmailTemplateBase(SpecificEmailTemplateMixin, RHProtected):
    def _check_access(self):
        RHProtected._check_access(self)
        SpecificEmailTemplateMixin._check_access(self)


class RHEditEmailTemplate(RHModifyEmailTemplateBase):
    def _process(self):
        form = EditEmailTemplatesForm(target=self.target, obj=self.email_tpl)
        if form.validate_on_submit():
            self.email_tpl.rules = {'status': form.status.data}
            form.populate_obj(self.email_tpl)
            flash(_("Edited email template '{}'").format(self.email_tpl.title), 'success')
            return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))
        return jsonify_form(form, disabled_until_change=False)


class RHDeleteEmailTemplate(RHModifyEmailTemplateBase):
    def _process(self):
        db.session.delete(self.email_tpl)
        db.session.flush()
        flash(_('The email template has been deleted'), 'success')
        return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))


class CloneTemplateMixin(TargetFromURLMixin):
    cloneable_elsewhere = False

    def _check_access(self):
        if not self.target.can_manage(session.user):
            raise Forbidden
        elif isinstance(self.target, Event):
            check_event_locked(self, self.target)

    def _process_args(self):
        self.email_tpl = EmailTemplate.get_or_404(request.view_args['email_template_id'])
        if self.target.is_deleted:
            raise NotFound

    def is_active(self):
        email_templates = [email_tpl for email_tpl in self.target.email_templates
                           if email_tpl.type == self.email_tpl.type]
        if status := self.email_tpl.rules.get('status'):
            email_templates = [email_tpl for email_tpl in email_templates
                               if email_tpl.rules and email_tpl.rules.get('status') == status]
        if email_templates:
            return not any(tpl.is_active for tpl in email_templates)
        return self.email_tpl.is_active

    def clone_template(self, target=None):
        title = f'{self.email_tpl.title} (copy)'
        target_dict = target or self.target_dict
        new_email_tpl = EmailTemplate(title=title, type=self.email_tpl.type, **target_dict)
        new_email_tpl.subject = self.email_tpl.subject
        new_email_tpl.body = self.email_tpl.body
        new_email_tpl.is_system_template = self.email_tpl.is_system_template
        new_email_tpl.is_active = self.is_active()
        new_email_tpl.rules = deepcopy(self.email_tpl.rules)
        message = _("Created copy of template '{}'").format(self.email_tpl.title)
        if target_dict != self.target_dict:
            message += Markup(' (<a href="{}">{}</a>)').format(url_for('email_templates.email_template_list',
                                                                       target_dict['category']), _('Go to category'))
        flash(message, 'success')
        return jsonify_data(html=_render_template_list(self.target, event=self.event_or_none))

    def _process(self):
        if self.cloneable_elsewhere:
            category = (self.target if isinstance(self.target, Category) and
                                       self.target.can_manage(session.user) else None)
            form = CloneTemplateForm(category=category)
            if form.validate_on_submit():
                return self.clone_template(target=form.data)
            return jsonify_form(form, submit=_('Clone'), disabled_until_change=False)
        if request.method == 'POST':
            return self.clone_template()


class RHCloneEventEmailTemplate(CloneTemplateMixin, RHManageEventBase):
    def _process_args(self):
        RHManageEventBase._process_args(self)
        CloneTemplateMixin._process_args(self)


class RHCloneCategoryEmailTemplate(CloneTemplateMixin, RHManageCategoryBase):
    cloneable_elsewhere = True

    def _process_args(self):
        RHManageCategoryBase._process_args(self)
        CloneTemplateMixin._process_args(self)
