# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from flask import session
from werkzeug.datastructures import MultiDict


def save_identity_info(identity_info, user):
    """Saves information from IdentityInfo in the session"""
    trusted_email = identity_info.provider.settings.get('trusted_email', False)
    session['login_identity_info'] = {
        'provider': identity_info.provider.name,
        'provider_title': identity_info.provider.title,
        'identifier': identity_info.identifier,
        'multipass_data': identity_info.multipass_data,
        'data': dict(identity_info.data.lists()),
        'indico_user_id': user.id if user else None,
        'email_verified': bool(identity_info.data['email'] and trusted_email)
    }


def load_identity_info():
    """Retrieves identity information from the session"""
    try:
        info = session['login_identity_info'].copy()
    except KeyError:
        return None
    # Restoring a multidict is quite ugly...
    data = info.pop('data')
    info['data'] = MultiDict()
    info['data'].update(data)
    return info
