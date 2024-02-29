# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import redirect, session

from indico.modules.admin import RHAdminBase
from indico.modules.legal import check_terms_required, legal_settings
from indico.modules.legal.forms import LegalMessagesForm, create_agreement_form
from indico.modules.legal.views import WPDisplayAgreement, WPDisplayPrivacyPolicy, WPDisplayTOS, WPManageLegalMessages
from indico.util.date_time import now_utc
from indico.web.flask.util import url_for
from indico.web.rh import RH
from indico.web.util import url_for_index


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


class RHAcceptTerms(RH):
    def _process(self):
        if not check_terms_required():
            return redirect(url_for_index())

        form = create_agreement_form()
        if form.validate_on_submit():
            if form.accept_terms.data:
                session.user.accepted_terms_dt = now_utc()
            return redirect(session.pop('legal_agreement_return_path', url_for_index()))

        return WPDisplayAgreement.render_template('agreement.html', form=form, **legal_settings.get_all())
