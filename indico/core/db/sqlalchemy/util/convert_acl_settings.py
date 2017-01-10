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

"""
Utility to convert ACLs settings from JSON settings to ACL settings
"""

# TODO: remove this module before releasing 2.0 when removing all the alembic revisions from the 1.9 era
# Indico 2.0 should come with a clean revision list!

import itertools
import json
from collections import defaultdict

from alembic import op

from indico.core.auth import multipass
from indico.core.db.sqlalchemy.principals import PrincipalType


def _principal_to_args(principal):
    type_, id_ = principal
    if type_ in {'Avatar', 'User'}:
        return PrincipalType.user.value, int(id_), None, None, None
    elif type_ == 'Group':
        if isinstance(id_, (int, basestring)):  # legacy group
            if unicode(id_).isdigit():
                return PrincipalType.local_group.value, None, int(id_), None, None
            else:
                return PrincipalType.multipass_group.value, None, None, multipass.default_group_provider.name, id_
        else:
            provider, name_or_id = id_
            if provider:
                return PrincipalType.multipass_group.value, None, None, provider, name_or_id
            else:
                return PrincipalType.local_group.value, None, name_or_id, None, None
    else:
        raise ValueError('Unexpected type: {}'.format(type_))


def _args_to_principal(type_, user_id, local_group_id, multipass_group_provider, multipass_group_name):
    if type_ == PrincipalType.user:
        return 'User', user_id
    elif type_ == PrincipalType.local_group:
        return 'Group', (None, local_group_id)
    elif type_ == PrincipalType.multipass_group:
        return 'Group', (multipass_group_provider, multipass_group_name)
    else:
        raise ValueError('Unexpected type: {}'.format(type_))


def json_to_acl(settings):
    conn = op.get_bind()
    settings = {tuple(x.split('.', 1)) for x in settings}
    params = ','.join(['(%s, %s)'] * len(settings))
    res = conn.execute("SELECT id, module, name, value "
                       "FROM indico.settings "
                       "WHERE (module, name) IN ({})".format(params),
                       tuple(itertools.chain.from_iterable(settings)))
    for id_, module, name, value in res:
        for args in map(_principal_to_args, value):
            conn.execute("INSERT INTO indico.settings_principals "
                         "(module, name, type, user_id, local_group_id, mp_group_provider, mp_group_name) VALUES "
                         "(%s, %s, %s, %s, %s, %s, %s)", (module, name) + args)
        conn.execute("DELETE FROM indico.settings WHERE id = %s", (id_,))


def acl_to_json(settings):
    conn = op.get_bind()
    settings = {tuple(x.split('.', 1)) for x in settings}
    params = ','.join(['(%s, %s)'] * len(settings))
    res = conn.execute("SELECT id, module, name, type, user_id, local_group_id, mp_group_provider, mp_group_name "
                       "FROM indico.settings_principals "
                       "WHERE (module, name) IN ({})".format(params),
                       tuple(itertools.chain.from_iterable(settings)))
    acls = defaultdict(set)
    ids = set()
    for row in res:
        ids.add(row[0])
        acls[row[1:3]].add(_args_to_principal(*row[3:]))
    for (module, name), acl in acls.iteritems():
        conn.execute("INSERT INTO indico.settings (module, name, value) VALUES (%s, %s, %s)",
                     (module, name, json.dumps(list(acl))))
    conn.execute("DELETE FROM indico.settings_principals WHERE id IN ({})".format(','.join(['%s'] * len(ids))), (ids,))
