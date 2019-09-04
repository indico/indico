# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request

from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.management.forms import ProgramCodesForm
from indico.modules.events.management.settings import program_codes_settings
from indico.modules.events.management.views import WPEventProgramCodes
from indico.util.placeholders import render_placeholder_info
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form


class RHProgramCodes(RHManageEventBase):
    def _process(self):
        templates = program_codes_settings.get_all(self.event)
        return WPEventProgramCodes.render_template('program_codes.html', self.event, 'program_codes',
                                                   templates=templates)


class RHProgramCodeTemplates(RHManageEventBase):
    def _process(self):
        form = ProgramCodesForm(obj=FormDefaults(**program_codes_settings.get_all(self.event)))
        contribution_placeholders = render_placeholder_info('program-codes-contribution', contribution=None)
        subcontribution_placeholders = render_placeholder_info('program-codes-subcontribution', subcontribution=None)
        session_placeholders = render_placeholder_info('program-codes-session', session=None)
        session_block_placeholders = render_placeholder_info('program-codes-session-block', session_block=None)
        form.contribution_template.description = contribution_placeholders
        form.subcontribution_template.description = subcontribution_placeholders
        form.session_template.description = session_placeholders
        form.session_block_template.description = session_block_placeholders

        if form.validate_on_submit():
            program_codes_settings.set_multi(self.event, form.data)
            return jsonify_data(flash=False)

        return jsonify_form(form)
