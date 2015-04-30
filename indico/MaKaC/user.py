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


from flask_multipass import IdentityInfo

import MaKaC
from MaKaC.common import indexes
from MaKaC.common.cache import GenericCache
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.errors import UserError

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.users import User
from indico.modules.users.legacy import AvatarProvisionalWrapper
from indico.util.i18n import _
from indico.util.redis import avatar_links, suggestions, write_client as redis_write_client


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
    _indexes = [ "email", "name", "surName","organisation", "status" ]

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

    def add(self,av):
        """
            Before adding the user, check if the email address isn't used
        """
        if av.getEmail() is None or av.getEmail()=="":
            raise UserError(_("User not created. You must enter an email address"))
        emailmatch = self.match({'email': av.getEmail()}, exact=1, searchInAuthenticators=False)
        if emailmatch != None and len(emailmatch) > 0 and emailmatch[0] != '':
            raise UserError(_("User not created. The email address %s is already used.")% av.getEmail())
        id = ObjectHolder.add(self,av)
        for i in self._indexes:
            indexes.IndexesHolder().getById(i).indexUser(av)
        return id
