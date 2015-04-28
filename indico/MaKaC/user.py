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


from BTrees.OOBTree import OOTreeSet
from flask_multipass import IdentityInfo
from persistent import Persistent
from pytz import all_timezones

import MaKaC
from MaKaC.authentication.AuthenticationMgr import AuthenticatorMgr
from MaKaC.common import filters, indexes
from MaKaC.common.cache import GenericCache
import MaKaC.common.info as info
from MaKaC.common.Locators import Locator
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.errors import UserError, MaKaCError
from MaKaC.common.fossilize import Fossilizable, fossilizes
from MaKaC.fossils.user import (IAvatarFossil, IAvatarAllDetailsFossil, IGroupFossil, IPersonalInfoFossil,
                                IAvatarMinimalFossil)
from MaKaC.trashCan import TrashCanManager

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.users import User
from indico.modules.users.legacy import AvatarUserWrapper, AvatarProvisionalWrapper
from indico.util.caching import memoize_request
from indico.util.decorators import cached_classproperty
from indico.util.i18n import _
from indico.util.redis import avatar_links, suggestions, write_client as redis_write_client
from indico.util.string import safe_upper, safe_slice
from indico.util.user import retrieve_principals


class Group(Persistent, Fossilizable):
    fossilizes(IGroupFossil)

    """
    """
    groupType = "Default"

    def __init__(self, groupData=None):
        self.id = ""
        self.name = ""
        self.description = ""
        self.email = ""
        self.members = []
        self.obsolete = False

    def __cmp__(self, other):
        if type(self) is not type(other):
            # This is actually dangerous and the ZODB manual says not to do this
            # because it relies on memory order. However, this branch should never
            # be taken anyway since we do not store different types in the same set
            # or use them as keys.
            return cmp(hash(self), hash(other))
        return cmp(self.getId(), other.getId())

    def setId(self, newId):
        self.id = str(newId)

    def getId(self):
        return self.id

    def setName(self, newName):
        self.name = newName.strip()
        GroupHolder().notifyGroupNameChange(self)

    def getName(self):
        return self.name
    getFullName = getName

    def setDescription(self, newDesc):
        self.description = newDesc.strip()

    def getDescription(self):
        return self.description

    def setEmail(self, newEmail):
        self.email = newEmail.strip()

    def getEmail(self):
        try:
            return self.email
        except:
            self.email = ""
        return self.email

    def isObsolete(self):
        if not hasattr(self, "obsolete"):
            self.obsolete = False
        return self.obsolete

    def setObsolete(self, obsolete):
        self.obsolete = obsolete

    def _cleanGroupMembershipCache(self, avatar):
        group_membership = GenericCache('groupmembership')
        key = "{0}-{1}".format(self.getId(), avatar.getId())
        group_membership.delete(key)

    def addMember(self, newMember):
        if newMember == self:
            raise MaKaCError(_("It is not possible to add a group as member of itself"))
        if self.containsMember(newMember) or newMember.containsMember(self):
            return
        self.members.append(newMember)
        if isinstance(newMember, AvatarUserWrapper):
            newMember.linkTo(self, "member")
        self._p_changed = 1

        # We need to clean the gooup membership cache
        self._cleanGroupMembershipCache(newMember)

    def removeMember(self, member):
        if member is None or member not in self.members:
            return
        self.members.remove(member)
        if isinstance(member, AvatarUserWrapper):
            member.unlinkTo(self, "member")
        self._p_changed = 1

        # We need to clean the gooup membership cache
        self._cleanGroupMembershipCache(member)

    def getMemberList(self):
        return self.members

    def _containsUser(self, avatar):
        if avatar == None:
            return 0
        for member in self.members:
            if member.containsUser(avatar):
                return 1
        return 0

    def containsUser(self, avatar):
        group_membership = GenericCache('groupmembership')
        if avatar is None:
            return False
        key = "{0}-{1}".format(self.getId(), avatar.getId())
        user_in_group = group_membership.get(key)
        if user_in_group is None:
            user_in_group = self._containsUser(avatar)
            group_membership.set(key, user_in_group, time=1800)
        return user_in_group

    def containsMember(self, member):
        if member == None:
            return 0
        if member in self.members:
            return 1
        for m in self.members:
            try:
                if m.containsMember(member):
                    return 1
            except AttributeError, e:
                continue
        return 0

    def canModify(self, aw_or_user):
        if hasattr(aw_or_user, 'getUser'):
            aw_or_user = aw_or_user.getUser()
        return self.canUserModify(aw_or_user)

    def canUserModify(self, user):
        return self.containsMember(user) or user.user.is_admin

    def getLocator(self):
        d = Locator()
        d["groupId"] = self.getId()
        return d

    def exists(self):
        return True


