# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import redirect, render_template, request, session

from indico.core import signals
from indico.core.settings import SettingsProxy
from indico.core.settings.converters import ServerDateConverter
from indico.util.i18n import _
from indico.web.flask.templating import template_hook
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


_DEFAULT_RESTRICTED_DISCLAIMER = ('Circulation to people other than the intended audience is not authorized. '
                                  'You are obliged to treat the information with the appropriate level of '
                                  'confidentiality.')
_DEFAULT_PROTECTED_DISCLAIMER = ('As such, this information is intended for an internal audience only. '
                                 'You are obliged to treat the information with the appropriate level of '
                                 'confidentiality.')


legal_settings = SettingsProxy('legal', {
    'network_protected_disclaimer': _DEFAULT_PROTECTED_DISCLAIMER,
    'restricted_disclaimer': _DEFAULT_RESTRICTED_DISCLAIMER,
    'tos_url': '',
    'tos': '',
    'privacy_policy_url': '',
    'privacy_policy': '',
    'terms_require_accept': False,
    'terms_effective_date': None,
}, converters={
    'terms_effective_date': ServerDateConverter
})


@signals.menu.items.connect_via('admin-sidemenu')
def _sidemenu_items(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('legal_messages', _('Legal/Disclaimers'), url_for('legal.manage'), section='security')


@template_hook('page-footer', priority=50)
def _inject_tos_footer(**kwargs):
    url = legal_settings.get('tos_url')
    if url or legal_settings.get('tos'):
        return render_template('legal/tos_footer.html', url=url)


@template_hook('page-footer', priority=51)
def _inject_privacy_footer(**kwargs):
    url = legal_settings.get('privacy_policy_url')
    if url or legal_settings.get('privacy_policy'):
        return render_template('legal/privacy_footer.html', url=url)


@template_hook('global-announcement', markup=False)
def _inject_announcement_header(**kwargs):
    # Don't show if no user or not admin
    if not session.user or not session.user.is_admin:
        return

    # Don't show the banner on the accept terms page
    if request.endpoint == 'legal.accept_agreement':
        return

    # Don't show the banner if accepting terms is not required
    terms_date = legal_settings.get('terms_effective_date')
    if not legal_settings.get('terms_require_accept') or not terms_date:
        return

    # If you have accepted the most current terms, you are good
    if session.user.accepted_tos_dt and session.user.accepted_tos_dt >= terms_date:
        return

    # Everyone else gets the warning
    return 'warning', render_template('legal/admin_agreement_banner.html'), True


def confirm_rh_terms_required():
    terms_date = legal_settings.get('terms_effective_date')
    if not legal_settings.get('terms_require_accept') or not terms_date:
        return

    # If you are not logged in or admin, we're not checking
    if not session.user or session.user.is_admin:
        return

    # If you have accepted the most current terms, you are good
    if session.user.accepted_tos_dt and session.user.accepted_tos_dt >= terms_date:
        return

    # Certain endpoints need to be passed through.
    if request.blueprint and request.blueprint in ('assets', 'legal', 'auth', 'core'):
        return

    # Everything else gets redirected to the terms page
    session['legal_agreement_return_path'] = request.path
    return redirect(url_for('legal.accept_agreement'))
