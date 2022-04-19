# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import uuid

from flask import request
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.cache import make_scoped_cache
from indico.modules.categories.models.categories import Category
from indico.modules.designer.models.templates import DesignerTemplate
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.management.forms import PosterPrintingForm
from indico.modules.events.posters import PosterPDF
from indico.util.i18n import _
from indico.web.flask.util import send_file, url_for
from indico.web.util import jsonify_data, jsonify_form


poster_cache = make_scoped_cache('poster-printing')


class RHPosterPrintSettings(RHManageEventBase):
    ALLOW_LOCKED = True

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.template_id = request.args.get('template_id')

    def _process(self):
        self.commit = False
        form = PosterPrintingForm(self.event, template=self.template_id)
        if form.validate_on_submit():
            data = dict(form.data)
            template_id = data.pop('template')
            key = str(uuid.uuid4())
            poster_cache.set(key, data, timeout=1800)
            download_url = url_for('.print_poster', self.event, template_id=template_id, uuid=key)
            return jsonify_data(flash=False, redirect=download_url, redirect_no_loading=True)
        return jsonify_form(form, disabled_until_change=False, back=_('Cancel'), submit=_('Download PDF'))


class RHPrintEventPoster(RHManageEventBase):
    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.template = DesignerTemplate.get_or_404(request.view_args['template_id'])

    def _check_access(self):
        RHManageEventBase._check_access(self)

        # Check that template belongs to this event or a category that is a parent
        if self.template.owner == self.event:
            return
        valid_category_ids = self.event.category_chain or [Category.get_root().id]
        if self.template.owner.id not in valid_category_ids:
            raise Forbidden

    def _process(self):
        self.commit = False
        config_params = poster_cache.get(request.view_args['uuid'])
        if not config_params:
            raise NotFound

        pdf = PosterPDF(self.template, config_params, self.event)
        return send_file(f'Poster-{self.event.id}.pdf', pdf.get_pdf(), 'application/pdf')