class _GroupFFName(filters.FilterField):
    _id="name"

    def satisfies(self,group):
        for value in self._values:
            if value.strip() != "":
                if value.strip() == "*":
                    return True
                if str(group.getName()).lower().find((str(value).strip().lower()))!=-1:
                    return True
        return False


class _GroupFilterCriteria(filters.FilterCriteria):
    _availableFields={"name":_GroupFFName}

    def __init__(self,criteria={}):
        filters.FilterCriteria.__init__(self,None,criteria)


class GroupHolder(ObjectHolder):
    """
    """
    idxName = "groups"
    counterName = "PRINCIPAL"

    def getById(self, id):
        raise RuntimeError('obsolete')

    def add(self, group):
        ObjectHolder.add(self, group)
        self.getIndex().indexGroup(group)

    def remove(self, group):
        ObjectHolder.remove(self, group)
        self.getIndex().unindexGroup(group)

    def notifyGroupNameChange(self, group):
        self.getIndex().unindexGroup(group)
        self.getIndex().indexGroup(group)

    def getIndex(self):
        index = indexes.IndexesHolder().getById("group")
        if index.getLength() == 0:
            self._reIndex(index)
        return index

    def _reIndex(self, index):
        for group in self.getList():
            index.indexGroup(group)

    def getBrowseIndex(self):
        return self.getIndex().getBrowseIndex()

    def getLength(self):
        return self.getIndex().getLength()

    def matchFirstLetter(self, letter, searchInAuthenticators=True):
        result = []
        index = self.getIndex()
        if searchInAuthenticators:
            self._updateGroupMatchFirstLetter(letter)
        match = index.matchFirstLetter(letter)
        if match != None:
            for groupid in match:
                if groupid != "":
                    if self.getById(groupid) not in result:
                        gr=self.getById(groupid)
                        result.append(gr)
        return result

    def match(self, criteria, searchInAuthenticators=True, exact=False):
        crit={}
        result = []
        for f,v in criteria.items():
            crit[f]=[v]
        if crit.has_key("groupname"):
            crit["name"] = crit["groupname"]
        if searchInAuthenticators:
            self._updateGroupMatch(crit["name"][0],exact)
        match = self.getIndex().matchGroup(crit["name"][0], exact=exact)

        if match != None:
            for groupid in match:
                gr = self.getById(groupid)
                if gr not in result:
                    result.append(gr)
        return result

    def update(self, group):
        if self.hasKey(group.getId()):
            current_group = self.getById(group.getId())
            current_group.setDescription(group.getDescription())

    def _updateGroupMatch(self, name, exact=False):
        for auth in AuthenticatorMgr().getList():
            for group in auth.matchGroup(name, exact):
                if not self.hasKey(group.getId()):
                    self.add(group)
                else:
                    self.update(group)

    def _updateGroupMatchFirstLetter(self, letter):
        for auth in AuthenticatorMgr().getList():
            for group in auth.matchGroupFirstLetter(letter):
                if not self.hasKey(group.getId()):
                    self.add(group)
                else:
                    self.update(group)


