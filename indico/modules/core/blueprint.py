# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.core.controllers import (RHChangeLanguage, RHChangeTimezone, RHConfig, RHContact, RHPrincipals,
                                             RHReportErrorAPI, RHResetSignatureTokens, RHSettings, RHSignURL,
                                             RHVersionCheck)
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
_bp.add_url_rule('/api/principals', 'principals', RHPrincipals, methods=('GET', 'POST'))
_bp.add_url_rule('/api/sign-url', 'sign_url', RHSignURL, methods=('POST',))
_bp.add_url_rule('/api/reset-signature-tokens', 'reset_signature_tokens', RHResetSignatureTokens, methods=('POST',))
_bp.add_url_rule('/api/config', 'config', RHConfig)

# Misc pages
_bp.add_url_rule('/contact', 'contact', RHContact)
_bp.add_url_rule('/report-error/api/<error_id>', 'report_error_api', RHReportErrorAPI, methods=('POST',))

# Allow loadbalancers etc to easily check whether the service is alive
_bp.add_url_rule('/ping', 'ping', lambda: ('', 204))
