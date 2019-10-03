# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import flash
from werkzeug.exceptions import NotFound

from indico.core.config import config
from indico.modules.events.abstracts.controllers.base import RHAbstractsBase, RHManageAbstractsBase
from indico.modules.events.abstracts.forms import BOASettingsForm
from indico.modules.events.abstracts.settings import boa_settings
from indico.modules.events.abstracts.util import clear_boa_cache, create_boa, create_boa_tex
from indico.modules.events.contributions import contribution_settings
from indico.util.i18n import _
from indico.web.flask.util import send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form


class RHManageBOA(RHManageAbstractsBase):
    """Configure book of abstracts"""

    def _process(self):
        form = BOASettingsForm(obj=FormDefaults(**boa_settings.get_all(self.event)))
        if form.validate_on_submit():
            boa_settings.set_multi(self.event, form.data)
            clear_boa_cache(self.event)
            flash(_('Book of Abstract settings have been saved'), 'success')
            return jsonify_data()
        return jsonify_form(form)


class RHExportBOA(RHAbstractsBase):
    """Export the book of abstracts"""

    def _check_access(self):
        RHAbstractsBase._check_access(self)
        published = contribution_settings.get(self.event, 'published')
        if not published:
            raise NotFound(_("The contributions of this event haven't been published yet"))

    def _process(self):
        if not config.LATEX_ENABLED:
            raise NotFound
        return send_file('book-of-abstracts.pdf', create_boa(self.event), 'application/pdf')


class RHExportBOATeX(RHManageAbstractsBase):
    """Export a zip file with the book of abstracts in TeX format"""

    def _process(self):
        return send_file('book-of-abstracts.zip', create_boa_tex(self.event), 'application/zip', inline=False)