class Avatar(Persistent, Fossilizable):
    """This class implements the representation of users inside the system.
       Basically it contains personal data from them which is relevant for the
       system.
    """
    fossilizes(IAvatarFossil, IAvatarAllDetailsFossil, IAvatarMinimalFossil)

    # When this class is defined MaKaC.conference etc. are not available yet
    @cached_classproperty
    @classmethod
    def linkedToMap(cls):
        import MaKaC.conference
        import MaKaC.registration
        import MaKaC.evaluation
        # Hey, when adding new roles don't forget to handle them in AvatarHolder.mergeAvatar, too!
        return {
            'category': {'cls': MaKaC.conference.Category,
                         'roles': set(['access', 'creator', 'favorite', 'manager'])},
            'conference': {'cls': MaKaC.conference.Conference,
                           'roles': set(['abstractSubmitter', 'access', 'chair', 'creator', 'editor', 'manager',
                                         'paperReviewManager', 'participant', 'referee', 'registrar', 'reviewer'])},
            'session': {'cls': MaKaC.conference.Session,
                        'roles': set(['access', 'coordinator', 'manager'])},
            'contribution': {'cls': MaKaC.conference.Contribution,
                             'roles': set(['access', 'editor', 'manager', 'referee', 'reviewer', 'submission'])},
            'track': {'cls': MaKaC.conference.Track,
                      'roles': set(['coordinator'])},
            'material': {'cls': MaKaC.conference.Material,
                         'roles': set(['access'])},
            'resource': {'cls': MaKaC.conference.Resource,
                         'roles': set(['access'])},
            'abstract': {'cls': MaKaC.review.Abstract,
                         'roles': set(['submitter'])},
            'registration': {'cls': MaKaC.registration.Registrant,
                             'roles': set(['registrant'])},
            'group': {'cls': MaKaC.user.Group,
                      'roles': set(['member'])},
            'evaluation': {'cls': MaKaC.evaluation.Submission,
                           'roles': set(['submitter'])}
        }

    def __init__(self, userData=None):
        """Class constructor.
           Attributes:
                userData -- dictionary containing user data to map into the
                            avatar. Possible key values (those with * are
                            multiple):
                                name, surname, title, organisation*, addess*,
                                email*, telephone*, fax*
        """
        self.id = ""
        self.personId = None
        self.name = ""
        self.surName = ""
        self.title = ""
        self.organisation = [""]
        self.address = [""]
        self.email = ""
        self.secondaryEmails = []
        self.telephone = [""]
        self.fax = [""]
        self.identities = []
        self.status = "Not confirmed" # The status can be 'activated', 'disabled' or 'Not confirmed'
        from MaKaC.common import utils
        self.key = utils.newKey() #key to activate the account
        self.registrants = {}

        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        self._lang = minfo.getLang()
        self._mergeTo = None
        self._mergeFrom = []

        #################################
        #Fermi timezone awareness       #
        #################################

        self.timezone = ""
        self.displayTZMode = ""

        #################################
        #Fermi timezone awareness(end)  #
        #################################

        self.resetLinkedTo()

        self.personalInfo = PersonalInfo()
        self.unlockedFields = [] # fields that are not synchronized with auth backends
        self.authenticatorPersonalData = {} # personal data from authenticator

        if userData is not None:
            if 'name' in userData:
                self.setName(userData["name"])
            if 'surName' in userData:
                self.setSurName(userData["surName"])
            if 'title' in userData:
                self.setTitle(userData["title"])
            if 'organisation' in userData:
                self.setOrganisation(self._flatten(userData['organisation']))
            if 'address' in userData:
                self.setAddress(self._flatten(userData["address"]))
            if 'email' in userData:
                self.setEmail(self._flatten(userData["email"]))
            if 'phone' in userData:
                self.setTelephone(userData["phone"])
            if 'fax' in userData:
                self.setFax(userData["fax"])

            ############################
            #Fermi timezone awareness  #
            ############################

            if 'timezone' in userData:
                self.setTimezone(userData["timezone"])
            else:
                self.setTimezone(info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone())

            self.setDisplayTZMode(userData.get("displayTZMode", "Event Timezone"))

    def _flatten(self, data):
        if isinstance(data, (list, set, tuple)):
            return data[0]
        else:
            return data

    def __repr__(self):
        return '<Avatar({0}, {1})>'.format(self.getId(), self.getFullName())

    def mergeTo(self, av):
        if av:
            av.mergeFrom(self)
        if self.getMergeTo():
            self._mergeTo.unmergeFrom(self)
        self._mergeTo = av

    def getMergeTo(self):
        try:
            return self._mergeTo
        except:
            self._mergeTo = None
        return self._mergeTo

    def isMerged(self):
        if self.getMergeTo():
            return True
        return False

    def mergeFrom(self, av):
        if not av in self.getMergeFromList():
            self._mergeFrom.append(av)
            self._p_changed = 1

    def unmergeFrom(self, av):
        if av in self.getMergeFromList():
            self._mergeFrom.remove(av)
            self._p_changed = 1

    def getMergeFromList(self):
        try:
            return self._mergeFrom
        except:
            self._mergeFrom = []
        return self._mergeFrom

    def getKey(self):
        return self.key

    @property
    @memoize_request
    def api_key(self):
        from indico.modules.api.models.keys import APIKey
        return APIKey.find_first(user_id=int(self.id), is_active=True)

    def resetLinkedTo(self):
        self.linkedTo = {}
        self.updateLinkedTo()
        self._p_changed = 1

    def getLinkedTo(self):
        try:
            return self.linkedTo
        except AttributeError:
            self.resetLinkedTo()
            return self.linkedTo

    def updateLinkedTo(self):
        self.getLinkedTo()  # Create attribute if does not exist
        for field, data in self.linkedToMap.iteritems():
            self.linkedTo.setdefault(field, {})
            for role in data['roles']:
                self.linkedTo[field].setdefault(role, OOTreeSet())

    def linkTo(self, obj, role):
        # to avoid issues with zombie avatars
        if not AvatarHolder().hasKey(self.getId()):
            return
        self.updateLinkedTo()
        for field, data in self.linkedToMap.iteritems():
            if isinstance(obj, data['cls']):
                if role not in data['roles']:
                    raise ValueError('role %s is not allowed for %s objects' % (role, type(obj).__name__))
                self.linkedTo[field][role].add(obj)
                self._p_changed = 1
                if redis_write_client:
                    event = avatar_links.event_from_obj(obj)
                    if event:
                        avatar_links.add_link(self, event, field + '_' + role)
                break

    def getLinkTo(self, field, role):
        self.updateLinkedTo()
        return self.linkedTo[field][role]

    def unlinkTo(self, obj, role):
        # to avoid issues with zombie avatars
        if not AvatarHolder().hasKey(self.getId()):
            return
        self.updateLinkedTo()
        for field, data in self.linkedToMap.iteritems():
            if isinstance(obj, data['cls']):
                if role not in data['roles']:
                    raise ValueError('role %s is not allowed for %s objects' % (role, type(obj).__name__))
                if obj in self.linkedTo[field][role]:
                    self.linkedTo[field][role].remove(obj)
                    self._p_changed = 1
                    if redis_write_client:
                        event = avatar_links.event_from_obj(obj)
                        if event:
                            avatar_links.del_link(self, event, field + '_' + role)
                break

    def getStatus(self):
        try:
            return self.status
        except AttributeError:
            self.status = "activated"
            return self.status

    def setStatus(self, status):
        statIdx = indexes.IndexesHolder().getById("status")
        statIdx.unindexUser(self)
        self.status = status
        self._p_changed = 1
        statIdx.indexUser(self)

    def activateAccount(self, checkPending=True):
        self.setStatus("activated")
        if checkPending:
            #----Grant rights if any
            from MaKaC.common import pendingQueues
            pendingQueues.PendingQueuesHolder().grantRights(self)

    def disabledAccount(self):
        self.setStatus("disabled")

    def isActivated(self):
        return self.status == "activated"

    def isDisabled(self):
        return self.status == "disabled"

    def isNotConfirmed(self):
        return self.status == "Not confirmed"

    def setId(self, id):
        self.id = str(id)

    def getId(self):
        return self.id

    def setPersonId(self, personId):
        self.personId = personId

    def getPersonId(self):
        return getattr(self, 'personId', None)

    def setName(self, name, reindex=False):
        if reindex:
            idx = indexes.IndexesHolder().getById('name')
            idx.unindexUser(self)
            self.name = name
            idx.indexUser(self)
        else:
            self.name = name
        self._p_changed = 1

    def getName(self):
        return self.name

    getFirstName = getName
    setFirstName = setName

    def setSurName(self, name, reindex=False):
        if reindex:
            idx = indexes.IndexesHolder().getById('surName')
            idx.unindexUser(self)
            self.surName = name
            idx.indexUser(self)
        else:
            self.surName = name

    def getSurName(self):
        return self.surName

    def getFamilyName(self):
        return self.surName

    def getFullName(self):
        surName = ""
        if self.getSurName():
            surName = "%s, " % safe_upper(self.getSurName())
        return "%s%s" % (surName, self.getName())

    def getStraightFullName(self, upper=True):
        lastName = safe_upper(self.getFamilyName()) if upper else self.getFamilyName()
        return "{0} {1}".format(self.getFirstName(), lastName).strip()

    getDirectFullNameNoTitle = getStraightFullName

    def getAbrName(self):
        res = self.getSurName()
        if self.getName():
            if res:
                res = "%s, " % res
            res = "%s%s." % (res, safe_upper(safe_slice(self.getName(), 0, 1)))
        return res

    def getStraightAbrName(self):
        name = ""
        if self.getName():
            name = "%s. " % safe_upper(safe_slice(self.getName(), 0, 1))
        return "%s%s" % (name, self.getSurName())

    def addOrganisation(self, newOrg, reindex=False):
        if reindex:
            idx = indexes.IndexesHolder().getById('organisation')
            idx.unindexUser(self)
            self.organisation.append(newOrg.strip())
            idx.indexUser(self)
        else:
            self.organisation.append(newOrg.strip())
        self._p_changed = 1

    def setOrganisation(self, org, item=0, reindex=False):
        if reindex:
            idx = indexes.IndexesHolder().getById('organisation')
            idx.unindexUser(self)
            self.organisation[item] = org.strip()
            idx.indexUser(self)
        else:
            self.organisation[item] = org.strip()
        self._p_changed = 1

    setAffiliation = setOrganisation

    def getOrganisations(self):
        return self.organisation

    def getOrganisation(self):
        return self.organisation[0]

    getAffiliation = getOrganisation

    def setTitle(self, title):
        self.title = title

    def getTitle(self):
        return self.title

    #################################
    #Fermi timezone awareness       #
    #################################

    def setTimezone(self,tz=None):
        if not tz:
            tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        self.timezone = tz

    def getTimezone(self):
        tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        try:
            if self.timezone in all_timezones:
                return self.timezone
            else:
                self.setTimezone(tz)
                return tz
        except:
            self.setTimezone(tz)
            return tz

    def setDisplayTZMode(self,display_tz='Event Timezone'):
        self.displayTZMode = display_tz

    def getDisplayTZMode(self):
        return self.displayTZMode

    #################################
    #Fermi timezone awareness(end)  #
    #################################

    def addAddress(self, newAddress):
        self.address.append(newAddress)
        self._p_changed = 1

    def getAddresses(self):
        return self.address

    def getAddress(self):
        return self.address[0]

    def setAddress(self, address, item=0):
        self.address[item] = address
        self._p_changed = 1

    def setEmail(self, email, reindex=False):
        if reindex:
            idx = indexes.IndexesHolder().getById('email')
            idx.unindexUser(self)
            self.email = email.strip().lower()
            idx.indexUser(self)
        else:
            self.email = email.strip().lower()

    def getEmails(self):
        return [self.email] + self.getSecondaryEmails()

    def getEmail(self):
        return self.email

    def getSecondaryEmails(self):
        try:
            return self.secondaryEmails
        except:
            self.secondaryEmails = []
            return self.secondaryEmails

    def addSecondaryEmail(self, email, reindex=False):
        email = email.strip().lower()
        if email not in self.getSecondaryEmails():
            if reindex:
                idx = indexes.IndexesHolder().getById('email')
                idx.unindexUser(self)
                self.secondaryEmails.append(email)
                idx.indexUser(self)
            else:
                self.secondaryEmails.append(email)
            self._p_changed = 1

    def removeSecondaryEmail(self, email, reindex=False):
        email = email.strip().lower()
        if email in self.getSecondaryEmails():
            if reindex:
                idx = indexes.IndexesHolder().getById('email')
                idx.unindexUser(self)
                self.secondaryEmails.remove(email)
                idx.indexUser(self)
            else:
                self.secondaryEmails.remove(email)
            self._p_changed = 1

    def setSecondaryEmails(self, emailList, reindex=False):
        emailList = [email.lower().strip() for email in emailList]
        if reindex:
            idx = indexes.IndexesHolder().getById('email')
            idx.unindexUser(self)
            self.secondaryEmails = emailList
            idx.indexUser(self)
        else:
            self.secondaryEmails = emailList

    def hasEmail(self, email):
        l = [self.email] + self.getSecondaryEmails()
        return email.lower().strip() in l

    def hasSecondaryEmail(self, email):
        return email.lower().strip() in self.getSecondaryEmails()

    def addTelephone(self, newTel):
        self.telephone.append(newTel)
        self._p_changed = 1

    def getTelephone(self):
        return self.telephone[0]
    getPhone = getTelephone

    def setTelephone(self, tel, item=0):
        self.telephone[item] = tel
        self._p_changed = 1
    setPhone = setTelephone

    def getTelephones(self):
        return self.telephone

    def getSecondaryTelephones(self):
        return self.telephone[1:]

    def addFax(self, newFax):
        self.fax.append(newFax)
        self._p_changed = 1

    def setFax(self, fax, item=0):
        self.fax[item] = fax
        self._p_changed = 1

    def getFax(self):
        return self.fax[0]

    def getFaxes(self):
        return self.fax

    def addIdentity(self, newId):
        """ Adds a new identity to this Avatar.
            :param newId: a new PIdentity or inheriting object
            :type newId: PIdentity
        """
        if newId != None and (newId not in self.identities):
            self.identities.append(newId)
            self._p_changed = 1

    def removeIdentity(self, Id):
        """ Removed an identity from this Avatar.
            :param newId: a PIdentity or inheriting object
            :type newId: PIdentity
        """
        if Id in self.identities:
            self.identities.remove(Id)
            self._p_changed = 1

    def getIdentityList(self, create_identities=False):
        """ Returns a list of identities for this Avatar.
            Each identity will be a PIdentity or inheriting object
        """
        if create_identities:
            for authenticator in AuthenticatorMgr().getList():
                identities = self.getIdentityByAuthenticatorId(authenticator.getId())
                for identity in identities:
                    self.addIdentity(identity)
        return self.identities

    def getIdentityByAuthenticatorId(self, authenticatorId):
        """ Return a list of PIdentity objects given an authenticator name
            :param authenticatorId: the id of an authenticator, e.g. 'Local', 'LDAP', etc
            :type authenticatorId: str
        """
        result = []
        for identity in self.identities:
            if identity.getAuthenticatorTag() == authenticatorId:
                result.append(identity)
        if not result:
            identity = AuthenticatorMgr().getById(authenticatorId).fetchIdentity(self)
            if identity:
                result.append(identity)
        return result


    def getIdentityById(self, id, tag):
        """ Returns a PIdentity object given an authenticator name and the identity's login
            :param id: the login string for this identity
            :type id: str
            :param tag: the name of an authenticator, e.g. 'Local', 'LDAP', etc
            :type tag: str
        """

        for Id in self.identities:
            if Id.getAuthenticatorTag() == tag and Id.getLogin() == id:
                return Id
        return None

    def addRegistrant(self, n):
        if n != None and (n.getConference().getId() not in self.getRegistrants().keys()):
            self.getRegistrants()[ n.getConference().getId() ] = n
            self._p_changed = 1

    def removeRegistrant(self, r):
        if self.getRegistrants().has_key(r.getConference().getId()):

            # unlink registrant from user
            self.unlinkTo(r,'registrant')

            del self.getRegistrants()[r.getConference().getId()]
            self._p_changed = 1

    def getRegistrantList(self):
        return self.getRegistrants().values()

    def getRegistrants(self):
        try:
            if self.registrants:
                pass
        except AttributeError, e:
            self.registrants = {}
            self._p_changed = 1
        return self.registrants

    def getRegistrantById(self, confId):
        if self.getRegistrants().has_key(confId):
            return self.getRegistrants()[confId]
        return None

    def isRegisteredInConf(self, conf):
        if conf.getId() in self.getRegistrants().keys():
            return True
        for email in self.getEmails():
            registrant = conf.getRegistrantsByEmail(email)
            if registrant:
                self.addRegistrant(registrant)
                registrant.setAvatar(self)
                return True
        return False

    def hasSubmittedEvaluation(self, evaluation):
        for submission in evaluation.getSubmissions():
            if submission.getSubmitter()==self:
                return True
        return False

    def containsUser(self, avatar):
        return avatar == self
    containsMember = containsUser

    def canModify(self, aw_or_user):
        if hasattr(aw_or_user, 'getUser'):
            aw_or_user = aw_or_user.getUser()
        return self.canUserModify(aw_or_user)

    def canUserModify(self, user):
        return user == self or (user in AdminList.getInstance().getList())

    def getLocator(self):
        d = Locator()
        d["userId"] = self.getId()
        return d

    def delete(self):
        TrashCanManager().add(self)

    def recover(self):
        TrashCanManager().remove(self)

    # Room booking related

    def is_member_of_group(self, group_name):
        # Try to get the result from the cache
        try:
            if group_name in self._v_isMember.keys():
                return self._v_isMember[group_name]
        except Exception:
            self._v_isMember = {}

        groups = []
        try:
            # try to get the exact match first, which is what we expect since
            # there shouldn't be uppercase letters
            groups.append(GroupHolder().getById(group_name))
        except KeyError:
            groups = GroupHolder().match({'name': group_name}, searchInAuthenticators=False, exact=True)
            if not groups:
                groups = GroupHolder().match({'name': group_name}, exact=True)

        if groups:
            result = groups[0].containsUser(self)
            self._v_isMember[group_name] = result
            return result
        self._v_isMember[group_name] = False
        return False

    def isAdmin(self):
        """
        Convenience method for checking whether this user is an admin.
        Returns bool.
        """
        al = AdminList.getInstance()
        if al.isAdmin(self):
            return True
        return False

    @memoize_request
    def isRBAdmin(self):
        """
        Convenience method for checking whether this user is an admin for the RB module.
        Returns bool.
        """
        from indico.modules.rb import settings as rb_settings

        if self.isAdmin():
            return True
        principals = retrieve_principals(rb_settings.get('admin_principals'))
        return any(principal.containsUser(self) for principal in principals)

    @property
    @memoize_request
    def has_rooms(self):
        """Checks if the user has any rooms"""
        from indico.modules.rb.models.rooms import Room  # avoid circular import
        return Room.user_owns_rooms(self)

    @memoize_request
    def get_rooms(self):
        """Returns the rooms this user is responsible for"""
        from indico.modules.rb.models.rooms import Room  # avoid circular import
        return Room.get_owned_by(self)

    def getPersonalInfo(self):
        try:
            return self.personalInfo
        except:
            self.personalInfo = PersonalInfo()
            return self.personalInfo

    def isFieldSynced(self, field):
        if not hasattr(self, 'unlockedFields'):
            self.unlockedFields = []
        return field not in self.unlockedFields

    def setFieldSynced(self, field, synced):
        # check if the sync state is the same. also creates the list if it's missing
        if synced == self.isFieldSynced(field):
            pass
        elif synced:
            self.unlockedFields.remove(field)
            self._p_changed = 1
        else:
            self.unlockedFields.append(field)
            self._p_changed = 1

    def getNotSyncedFields(self):
        if not hasattr(self, 'unlockedFields'):
            self.unlockedFields = []
        return self.unlockedFields

    def setAuthenticatorPersonalData(self, field, value):
        fields = {'phone': {'get': self.getPhone,
                            'set': self.setPhone},
                  'fax': {'get': self.getFax,
                          'set': self.setFax},
                  'address': {'get': self.getAddress,
                              'set': self.setAddress},
                  'surName': {'get': self.getSurName,
                              'set': lambda x: self.setSurName(x, reindex=True)},
                  'firstName': {'get': self.getFirstName,
                                'set': lambda x: self.setFirstName(x, reindex=True)},
                  'affiliation': {'get': self.getAffiliation,
                                  'set': lambda x: self.setAffiliation(x, reindex=True)},
                  'email': {'get': self.getEmail,
                            'set': lambda x: self.setEmail(x, reindex=True)}}

        if not hasattr(self, 'authenticatorPersonalData'):
            self.authenticatorPersonalData = {}
        self.authenticatorPersonalData[field] = value or ''

        field_accessors = fields[field]
        if value and value != field_accessors['get']() and self.isFieldSynced(field):
            field_accessors['set'](value)
        self._p_changed = 1

    def getAuthenticatorPersonalData(self, field):
        if not hasattr(self, 'authenticatorPersonalData'):
            self.authenticatorPersonalData = {}
        return self.authenticatorPersonalData.get(field)

    def clearAuthenticatorPersonalData(self):
        self.authenticatorPersonalData = {}

    def getLang(self):
        try:
            return self._lang
        except:
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            self._lang = minfo.getLang()
            return self._lang

    def setLang(self, lang):
        self._lang =lang


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


