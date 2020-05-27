# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash, request

from indico.modules.events.papers.controllers.base import RHManagePapersBase, RHPapersBase
from indico.modules.events.papers.forms import PaperTemplateForm
from indico.modules.events.papers.models.templates import PaperTemplate
from indico.modules.events.papers.operations import create_paper_template, delete_paper_template, update_paper_template
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHManagePaperTemplates(RHManagePapersBase):
    """Manage the available paper templates"""

    def _process(self):
        return jsonify_template('events/papers/management/templates.html', event=self.event)


class RHManagePaperTemplateBase(RHManagePapersBase):
    """Base class to manage a specific paper template"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.template
        }
    }

    def _process_args(self):
        RHManagePapersBase._process_args(self)
        self.template = PaperTemplate.get_or_404(request.view_args['template_id'])


def _render_teplate_list(event):
    tpl = get_template_module('events/papers/management/_templates.html')
    return jsonify_data(html=tpl.render_template_list(event))


class RHUploadPaperTemplate(RHManagePapersBase):
    """Upload a new paper template"""

    def _process(self):
        form = PaperTemplateForm()
        if form.validate_on_submit():
            template = create_paper_template(self.event, form.data)
            flash(_('Paper template "{}" added.').format(template.name), 'success')
            return _render_teplate_list(self.event)
        return jsonify_form(form, form_header_kwargs={'action': request.relative_url})


class RHEditPaperTemplate(RHManagePaperTemplateBase):
    """Edit a paper template"""

    def _process(self):
        form = PaperTemplateForm(template=self.template, obj=FormDefaults(self.template, template=self.template))
        if form.validate_on_submit():
            old_name = self.template.name
            update_paper_template(self.template, form.data)
            flash(_('Paper template "{}" updated.').format(old_name), 'success')
            return _render_teplate_list(self.event)
        return jsonify_form(form, form_header_kwargs={'action': request.relative_url})


class RHDeletePaperTemplate(RHManagePaperTemplateBase):
    """Delete a paper template"""

    def _process(self):
        delete_paper_template(self.template)
        flash(_('Paper template "{}" deleted.').format(self.template.name), 'success')
        return _render_teplate_list(self.event)


class RHDownloadPaperTemplate(RHPapersBase):
    """Download a paper template"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.template
        }
    }

    def _process_args(self):
        RHPapersBase._process_args(self)
        self.template = PaperTemplate.get_or_404(request.view_args['template_id'])

    def _process(self):
        return self.template.send()
