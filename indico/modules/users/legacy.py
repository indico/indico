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

from persistent import Persistent

from functools import wraps

from indico.modules.users.models.users import User
from indico.util.caching import memoize_request
from indico.util.fossilize import fossilizes, Fossilizable
from indico.util.string import to_unicode, return_ascii
from indico.util.user import retrieve_principals

from MaKaC.common.Locators import Locator
from MaKaC.fossils.user import IAvatarFossil, IAvatarMinimalFossil


def encode_utf8(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        return f(*args, **kwargs).encode('utf-8')

    return _wrapper


class AvatarUserWrapper(Persistent, Fossilizable):
    """Avatar-like wrapper class that holds a DB-stored user."""

    fossilizes(IAvatarFossil, IAvatarMinimalFossil)

    def __init__(self, user_id):
        self.id = str(user_id)

    @property
    @memoize_request
    def user(self):
        return User.get(int(self.id))

    def getId(self):
        return self.id

    @property
    def api_key(self):
        return self.user.api_key

    def linkTo(self, obj, role):
        # deleted users shouldn't be able to be linked
        # TODO: log deleted users?

        if not self.user.is_deleted:
            self.user.link_to(obj, role)

    def unlinkTo(self, obj, role):
        # deleted users shouldn't be able to be linked
        # TODO: log deleted users?

        if not self.user.is_deleted:
            self.user.unlink_to(obj, role)

    def getLinkedTo(self):
        return None

    def getStatus(self):
        return 'deleted' if self.user.is_deleted else 'activated'

    def isActivated(self):
        # All accounts are activated during the transition period
        return True

    def isDisabled(self):
        # The user has been blocked or deleted (due to merge)
        return self.user.is_blocked or self.user.is_deleted

    def setName(self, name, reindex=False):
        self.user.first_name = to_unicode(name)

    @encode_utf8
    def getName(self):
        return self.user.first_name

    getFirstName = getName

    def setSurName(self, surname, reindex=False):
        self.user.last_name = to_unicode(surname)

    @encode_utf8
    def getSurName(self):
        return self.user.last_name

    getFamilyName = getSurName

    @encode_utf8
    def getFullName(self):
        return self.user.get_full_name(last_name_first=True, last_name_upper=True,
                                       abbrev_first_name=False, show_title=False)

    @encode_utf8
    def getStraightFullName(self, upper=True):
        return self.user.get_full_name(last_name_first=False, last_name_upper=True,
                                       abbrev_first_name=False, show_title=False)

    getDirectFullNameNoTitle = getStraightFullName

    @encode_utf8
    def getAbrName(self):
        return self.user.get_full_name(last_name_first=True, last_name_upper=False,
                                       abbrev_first_name=True, show_title=False)

    @encode_utf8
    def getStraightAbrName(self):
        return self.user.get_full_name(last_name_first=False, last_name_upper=False,
                                       abbrev_first_name=True, show_title=False)

    def setOrganisation(self, affiliation, reindex=False):
        self.user.affiliation = to_unicode(affiliation)

    @encode_utf8
    def getOrganisation(self):
        return self.user.affiliation

    getAffiliation = getOrganisation

    def setTitle(self, title):
        self.user.title = to_unicode(title)

    @encode_utf8
    def getTitle(self):
        return self.user.title

    def setTimezone(self, tz):
        self.user.settings.set('timezone', to_unicode(tz))

    @encode_utf8
    def getTimezone(self):
        return self.user.settings.get('timezone')

    def getDisplayTZMode(self):
        return 'MyTimezone' if self.user.settings.get('force_timezone') else 'Event Timezone'

    def setDisplayTZMode(self, display_tz='Event Timezone'):
        self.user.settings.set('force_timezone', display_tz == 'MyTimezone')

    @encode_utf8
    def getAddresses(self):
        return [self.user.address]

    @encode_utf8
    def getAddress(self):
        return self.user.address

    def setAddress(self, address):
        self.user.address = to_unicode(address)

    def getEmails(self):
        # avoid 'stale association proxy'
        user = self.user
        return set(user.all_emails)

    @encode_utf8
    def getEmail(self):
        return self.user.email

    def setEmail(self, email, reindex=False):
        self.user.email = to_unicode(email)

    def getSecondaryEmails(self):
        return self.user.secondary_emails

    def addSecondaryEmail(self, email, reindex=False):
        return self.user.secondary_emails.add(to_unicode(email.strip().lower()))

    def removeSecondaryEmail(self, email, reindex=False):
        self.user.secondary_emails.remove(email)

    def setSecondaryEmails(self, emails, reindex=False):
        self.user.secondary_emails = {to_unicode(email.strip().lower()) for email in emails}

    def hasEmail(self, email):
        return email.lower() in self.user.all_emails

    def hasSecondaryEmail(self, email):
        return email.lower() in self.user.secondary_emails

    @encode_utf8
    def getTelephone(self):
        return self.user.phone

    def getFax(self):
        # Some older code still clones fax, etc...
        # it's never shown in the interface anyway.
        return ''

    getPhone = getTelephone

    def setTelephone(self, phone):
        self.user.phone = to_unicode(phone)

    setPhone = setTelephone

    def clearAuthenticatorPersonalData(self):
        pass

    def setAuthenticatorPersonalData(self, field, value):
        pass

    def getIdentityById(self, id, tag):
        return True

    def addRegistrant(self, r):
        # This doesn't seem to be needed, as it is stored in linkedTo as well
        # TODO: Check that it can be deleted
        pass

    def removeRegistrant(self, r):
        # This doesn't seem to be needed, as it is stored in linkedTo as well
        # TODO: Check that it can be deleted
        pass

    def isRegisteredInConf(self, conf):
        return any(obj for obj in self.user.get_linked_objects('registration', 'registrant')
                   if obj.getConference() == conf)

    def getRegistrantById(self, conf_id):
        return next(obj for obj in self.user.get_linked_objects('registration', 'registrant')
                    if obj.getConference().id == conf_id)

    def hasSubmittedEvaluation(self, evaluation):
        for submission in evaluation.getSubmissions():
            submitter = submission.getSubmitter()
            if submitter and submitter.id == self.id:
                return True
        return False

    def containsUser(self, avatar):
        return avatar.id == self.id

    containsMember = containsUser

    def canModify(self, aw_or_user):
        if hasattr(aw_or_user, 'getUser'):
            aw_or_user = aw_or_user.getUser()
        return self.canUserModify(aw_or_user)

    def canUserModify(self, avatar):
        return avatar.id == self.id or avatar.user.is_admin

    def getLocator(self):
        d = Locator()
        d["userId"] = self.id
        return d

    def is_member_of_group(self, group_name):
        from MaKaC.user import GroupHolder
        try:
            groups = [GroupHolder().getById(group_name)]
        except KeyError:
            groups = GroupHolder().match({'name': group_name}, searchInAuthenticators=False, exact=True)
            if not groups:
                groups = GroupHolder().match({'name': group_name}, exact=True)

        return groups and groups[0].containsUser(self)

    def isAdmin(self):
        return self.user.is_admin

    @memoize_request
    def isRBAdmin(self):
        """
        Convenience method for checking whether this user is an admin for the RB module.
        Returns bool.
        """
        from indico.modules.rb import settings as rb_settings

        if self.user.is_admin:
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

    @encode_utf8
    def getLang(self):
        return self.user.settings.get('lang')

    def setLang(self, lang):
        self.user.settings.set('lang', to_unicode(lang))

    @return_ascii
    def __repr__(self):
        return u'<AvatarUserWrapper {}: {} ({})>'.format(self.id, self.user.full_name, self.user.email)
