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

from flask_multipass import IdentityInfo

from indico.legacy.common.cache import GenericCache
from indico.legacy.fossils.user import IAvatarFossil, IAvatarMinimalFossil
from indico.modules.auth import Identity
from indico.modules.users import User, logger
from indico.util.caching import memoize_request
from indico.util.fossilize import Fossilizable, fossilizes
from indico.util.locators import locator_property
from indico.util.string import encode_utf8, return_ascii, to_unicode


AVATAR_FIELD_MAP = {
    'email': 'email',
    'name': 'first_name',
    'surName': 'last_name',
    'organisation': 'affiliation'
}


class AvatarUserWrapper(Fossilizable):
    """Avatar-like wrapper class that holds a DB-stored user."""

    fossilizes(IAvatarFossil, IAvatarMinimalFossil)

    def __init__(self, user_id):
        self.id = str(user_id)

    @property
    @memoize_request
    def _original_user(self):
        # A proper user, with an id that can be mapped directly to sqlalchemy
        if isinstance(self.id, int) or self.id.isdigit():
            return User.get(int(self.id))
        # A user who had no real indico account but an ldap identifier/email.
        # In this case we try to find his real user and replace the ID of this object
        # with that user's ID.
        data = self.id.split(':')
        # TODO: Once everything is in SQLAlchemy this whole thing needs to go away!
        user = None
        if data[0] == 'LDAP':
            identifier = data[1]
            email = data[2]
            # You better have only one ldap provider or at least different identifiers ;)
            identity = Identity.find_first(Identity.provider != 'indico', Identity.identifier == identifier)
            if identity:
                user = identity.user
        elif data[0] == 'Nice':
            email = data[1]
        else:
            return None
        if not user:
            user = User.find_first(User.all_emails.contains(email))
        if user:
            self._old_id = self.id
            self.id = str(user.id)
            logger.info("Updated legacy user id (%s => %s)", self._old_id, self.id)
        return user

    @property
    @memoize_request
    def user(self):
        user = self._original_user
        if user is not None and user.is_deleted and user.merged_into_id is not None:
            while user.merged_into_id is not None:
                user = user.merged_into_user
        return user

    def getId(self):
        return str(self.user.id) if self.user else str(self.id)

    @property
    def api_key(self):
        return self.user.api_key if self.user else None

    def getStatus(self):
        return 'deleted' if not self.user or self.user.is_deleted else 'activated'

    def isActivated(self):
        # All accounts are activated during the transition period
        return True

    def isDisabled(self):
        # The user has been blocked or deleted (due to merge)
        return not self.user or self.user.is_blocked or self.user.is_deleted

    def setName(self, name, reindex=False):
        self.user.first_name = to_unicode(name)

    @encode_utf8
    def getName(self):
        return self.user.first_name if self.user else ''

    getFirstName = getName

    def setSurName(self, surname, reindex=False):
        self.user.last_name = to_unicode(surname)

    @encode_utf8
    def getSurName(self):
        return self.user.last_name if self.user else ''

    getFamilyName = getSurName

    @encode_utf8
    def getFullName(self):
        if not self.user:
            return ''
        return self.user.get_full_name(last_name_first=True, last_name_upper=True,
                                       abbrev_first_name=False, show_title=False)

    @encode_utf8
    def getStraightFullName(self, upper=True):
        if not self.user:
            return ''
        return self.user.get_full_name(last_name_first=False, last_name_upper=upper,
                                       abbrev_first_name=False, show_title=False)

    getDirectFullNameNoTitle = getStraightFullName

    @encode_utf8
    def getAbrName(self):
        if not self.user:
            return ''
        return self.user.get_full_name(last_name_first=True, last_name_upper=False,
                                       abbrev_first_name=True, show_title=False)

    @encode_utf8
    def getStraightAbrName(self):
        if not self.user:
            return ''
        return self.user.get_full_name(last_name_first=False, last_name_upper=False,
                                       abbrev_first_name=True, show_title=False)

    def setOrganisation(self, affiliation, reindex=False):
        self.user.affiliation = to_unicode(affiliation)

    @encode_utf8
    def getOrganisation(self):
        return self.user.affiliation if self.user else ''

    getAffiliation = getOrganisation

    def setTitle(self, title):
        self.user.title = to_unicode(title)

    @encode_utf8
    def getTitle(self):
        return self.user.title if self.user else ''

    def setTimezone(self, tz):
        self.user.settings.set('timezone', to_unicode(tz))

    @encode_utf8
    def getAddress(self):
        return self.user.address if self.user else ''

    def setAddress(self, address):
        self.user.address = to_unicode(address)

    def getEmails(self):
        # avoid 'stale association proxy'
        user = self.user
        return set(user.all_emails) if user else set()

    @encode_utf8
    def getEmail(self):
        return self.user.email if self.user else ''

    email = property(getEmail)

    def setEmail(self, email, reindex=False):
        self.user.email = to_unicode(email)

    def hasEmail(self, email):
        user = self.user  # avoid 'stale association proxy'
        if not user:
            return False
        return email.lower() in user.all_emails

    @encode_utf8
    def getTelephone(self):
        return self.user.phone if self.user else ''

    def getFax(self):
        # Some older code still clones fax, etc...
        # it's never shown in the interface anyway.
        return ''

    getPhone = getTelephone

    def setTelephone(self, phone):
        self.user.phone = to_unicode(phone)

    setPhone = setTelephone

    def canUserModify(self, avatar):
        if not self.user:
            return False
        return avatar.id == str(self.user.id) or avatar.user.is_admin

    @locator_property
    def locator(self):
        d = {}
        if self.user:
            d['userId'] = self.user.id
        return d

    def isAdmin(self):
        if not self.user:
            return False
        return self.user.is_admin

    @property
    def as_new(self):
        return self.user

    def __eq__(self, other):
        if not isinstance(other, (AvatarUserWrapper, User)):
            return False
        elif str(self.id) == str(other.id):
            return True
        elif self.user:
            return str(self.user.id) == str(other.id)
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(str(self.id))

    @return_ascii
    def __repr__(self):
        if self.user is None:
            return u'<AvatarUserWrapper {}: user does not exist>'.format(self.id)
        elif self._original_user.merged_into_user:
            return u'<AvatarUserWrapper {}: {} ({}) [{}]>'.format(
                self.id, self._original_user.full_name, self._original_user.email, self.user.id)
        else:
            return u'<AvatarUserWrapper {}: {} ({})>'.format(self.id, self.user.full_name, self.user.email)


