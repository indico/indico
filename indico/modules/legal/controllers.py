# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import redirect, request, session

from indico.modules.admin import RHAdminBase
from indico.modules.legal import legal_settings
from indico.modules.legal.forms import AgreementForm, LegalMessagesForm
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
        terms_date = legal_settings.get('terms_effective_date')
        user_accepted = (
            session.user.accepted_tos_dt
            and session.user.accepted_tos_dt >= terms_date
        )
        if not request.args.get('preview', False) and (
            not legal_settings.get('terms_require_accept') or not terms_date or user_accepted
        ):
            return redirect(url_for_index())

        form = AgreementForm()

        if form.validate_on_submit():
            if not request.args.get('preview', False) and form.data['accept_terms']:
                session.user.accepted_tos_dt = max(now_utc(), terms_date)

            returnpath = session.pop('legal_agreement_return_path', url_for_index())
            return redirect(returnpath)

        return WPDisplayAgreement.render_template(
            'agreement.html',
            form=form,
            **legal_settings.get_all()
        )
