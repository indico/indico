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

from __future__ import unicode_literals


def serialize_role(role):
    """Serialize role to JSON-like object"""
    return {
        'id': role.id,
        'name': role.name,
        'code': role.code,
        'color': role.color,
        'identifier': 'Role:{}'.format(role.id),
        '_type': 'EventRole'
    }


def get_role_colors():
    """Get the list of colors available for event roles"""
    return ['005272', '007cac', '5d95ea',
            'af0000', 'a76766',
            '999999', '555555', '777777',
            '67a766', '6cc644',
            '9c793b', 'e99e18',
            'b14300', 'e25300',
            '6e5494', 'cb6ea4',
            '0b63a5', '00a4e4']
