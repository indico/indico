# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from werkzeug.exceptions import BadRequest

from indico.core.db import db
from indico.modules.events.abstracts.controllers.base import RHManageAbstractsBase
from indico.modules.events.abstracts.forms import (CreateEmailTemplateForm, EditEmailTemplateRuleForm,
                                                   EditEmailTemplateTextForm)
from indico.modules.events.abstracts.models.abstracts import AbstractState
from indico.modules.events.abstracts.models.email_templates import AbstractEmailTemplate
from indico.modules.events.abstracts.notifications import get_abstract_notification_tpl_module
from indico.modules.events.abstracts.util import build_default_email_template, create_mock_abstract
from indico.web.flask.templating import get_template_module
from indico.web.util import jsonify_data, jsonify_template


class RHEmailTemplateList(RHManageAbstractsBase):
    """Display list of e-mail templates."""

    def _process(self):
        return jsonify_template('events/abstracts/management/notification_tpl_list.html', event=self.event,
                                **_get_rules_fields(self.event))


class RHAddEmailTemplate(RHManageAbstractsBase):
    """Add a new e-mail template."""

    def _process(self):
        form = CreateEmailTemplateForm(event=self.event)
        if form.validate_on_submit():
            new_tpl = build_default_email_template(self.event, form.default_tpl.data)
            form.populate_obj(new_tpl)
            self.event.abstract_email_templates.append(new_tpl)
            db.session.flush()
            return _render_notification_list(self.event)
        return jsonify_template('events/abstracts/management/notification_tpl_form.html', form=form)


class RHSortEmailTemplates(RHManageAbstractsBase):
    """Sort e-mail templates according to the order provided by the client."""

    def _process(self):
        sort_order = request.json['sort_order']
        tpls = {s.id: s for s in self.event.abstract_email_templates}
        for position, tpl_id in enumerate(sort_order, 1):
            if tpl_id in tpls:
                tpls[tpl_id].position = position


class RHEditEmailTemplateBase(RHManageAbstractsBase):
    """Base class for operations that involve editing an e-mail template."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.email_tpl
        }
    }

    def _process_args(self):
        RHManageAbstractsBase._process_args(self)
        self.email_tpl = AbstractEmailTemplate.get_one(request.view_args['email_tpl_id'])


class RHEditEmailTemplateRules(RHEditEmailTemplateBase):
    """Edit the rules of a notification template."""

    def _process(self):
        form = EditEmailTemplateRuleForm(obj=self.email_tpl, event=self.event)
        if form.validate_on_submit():
            form.populate_obj(self.email_tpl)
            return _render_notification_list(self.event)
        return jsonify_template('events/abstracts/management/notification_tpl_form.html', form=form, is_edit=True)


class RHEditEmailTemplateText(RHEditEmailTemplateBase):
    """Edit the e-mail text of a notification template."""

    def _process(self):
        form = EditEmailTemplateTextForm(obj=self.email_tpl, event=self.event)
        if form.validate_on_submit():
            form.populate_obj(self.email_tpl)
            return _render_notification_list(self.event)
        return jsonify_template('events/abstracts/management/notification_tpl_text_form.html', form=form, is_edit=True)


class RHDeleteEmailTemplate(RHEditEmailTemplateBase):
    """Delete an e-mail template."""

    def _process(self):
        db.session.delete(self.email_tpl)
        return _render_notification_list(self.event, flash=False)


class RHEmailTemplateREST(RHEditEmailTemplateBase):
    """Perform RESTful actions on an email template."""

    def _process_PATCH(self):
        if request.json is None:
            raise BadRequest('Expected JSON payload')

        invalid_fields = request.json.viewkeys() - {'stop_on_match'}
        if invalid_fields:
            raise BadRequest("Invalid fields: {}".format(', '.join(invalid_fields)))

        if 'stop_on_match' in request.json:
            self.email_tpl.stop_on_match = request.json['stop_on_match']

        return jsonify_data(flash=False)


def _get_rules_fields(event):
    abstract = create_mock_abstract(event)
    email_tpl_dict = {et.id: get_abstract_notification_tpl_module(et, abstract)
                      for et in event.abstract_email_templates}
    return {'tracks': {track.id: track for track in event.tracks},
            'states': AbstractState.__titles__, 'contrib_types': {ct.id: ct for ct in event.contribution_types},
            'email_tpls': email_tpl_dict}


def _render_notification_list(event, flash=True):
    tpl = get_template_module('events/abstracts/management/_notification_tpl_list.html')
    return jsonify_data(html=tpl.render_notification_list(event, **_get_rules_fields(event)), flash=flash)
