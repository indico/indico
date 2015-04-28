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


    def mergeAvatar(self, prin, merged):
        #replace merged by prin in all object where merged is
        links = merged.getLinkedTo()
        for objType in links.keys():
            if objType == "category":
                for role in links[objType].keys():
                    for cat in set(links[objType][role]):
                        # if the category has been deleted
                        if cat.getOwner() == None and cat.getId() != '0':
                            Logger.get('user.merge').warning(
                                "Trying to remove %s from %s (%s) but it seems to have been deleted" % \
                                (cat, prin.getId(), role))
                            continue
                        elif role == "creator":
                            cat.revokeConferenceCreation(merged)
                            cat.grantConferenceCreation(prin)
                        elif role == "manager":
                            cat.revokeModification(merged)
                            cat.grantModification(prin)
                        elif role == "access":
                            cat.revokeAccess(merged)
                            cat.grantAccess(prin)
                        elif role == "favorite":
                            merged.unlinkTo(cat, 'favorite')
                            prin.linkTo(cat, 'favorite')

            elif objType == "conference":
                confHolderIdx = MaKaC.conference.ConferenceHolder()._getIdx()

                for role in links[objType].keys():
                    for conf in set(links[objType][role]):
                        # if the conference has been deleted
                        if conf.getId() not in confHolderIdx:
                            Logger.get('user.merge').warning(
                                "Trying to remove %s from %s (%s) but it seems to have been deleted" % \
                                (conf, prin.getId(), role))
                            continue
                        elif role == "creator":
                            conf.setCreator(prin)
                        elif role == "chair":
                            conf.removeChair(merged)
                            conf.addChair(prin)
                        elif role == "manager":
                            conf.revokeModification(merged)
                            conf.grantModification(prin)
                        elif role == "access":
                            conf.revokeAccess(merged)
                            conf.grantAccess(prin)
                        elif role == "abstractSubmitter":
                            conf.removeAuthorizedSubmitter(merged)
                            conf.addAuthorizedSubmitter(prin)

            if objType == "session":
                for role in links[objType].keys():
                    for ses in set(links[objType][role]):
                        owner = ses.getOwner()
                        # tricky, as conference containing it may have been deleted
                        if owner == None or owner.getOwner() == None:
                                Logger.get('user.merge').warning(
                                    "Trying to remove %s from %s (%s) but it seems to have been deleted" % \
                                    (ses, prin.getId(), role))
                        elif role == "manager":
                            ses.revokeModification(merged)
                            ses.grantModification(prin)
                        elif role == "access":
                            ses.revokeAccess(merged)
                            ses.grantAccess(prin)
                        elif role == "coordinator":
                            ses.removeCoordinator(merged)
                            ses.addCoordinator(prin)

            if objType == "contribution":
                for role in links[objType].keys():
                    for contrib in set(links[objType][role]):
                        if contrib.getOwner() == None:
                                Logger.get('user.merge').warning(
                                    "Trying to remove %s from %s (%s) but it seems to have been deleted" % \
                                    (contrib, prin.getId(), role))
                        elif role == "manager":
                            contrib.revokeModification(merged)
                            contrib.grantModification(prin)
                        elif role == "access":
                            contrib.revokeAccess(merged)
                            contrib.grantAccess(prin)
                        elif role == "submission":
                            contrib.revokeSubmission(merged)
                            contrib.grantSubmission(prin)

            if objType == "track":
                for role in links[objType].keys():
                    if role == "coordinator":
                        for track in set(links[objType][role]):
                            track.removeCoordinator(merged)
                            track.addCoordinator(prin)

            if objType == "material":
                for role in links[objType].keys():
                    if role == "access":
                        for mat in set(links[objType][role]):
                            mat.revokeAccess(merged)
                            mat.grantAccess(prin)

            if objType == "file":
                for role in links[objType].keys():
                    if role == "access":
                        for mat in set(links[objType][role]):
                            mat.revokeAccess(merged)
                            mat.grantAccess(prin)

            if objType == "abstract":
                for role in links[objType].keys():
                    if role == "submitter":
                        for abstract in set(links[objType][role]):
                            abstract.setSubmitter(prin)

            if objType == "registration":
                for role in links[objType].keys():
                    if role == "registrant":
                        for reg in set(links[objType][role]):
                            reg.setAvatar(prin)
                            prin.addRegistrant(reg)

            # TODO: handle this properly in the users module via the merge hook
            # if objType == "group":
            #     for role in links[objType].keys():
            #         if role == "member":
            #             for group in set(links[objType][role]):
            #                 group.removeMember(merged)
            #                 group.addMember(prin)

            if objType == "evaluation":
                for role in links[objType].keys():
                    if role == "submitter":
                        for submission in set(links[objType][role]):
                            if len([s for s in submission.getEvaluation().getSubmissions() if s.getSubmitter()==prin]) >0 :
                                #prin has also answered to the same evaluation as merger's.
                                submission.setSubmitter(None)
                            else:
                                #prin ditn't answered to the same evaluation as merger's.
                                submission.setSubmitter(prin)

        # Merge avatars in redis
        if redis_write_client:
            avatar_links.merge_avatars(prin, merged)
            suggestions.merge_avatars(prin, merged)

        # Merge avatars in RB
        from indico.modules.rb.utils import rb_merge_users
        rb_merge_users(prin.getId(), merged.getId())

        # Notify signal listeners about the merge
        signals.merge_users.send(prin, merged=merged)

        # remove merged from holder
        self.remove(merged)
        idxs = indexes.IndexesHolder()
        org = idxs.getById('organisation')
        email = idxs.getById('email')
        name = idxs.getById('name')
        surName = idxs.getById('surName')
        status_index = idxs.getById('status')

        org.unindexUser(merged)
        email.unindexUser(merged)
        name.unindexUser(merged)
        surName.unindexUser(merged)
        status_index.unindexUser(merged)

        # add merged email and logins to prin and merge users
        for mail in merged.getEmails():
            prin.addSecondaryEmail(mail)
        for id in merged.getIdentityList(create_identities=True):
            id.setUser(prin)
            prin.addIdentity(id)

        merged.mergeTo(prin)

        # reindex prin email
        email.unindexUser(prin)
        email.indexUser(prin)

    def unmergeAvatar(self, prin, merged):
        if not merged in prin.getMergeFromList():
            return False
        merged.mergeTo(None)

        idxs = indexes.IndexesHolder()
        org = idxs.getById('organisation')
        email = idxs.getById('email')
        name = idxs.getById('name')
        surName = idxs.getById('surName')


        email.unindexUser(prin)
        for mail in merged.getEmails():
            prin.removeSecondaryEmail(mail)

        for id in merged.getIdentityList(create_identities=True):
            prin.removeIdentity(id)
            id.setUser(merged)

        self.add(merged)

        org.indexUser(merged)
        email.indexUser(merged)
        name.indexUser(merged)
        surName.indexUser(merged)

        email.indexUser(prin)
        return True
