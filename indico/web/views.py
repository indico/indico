# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals

from flask import session
from markupsafe import Markup
from pytz import common_timezones, common_timezones_set

from indico.core.config import Config
from indico.modules.legal import legal_settings
from indico.util.i18n import get_all_locales
from indico.web.flask.templating import get_template_module


def _get_timezone_display(local_tz, timezone, force=False):
    if force and local_tz:
        return local_tz
    elif timezone == 'LOCAL':
        return local_tz or Config.getInstance().getDefaultTimezone()
    else:
        return timezone


def render_session_bar(protected_object=None, local_tz=None, force_local_tz=False):
    protection_disclaimers = {
        'network': legal_settings.get('network_protected_disclaimer'),
        'restricted': legal_settings.get('restricted_disclaimer')
    }
    default_tz = Config.getInstance().getDefaultTimezone()
    if session.user:
        user_tz = session.user.settings.get('timezone', default_tz)
        if session.timezone == 'LOCAL':
            tz_mode = 'local'
        elif session.timezone == user_tz:
            tz_mode = 'user'
        else:
            tz_mode = 'custom'
    else:
        user_tz = None
        tz_mode = 'local' if session.timezone == 'LOCAL' else 'custom'
    active_tz = _get_timezone_display(local_tz, session.timezone, force_local_tz)
    timezones = common_timezones
    if active_tz not in common_timezones_set:
        timezones = list(common_timezones) + [active_tz]
    timezone_data = {
        'disabled': force_local_tz,
        'user_tz': user_tz,
        'active_tz': active_tz,
        'tz_mode': tz_mode,
        'timezones': timezones,
    }
    tpl = get_template_module('_session_bar.html')
    rv = tpl.render_session_bar(protected_object=protected_object,
                                protection_disclaimers=protection_disclaimers,
                                timezone_data=timezone_data,
                                languages=get_all_locales())
    return Markup(rv)
