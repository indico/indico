# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import request

from indico.core.db import db
from indico.modules.events.abstracts.controllers.management import RHManageAbstractsBase
from indico.modules.events.abstracts.forms import (EditEmailTemplateRuleForm, EditEmailTemplateTextForm,
                                                   CreateEmailTemplateForm)
from indico.modules.events.abstracts.models.email_templates import AbstractEmailTemplate
from indico.modules.events.abstracts.util import build_default_email_template, create_mock_abstract
from indico.util.placeholders import replace_placeholders
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data, jsonify_template


class RHEmailTemplateList(RHManageAbstractsBase):
    """Display list of e-mail templates."""

    def _process(self):
        return jsonify_template('events/abstracts/management/notification_tpl_list.html', event=self.event_new)


class RHEmailTemplateAdd(RHManageAbstractsBase):
    """Add a new e-mail template."""

    def _process(self):
        form = CreateEmailTemplateForm(event=self.event_new)
        if form.validate_on_submit():
            new_tpl = build_default_email_template(self.event_new, form.default_tpl.data)
            form.populate_obj(new_tpl)
            self.event_new.abstract_email_templates.append(new_tpl)
            db.session.flush()

            tpl = get_template_module('events/abstracts/management/_notification_tpl_list.html')
            return jsonify_data(html=tpl.render_notification_list(self.event_new))
        return jsonify_template('events/abstracts/management/notification_tpl_form.html', form=form)


class RHEMailTemplateModifBase(RHManageAbstractsBase):
    """Base RH for a specific subcontribution"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.email_tpl
        }
    }

    def _checkParams(self, params):
        RHManageAbstractsBase._checkParams(self, params)
        self.email_tpl = AbstractEmailTemplate.get_one(request.view_args['email_tpl_id'])


class RHEmailTemplateRuleEdit(RHEMailTemplateModifBase):
    """Add a new e-mail template."""

    def _process(self):
        form = EditEmailTemplateRuleForm(obj=self.email_tpl, event=self.event_new)
        if form.validate_on_submit():
            form.populate_obj(self.email_tpl)
            tpl = get_template_module('events/abstracts/management/_notification_tpl_list.html')
            return jsonify_data(html=tpl.render_notification_list(self.event_new))
        return jsonify_template('events/abstracts/management/notification_tpl_form.html',
                                form=form, is_edit=True)


class RHEmailTemplateTextEdit(RHEMailTemplateModifBase):
    """Add a new e-mail template."""

    def _process(self):
        form = EditEmailTemplateTextForm(obj=self.email_tpl, event=self.event_new)
        if form.validate_on_submit():
            form.populate_obj(self.email_tpl)
            tpl = get_template_module('events/abstracts/management/_notification_tpl_list.html')
            return jsonify_data(html=tpl.render_notification_list(self.event_new))
        return jsonify_template('events/abstracts/management/notification_tpl_text_form.html', form=form, is_edit=True)


class RHEmailTemplateDelete(RHEMailTemplateModifBase):
    """Delete an e-mail template."""

    def _process(self):
        db.session.delete(self.email_tpl)
        tpl = get_template_module('events/abstracts/management/_notification_tpl_list.html')
        return jsonify_data(html=tpl.render_notification_list(self.event_new), flash=False)


class RHEmailTemplatePreview(RHEMailTemplateModifBase):
    """Delete an e-mail template."""

    def _process(self):
        abstract = create_mock_abstract(self.event_new)
        body = replace_placeholders('abstract-notification-email', self.email_tpl.body,
                                    abstract=abstract, escape_html=False)
        self.commit = False
        return jsonify_template('events/abstracts/management/notification_preview.html', body=body)