class LoginInfo:

    def __init__(self, login, password):
        self.setLogin(login)
        self.setPassword(password)

    def setLogin(self, newLogin):
        self.login = newLogin.strip()

    def getLogin(self):
        return self.login

    def setPassword(self, newPassword):
        self.password = newPassword

    def getPassword(self):
        return self.password


class PersonalInfo(Persistent, Fossilizable):

    fossilizes(IPersonalInfoFossil)

    def __init__(self):
        self._basket = PersonalBasket()
        self._showPastEvents = False #determines if past events in category overview will be shown

        self._p_changed = 1

    def getShowPastEvents(self):
        if not hasattr(self, "_showPastEvents"):
            self._showPastEvents = False
        return self._showPastEvents

    def setShowPastEvents(self, value):
        self._showPastEvents = value

    def getBasket(self):
        return self._basket

class PersonalBasket(Persistent):

# Generic basket, for Events, Categories, Avatars, Groups and Rooms

    def __init__(self):
        self._events = {}
        self._categories = {}
        self._rooms = {}
        self._users = {}
        self._userGroups = {}
        self._p_changed = 1

    def __findDict(self, element):

        if (type(element) == MaKaC.conference.Conference):
            return self._events
        elif (type(element) == MaKaC.conference.Category):
            return self._categories
        elif (type(element) == Avatar):
            return self._users
        elif (type(element) == Group):
            return self._userGroups
        else:
            raise Exception(_("Unknown Element Type"))

    def addElement(self, element):
        basket = self.__findDict(element)
        if element.getId() not in basket:
            basket[element.getId()] = element
            self._p_changed = 1
            return True
        return False

    def deleteElement(self, element=None):
        res = self.__findDict(element).pop(element.getId(), None)

        if res == None:
            return False

        self._p_changed = 1
        return True

    def deleteUser(self, user_id):
        res = self._users.pop(user_id, None)
        self._p_changed = 1
        return res is not None

    def hasElement(self, element):
        return element.getId() in self.__findDict(element)

    def hasUserId(self, id):
        return self._users.has_key(id)

    def getUsers(self):
        return self._users
