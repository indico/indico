# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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


from flask_multipass import IdentityInfo

from MaKaC.common.cache import GenericCache
from MaKaC.common.ObjectHolders import ObjectHolder

from indico.modules.users import User
from indico.modules.users.legacy import AvatarProvisionalWrapper


AVATAR_FIELD_MAP = {
    "email": "email",
    "name": "first_name",
    "surName": "last_name",
    "organisation": "affiliation"
}


class AvatarHolder(ObjectHolder):
    """Specialised ObjectHolder dealing with user (avatar) objects. Objects of
       this class represent an access point to Avatars of the application and
       provides different methods for accessing and retrieving them in several
       ways.
    """
    idxName = "avatars"
    counterName = "PRINCIPAL"

    def match(self, criteria, exact=False, onlyActivated=True, searchInAuthenticators=False):
        from indico.modules.users.util import search_users
        cache = GenericCache('pending_identities')

        def _process_identities(obj):
            if isinstance(obj, IdentityInfo):
                cache.set(obj.provider.name + ":" + obj.identifier, obj.data)
                return AvatarProvisionalWrapper(obj)
            else:
                return obj.as_avatar

        results = search_users(exact=exact, include_pending=not onlyActivated, include_deleted=not onlyActivated,
                               external=searchInAuthenticators,
                               **{AVATAR_FIELD_MAP[k]: v for (k, v) in criteria.iteritems() if v})

        return [_process_identities(obj) for obj in results]

    def getById(self, id):
        if isinstance(id, int) or id.isdigit():
            user = User.get(int(id))
            if user:
                return user.as_avatar
