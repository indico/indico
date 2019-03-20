# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.util.caching import memoize_request


@memoize_request
def rb_check_user_access(user):
    """Checks if the user has access to the room booking system"""
    from indico.modules.rb import rb_settings
    if rb_is_admin(user):
        return True
    if not rb_settings.acls.get('authorized_principals'):  # everyone has access
        return True
    return rb_settings.acls.contains_user('authorized_principals', user)


@memoize_request
def rb_is_admin(user):
    """Checks if the user is a room booking admin"""
    from indico.modules.rb import rb_settings
    if user.is_admin:
        return True
    return rb_settings.acls.contains_user('admin_principals', user)
