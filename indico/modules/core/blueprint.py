# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request

from indico.modules.core.controllers import (RHAPIGenerateCaptcha, RHChangeLanguage, RHChangeTimezone, RHConfig,
                                             RHContact, RHPrincipals, RHRenderMarkdown, RHReportErrorAPI,
                                             RHResetSignatureTokens, RHSessionExpiry, RHSessionRefresh, RHSettings,
                                             RHSignURL, RHVersionCheck)
from indico.web.flask.util import redirect_view
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('core', __name__, template_folder='templates', virtual_template_folder='core')

_bp.add_url_rule('/admin/settings/', 'settings', RHSettings, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/version-check', 'version_check', RHVersionCheck)

# TODO: replace with an actual admin dashboard at some point
_bp.add_url_rule('/admin/', 'admin_dashboard', view_func=redirect_view('.settings'))

# Global operations
_bp.add_url_rule('/change-language', 'change_lang', RHChangeLanguage, methods=('POST',))
_bp.add_url_rule('/change-timezone', 'change_tz', RHChangeTimezone, methods=('POST',))
_bp.add_url_rule('/session-expiry', 'session_expiry', RHSessionExpiry)
_bp.add_url_rule('/session-refresh', 'session_refresh', RHSessionRefresh, methods=('POST',))
_bp.add_url_rule('/api/principals', 'principals', RHPrincipals, methods=('POST',))
_bp.add_url_rule('/api/sign-url', 'sign_url', RHSignURL, methods=('POST',))
with _bp.add_prefixed_rules('/user/<int:user_id>', '/user'):
    _bp.add_url_rule('/reset-signature-tokens', 'reset_signature_tokens', RHResetSignatureTokens, methods=('POST',))
_bp.add_url_rule('/api/config', 'config', RHConfig)
_bp.add_url_rule('/api/render-markdown', 'markdown', RHRenderMarkdown, methods=('POST',))

# Misc pages
_bp.add_url_rule('/contact', 'contact', RHContact)
_bp.add_url_rule('/report-error/api/<error_id>', 'report_error_api', RHReportErrorAPI, methods=('POST',))

# Allow loadbalancers etc to easily check whether the service is alive
_bp.add_url_rule('/ping', 'ping', lambda: ('', 204))

# CAPTCHA
_bp.add_url_rule('/api/captcha/generate', 'generate_captcha', RHAPIGenerateCaptcha)


@_bp.url_defaults
def _add_user_id(endpoint, values):
    if endpoint == 'core.reset_signature_tokens' and 'user_id' not in values:
        values['user_id'] = request.view_args.get('user_id')
