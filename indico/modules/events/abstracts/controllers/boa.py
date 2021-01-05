# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import os

from flask import flash, request, session
from werkzeug.exceptions import NotFound

from indico.core.config import config
from indico.modules.events.abstracts.controllers.base import RHAbstractsBase, RHManageAbstractsBase
from indico.modules.events.abstracts.forms import BOASettingsForm
from indico.modules.events.abstracts.settings import boa_settings
from indico.modules.events.abstracts.util import clear_boa_cache, create_boa, create_boa_tex
from indico.modules.events.contributions import contribution_settings
from indico.modules.events.logs.models.entries import EventLogKind, EventLogRealm
from indico.modules.files.controllers import UploadFileMixin
from indico.util.i18n import _
from indico.util.marshmallow import FileField, file_extension
from indico.web.args import use_kwargs
from indico.web.flask.util import send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form


class RHBOASettings(RHManageAbstractsBase):
    """Configure book of abstracts."""

    def _process(self):
        form = BOASettingsForm(obj=FormDefaults(**boa_settings.get_all(self.event)))
        if form.validate_on_submit():
            boa_settings.set_multi(self.event, form.data)
            clear_boa_cache(self.event)
            flash(_('Book of Abstract settings have been saved'), 'success')
            return jsonify_data()
        if self.event.has_custom_boa:
            if config.LATEX_ENABLED:
                message = _('You are currently using a custom Book of Abstracts. Please note that any change '
                            'in the settings below will only affect the LaTeX files and not the custom PDF. '
                            'You need to rebuild the Book of Abstracts and upload the new version yourself.')
            else:
                message = _('Please note that any change in the settings below will only affect the LaTeX files '
                            'and not the Book of Abstracts itself. You need to rebuild it and upload the new '
                            'version yourself.')
            return jsonify_form(form, message=message)
        return jsonify_form(form)


class RHUploadBOAFile(UploadFileMixin, RHManageAbstractsBase):
    def get_file_context(self):
        return 'event', self.event.id, 'boa'

    def validate_file(self, file):
        return os.path.splitext(file.filename)[1].lower() == '.pdf'


class RHCustomBOA(RHManageAbstractsBase):
    """Manage custom book of abstracts."""

    @use_kwargs({
        'file': FileField(required=True, validate=file_extension('pdf')),
    })
    def _process_POST(self, file):
        self.event.custom_boa = file
        file.claim()
        self.event.log(EventLogRealm.reviewing, EventLogKind.positive, 'Abstracts',
                       'Custom Book of Abstracts uploaded', session.user)
        return '', 204

    def _process_DELETE(self):
        self.event.custom_boa = None
        self.event.log(EventLogRealm.reviewing, EventLogKind.negative, 'Abstracts',
                       'Custom Book of Abstracts deleted', session.user)
        return '', 204


class RHExportBOA(RHAbstractsBase):
    """Export the book of abstracts."""

    def _check_access(self):
        RHAbstractsBase._check_access(self)
        published = contribution_settings.get(self.event, 'published')
        if not published:
            raise NotFound(_("The contributions of this event have not been published yet"))

    def _process(self):
        if request.args.get('latex') == '1' and config.LATEX_ENABLED and self.event.can_manage(session.user):
            return send_file('book-of-abstracts.pdf', create_boa(self.event), 'application/pdf')
        if self.event.has_custom_boa:
            return self.event.custom_boa.send()
        elif config.LATEX_ENABLED:
            return send_file('book-of-abstracts.pdf', create_boa(self.event), 'application/pdf')
        raise NotFound


class RHExportBOATeX(RHManageAbstractsBase):
    """Export a zip file with the book of abstracts in TeX format."""

    def _process(self):
        return send_file('book-of-abstracts.zip', create_boa_tex(self.event), 'application/zip', inline=False)
