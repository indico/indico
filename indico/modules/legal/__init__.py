# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import render_template, session

from indico.core import signals
from indico.core.settings import SettingsProxy
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
    'privacy_policy': ''
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
