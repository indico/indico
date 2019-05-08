# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import redirect

from indico.modules.admin import RHAdminBase
from indico.modules.legal import legal_settings
from indico.modules.legal.forms import LegalMessagesForm
from indico.modules.legal.views import WPDisplayPrivacyPolicy, WPDisplayTOS, WPManageLegalMessages
from indico.web.flask.util import url_for
from indico.web.rh import RH


class RHManageLegalMessages(RHAdminBase):
    def _process(self):
        form = LegalMessagesForm(**legal_settings.get_all())
        if form.validate_on_submit():
            legal_settings.set_multi(form.data)
            return redirect(url_for('legal.manage'))
        return WPManageLegalMessages.render_template('manage_messages.html', 'legal_messages', form=form)


class RHDisplayTOS(RH):
    def _process(self):
        url = legal_settings.get('tos_url')
        if url:
            return redirect(url)
        return WPDisplayTOS.render_template('tos.html', tos=legal_settings.get('tos'))


class RHDisplayPrivacyPolicy(RH):
    def _process(self):
        url = legal_settings.get('privacy_policy_url')
        if url:
            return redirect(url)
        return WPDisplayPrivacyPolicy.render_template('privacy.html', content=legal_settings.get('privacy_policy'))