class AvatarProvisionalWrapper(Fossilizable):
    """
    Wraps provisional data for users that are not in the DB yet
    """

    fossilizes(IAvatarFossil, IAvatarMinimalFossil)

    def __init__(self, identity_info):
        self.identity_info = identity_info
        self.data = identity_info.data

    def getId(self):
        return u"{}:{}".format(self.identity_info.provider.name, self.identity_info.identifier)

    id = property(getId)

    @encode_utf8
    def getEmail(self):
        return self.data['email']

    def getEmails(self):
        return [self.data['email']]

    @encode_utf8
    def getFirstName(self):
        return self.data.get('first_name', '')

    @encode_utf8
    def getFamilyName(self):
        return self.data.get('last_name', '')

    @encode_utf8
    def getStraightFullName(self, upper=False):
        last_name = to_unicode(self.data.get('last_name', ''))
        if upper:
            last_name = last_name.upper()
        return u'{} {}'.format(to_unicode(self.data.get('first_name', '')), last_name)

    def getTitle(self):
        return ''

    @encode_utf8
    def getTelephone(self):
        return self.data.get('phone', '')

    getPhone = getTelephone

    @encode_utf8
    def getOrganisation(self):
        return self.data.get('affiliation', '')

    getAffiliation = getOrganisation

    def getFax(self):
        return None

    def getAddress(self):
        return u''

    @return_ascii
    def __repr__(self):
        return u'<AvatarProvisionalWrapper {}: {} ({first_name} {last_name})>'.format(
            self.identity_info.provider.name,
            self.identity_info.identifier,
            **self.data.to_dict())


def search_avatars(criteria, exact=False, search_externals=False):
    from indico.modules.users.util import search_users

    if not any(criteria.viewvalues()):
        return []

    def _process_identities(obj):
        if isinstance(obj, IdentityInfo):
            GenericCache('pending_identities').set('{}:{}'.format(obj.provider.name, obj.identifier), obj.data)
            return AvatarProvisionalWrapper(obj)
        else:
            return obj.as_avatar

    results = search_users(exact=exact, external=search_externals,
                           **{AVATAR_FIELD_MAP[k]: v for (k, v) in criteria.iteritems() if v})

    return [_process_identities(obj) for obj in results]
