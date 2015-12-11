# -*- coding: utf-8 -*-
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import time
import uuid
from flask import session

from MaKaC.common import indexes, info
from MaKaC.common.cache import GenericCache
from MaKaC.common.fossilize import fossilize
from MaKaC.common.utils import validMail
from MaKaC.fossils.user import IAvatarAllDetailsFossil, IAvatarFossil
from MaKaC.rb_location import CrossLocationQueries
from MaKaC.services.implementation.base import LoggedOnlyService, AdminService, ParameterManager, ServiceBase
from MaKaC.services.interface.rpc.common import (ServiceError, ServiceAccessError, NoReportError, Warning,
                                                 ResultWithWarning)
from MaKaC.user import AvatarHolder
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.webinterface.common.timezones import TimezoneRegistry
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
from indico.core.config import Config
from indico.util.i18n import _, getLocaleDisplayNames, availableLocales
from indico.util.redis import avatar_links
from indico.web.flask.util import url_for
from indico.web.http_api.auth import APIKey


class UserComparator(object):

    @staticmethod
    def cmpUsers(x, y):
        cmpResult = cmp(x["familyName"].lower(), y["familyName"].lower())
        if cmpResult == 0:
            cmpResult = cmp(x["firstName"].lower(), y["firstName"].lower())
        return cmpResult

    @staticmethod
    def cmpGroups(x, y):
        return cmp(x["name"].lower(), y["name"].lower())

class UserBaseService(LoggedOnlyService):

    def _checkParams(self):
        self._pm = ParameterManager(self._params)
        userId = self._pm.extract("userId", None)
        if userId is not None:
            ah = AvatarHolder()
            self._target = ah.getById(userId)
        else:
            raise ServiceError("ERR-U5", _("User id not specified"))

class UserModifyBase(UserBaseService):

    def _checkProtection(self):
        LoggedOnlyService._checkProtection(self)
        if self._aw.getUser():
            if not self._target.canModify( self._aw ):
                raise ServiceError("ERR-U6", _("You are not allowed to perform this request"))
        else:
            raise ServiceError("ERR-U7", _("You are currently not authenticated. Please log in again."))


class UserListEvents(LoggedOnlyService):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)

        self._time = self._params.get('time', None)
        self._target = self.getAW().getUser()

    def __exportElemDataFactory(self, moment):
        return lambda elem: {
            'id': elem[0].getId(),
            'title': elem[0].getTitle(),
            'roles': [elem[1]],
            'timestamp':time.mktime(elem[0].getStartDate().timetuple()),
            'startDate':str(elem[0].getStartDate().strftime("%d/%m/%Y")),
            'endDate':str(elem[0].getEndDate().strftime("%d/%m/%Y")),
            'startTime':str(elem[0].getStartDate().strftime("%H:%M")),
            'endTime':str(elem[0].getEndDate().strftime("%H:%M")),
            'type': moment,
            'evtType': elem[0].getVerboseType()
        }

    def _getAnswer( self):

        events = []

        self._target.getTimedLinkedEvents().sync()

        if (not self._time) or self._time == 'past':
            events.extend( map( self.__exportElemDataFactory('past'),
                               self._target.getTimedLinkedEvents().getPast()))

        if (not self._time) or self._time == 'present':
            events.extend( map(self.__exportElemDataFactory('present'),
                              self._target.getTimedLinkedEvents().getPresent()))

        if (not self._time) or self._time == 'future':
            events.extend( map(self.__exportElemDataFactory('future'),
                              self._target.getTimedLinkedEvents().getFuture()))

        jsonData = {}

        for event in events:
            if jsonData.has_key(event['id']):
                jsonData[event['id']]['roles'].append(event['roles'][0])
            else:
                jsonData[event['id']] = event

        return jsonData

class UserBasketBase:

    def _checkParams(self):
        ServiceBase._checkParams(self)
        self._pm = ParameterManager(self._params)
        userId = self._pm.extract("userId", pType=str, allowEmpty=True)
        if userId is not None:
            ah = AvatarHolder()
            self._target = ah.getById(userId)
        else:
            self._target = self._aw.getUser()

    def _checkProtection(self):
        if not self._aw.getUser():
            raise ServiceAccessError(_("You are currently not authenticated. Please log in again."))
        if not self._target.canUserModify(self._aw.getUser()):
            raise ServiceAccessError('Access denied')

class UserAddToBasket(LoggedOnlyService, UserBasketBase):

    def _checkParams(self):
        UserBasketBase._checkParams(self)

        self._userList = []
        for userData in self._params['value']:
            self._userList.append(AvatarHolder().getById(userData['id']))

    def _getAnswer(self):

        ##### Why not?
        #if (self._target in self._userList):
        #    raise ServiceError("ERR-U3","Trying to add user to his own favorites!")

        if (self._userList == []):
            raise ServiceError("ERR-U0","No users specified!")

        for user in self._userList:
            #we do not care if the user is already in the favourites
            self._target.getPersonalInfo().getBasket().addElement(user)

    def _checkProtection(self):
        LoggedOnlyService._checkProtection(self)
        UserBasketBase._checkProtection(self)


class UserRemoveFromBasket(LoggedOnlyService, UserBasketBase):
    def _checkParams(self):
        UserBasketBase._checkParams(self)
        self._userData = self._params['value']

    def _getAnswer( self):
        for obj in self._userData:
            if not self._target.getPersonalInfo().getBasket().deleteUser(obj['id']):
                raise ServiceError("ERR-U0","Element '%s' not found in favorites!" % obj['id'])

    def _checkProtection(self):
        LoggedOnlyService._checkProtection(self)
        UserBasketBase._checkProtection(self)

class UserListBasket(UserBasketBase, ServiceBase):

    """
    Service that lists the users belonging to the the user's "favorites"
    Should return None in case the user is not logged in.
    """

    def _checkParams(self):
        ServiceBase._checkParams(self)
        UserBasketBase._checkParams(self)
        self._allDetails = self._params.get("allDetails", False)

    def _getAnswer( self):

        if self._target:
            users = self._target.getPersonalInfo().getBasket().getUsers().values()

            if self._allDetails:
                fossilToUse = IAvatarAllDetailsFossil
            else:
                fossilToUse = IAvatarFossil

            fossilizedResult = fossilize(users, fossilToUse)
            fossilizedResult.sort(cmp=UserComparator.cmpUsers)
            return fossilizedResult

        else:
            return None

class UserGetEmail(LoggedOnlyService):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)
        self._target = self.getAW().getUser()


    def _getAnswer( self):
        if self._target:
            return self._target.getEmail()
        else:
            raise ServiceError("ERR-U4","User is not logged in")

class UserGetTimezone(ServiceBase):

    def _getAnswer(self):
        if self.getAW().getUser():
            tz = self.getAW().getUser().getTimezone()
        else:
            tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        return tz


class UserGetSessionTimezone(ServiceBase):

    def _getAnswer(self):
        return session.timezone


class UserGetSessionLanguage(ServiceBase):

    def _getAnswer(self):
        if self.getAW().getSession():
            return self.getAW().getSession().getLang()
        else:
            minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
            return minfo.getLang()

class UserCanBook(LoggedOnlyService):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)
        self._user = self.getAW().getUser()
        self._roomID = int(self._params.get("roomID", ""))
        self._roomLocation = self._params.get("roomLocation", "").replace("+"," ")
        self._room = CrossLocationQueries.getRooms(roomID = self._roomID, location = self._roomLocation)

    def _getAnswer( self):
        if self._user and self._room:
            if not self._room.isActive and not self._user.isAdmin():
                return False
            if not self._room.canBook( self._user ) and not self._room.canPrebook( self._user ):
                return False
            return True
        return False

class UserShowPastEvents(UserModifyBase):

    def _getAnswer( self):
        self._target.getPersonalInfo().setShowPastEvents(True)
        return True


class UserHidePastEvents(UserModifyBase):

    def _getAnswer( self):
        self._target.getPersonalInfo().setShowPastEvents(False)
        return True

class UserGetLanguages(UserBaseService):

    def _getAnswer( self):
        return getLocaleDisplayNames()


class UserSetLanguage(UserModifyBase):

    def _checkParams(self):
        UserModifyBase._checkParams(self)
        self._lang = self._params.get("lang",None)

    def _getAnswer( self):
        if self._lang and self._lang in availableLocales:
            self._target.setLang(self._lang)
            return True
        else:
            return False


class UserGetTimezones(UserBaseService):

    def _getAnswer( self):
        return TimezoneRegistry.getList()


class UserSetTimezone(UserModifyBase):

    def _checkParams(self):
        UserModifyBase._checkParams(self)
        self._tz = self._params.get("tz",None)

    def _getAnswer( self):
        if self._tz and self._tz in TimezoneRegistry.getList():
            self._target.setTimezone(self._tz)
            return True
        return False


class UserGetDisplayTimezones(UserBaseService):

    def _getAnswer( self):
        if self._target.getDisplayTZMode() == "Event Timezone":
            tzMode = ["Event Timezone", "MyTimezone"]
        else:
            tzMode = ["MyTimezone", "Event Timezone"]
        return tzMode


class UserSetDisplayTimezone(UserModifyBase):

    def _checkParams(self):
        UserModifyBase._checkParams(self)
        self._tzMode = self._params.get("tzMode",None)

    def _getAnswer( self):
        if self._tzMode and self._tzMode in ["Event Timezone", "MyTimezone"]:
            self._target.setDisplayTZMode(self._tzMode)
            return True
        return False


class UserPersonalDataBase(UserModifyBase):

    _dataTypes = ["title", "surName", "name", "fullName", "straightFullName", "organisation",
                  "email", "secondaryEmails", "address", "telephone", "fax"]

    def _checkParams(self):
        self._pm = ParameterManager(self._params)
        userId = self._pm.extract("userId", None)
        if userId is not None:
            ah = AvatarHolder()
            self._user = self._avatar = self._target = ah.getById(userId)
        else:
            raise ServiceError("ERR-U5", _("User id not specified"))
        self._dataType = self._pm.extract("dataType", pType=str, allowEmpty=False)
        if self._dataType not in self._dataTypes:
            raise ServiceError("ERR-U7", _("Data argument is not valid"))


class UserSetPersonalData(UserPersonalDataBase):

    def __init__(self, *args, **kwargs):
        UserPersonalDataBase.__init__(self, *args, **kwargs)
        self.process_data = {
            'title': self._process_title,
            'surName': self._process_surname,
            'name': self._process_name,
            'organisation': self._process_organisation,
            'email': self._process_email,
            'secondaryEmails': self._process_secondary_emails,
            'telephone': self._process_telephone,
            'fax': self._process_fax,
            'address': self._process_address
        }

    def _checkParams(self):
        UserPersonalDataBase._checkParams(self)
        if self._dataType in set(["surName", "name", "organisation", "email", "secondaryEmails"]):
            # empty only for secondary emails
            self._value = self._pm.extract("value", pType=str, allowEmpty=self._dataType == "secondaryEmails")

        else:
            self._value = self._pm.extract("value", pType=str, allowEmpty=True)

    def _generate_emails_list(self, value):
        value = value.replace(' ', ',').replace(';', ',')  # replace to have only one separator
        return [email for email in value.split(',') if email]

    def _confirm_email_address(self, email, data_type):
        email = email.strip().lower()

        if not validMail(email):
            raise NoReportError(_("Invalid email address: {0}").format(email))

        # Prevent adding the primary email as a secondary email
        if data_type == 'secondaryEmails' and email == self._avatar.getEmail():
            raise NoReportError(_("{0} is already the primary email address "
                                  "and cannot be used as a secondary email address.").format(email))

        # When setting a secondary email as primary, set it automatically and
        # re-index the user's emails without sending a confirmation email
        # (We assume the secondary emails are valid)
        if data_type == 'email' and email in self._avatar.getSecondaryEmails():
            self._avatar.removeSecondaryEmail(email)
            self._avatar.setEmail(email, reindex=True)
            return False

        existing = AvatarHolder().match({'email': email}, searchInAuthenticators=False)
        if existing:
            if any(av for av in existing if av != self._avatar):
                raise NoReportError(_("The email address {0} is already used by another user.").format(email))
            else:  # The email is already set correctly for the user: Do nothing
                return False

        # New email address
        token_storage = GenericCache('confirm-email')
        data = {'email': email, 'data_type': data_type, 'uid': self._avatar.getId()}
        token = str(uuid.uuid4())
        while token_storage.get(token):
            token = str(uuid.uuid4())
        token_storage.set(token, data, 24 * 3600)
        url = url_for('user.confirm_email', token=token, _external=True, _secure=True)

        if data_type == 'email':
            body_format = _(
                "Dear {0},\n"
                "You requested to change your account's primary email address.\n"
                "Please open the link below within 24 hours to confirm and activate this email address:\n"
                "\n{1}\n\n"
                "--\n"
                "Indico"
            )
        else:
            body_format = _(
                "Dear {0},\n"
                "You added this email address to your account's secondary emails list.\n"
                "Please open the link below within 24 hours to confirm and activate this email address:\n"
                "\n{1}\n\n"
                "--\n"
                "Indico"
            )

        confirmation = {
            'toList': [email],
            'fromAddr': Config.getInstance().getSupportEmail(),
            'subject': _("[Indico] Verify your email address"),
            'body': body_format.format(self._avatar.getFirstName(), url)
        }

        # Send mail with template message and link
        GenericMailer.send(GenericNotification(confirmation))
        return True

    def _getAnswer(self):
        if not self._user:
            raise ServiceError("ERR-U5", _("User id not specified"))

        getter_name = "get%s%s" % (self._dataType[0].upper(), self._dataType[1:])
        setter_name = "set%s%s" % (self._dataType[0].upper(), self._dataType[1:])
        setter = self.process_data.get(self._dataType, getattr(self._user, setter_name))

        ret_val = setter(self._value)
        if ret_val is not None:
            return ret_val
        return getattr(self._user, getter_name)()

    def _process_title(self, new_title):
        if self._value in TitlesRegistry().getList():
            self._user.setTitle(new_title)
        else:
            raise NoReportError(_("Invalid title value"))

    def _process_surname(self, new_surname):
        self._user.setFieldSynced('surName', False)
        self._user.setSurName(new_surname, reindex=True)

    def _process_name(self, new_name):
        self._user.setFieldSynced('firstName', False)
        self._user.setName(new_name, reindex=True)

    def _process_organisation(self, new_organisation):
        self._user.setFieldSynced('affiliation', False)
        self._user.setOrganisation(new_organisation, reindex=True)

    def _process_email(self, new_email):
        # Check if there is any user with this email address
        confirmation_sent = self._confirm_email_address(new_email, 'email')

        if confirmation_sent:
            warning = Warning(
                _("New primary email address"),
                _("We have sent a verification email to: {0}. "
                  "Once the address is verified, it will be set as your primary email address.").format(new_email)
            )
        else:  # Then the email has been set
            warning = Warning(_("New primary email address set"),
                              _("{0} has been set as your primary email address.").format(new_email))

        return ResultWithWarning(self._user.getEmail(), warning).fossilize()

    def _process_secondary_emails(self, value):
        emails_to_confirm = []
        emails_to_set = []
        invalid_email_errors = []
        secondary_emails = self._generate_emails_list(value)
        for email in secondary_emails:
            try:
                if self._confirm_email_address(email, 'secondaryEmails'):
                    emails_to_confirm.append(email)
                else:
                    emails_to_set.append(email)
            except NoReportError as e:
                invalid_email_errors.append(e.message)

        self._avatar.setSecondaryEmails(emails_to_set, reindex=True)
        # Generate confirmation message
        if not emails_to_confirm:
            confirmation_msg = None
        elif len(emails_to_confirm) == 1:
            email = emails_to_confirm[0]
            confirmation_title = _("New secondary email address")
            confirmation_msg = _("We have sent a verification email to: {0}. "
                                 "Once the address is verified, it will be shown on your profile.").format(email)
        else:
            confirmation_title = _("New secondary email addresses")
            confirmation_msg = _(
                "We have sent verification emails to: {0}. "
                "Once an address is verified, it will be shown on your profile.").format(', '.join(emails_to_confirm))

        # Generate error message
        if len(invalid_email_errors) == 1:
            error_msg = invalid_email_errors[0]
        elif invalid_email_errors:
            error_msg = ' '.join([_("Some email addresses were not set.")] + invalid_email_errors)
        else:
            error_msg = None

        if error_msg and confirmation_msg:
            return ResultWithWarning(
                ', '.join(self._user.getSecondaryEmails()),
                Warning(_("Warning, not all addresses were set"), ' '.join([error_msg, confirmation_msg]))
            ).fossilize()
        elif error_msg:
            raise NoReportError(error_msg)
        elif confirmation_msg:
            return ResultWithWarning(', '.join(self._user.getSecondaryEmails()),
                                     Warning(confirmation_title, confirmation_msg)).fossilize()

        return ', '.join(self._user.getSecondaryEmails())

    def _process_telephone(self, value):
        self._user.setFieldSynced('phone', False)
        self._user.setTelephone(value)

    def _process_fax(self, value):
        self._user.setFieldSynced('fax', False)
        self._user.setFax(value)

    def _process_address(self, value):
        self._user.setFieldSynced('address', False)
        self._user.setAddress(value)


class UserSyncPersonalData(UserPersonalDataBase):
    _dataTypes = ["surName", "firstName", "affiliation", "phone", "fax", "address"]

    def _getAnswer(self):
        if self._dataType == 'name':
            self._dataType = 'firstName'
        self._user.setFieldSynced(self._dataType, True)
        val = self._user.getAuthenticatorPersonalData(self._dataType)
        if val:
            setter = "set%s%s" % (self._dataType[0].upper(), self._dataType[1:])
            getattr(self._user, setter)(val)
        return dict(val=val)


class UserAcceptSecondaryEmail(UserModifyBase):

    def _checkParams(self):
        UserModifyBase._checkParams(self)
        self._secondaryEmail = self._params.get("secondaryEmail", None)

    def _getAnswer(self):
        av = AvatarHolder().match({"email": self._secondaryEmai}, forceWithoutExtAuth=True)
        if av and av[0] != self._user:
            raise NoReportError(_("The email address %s is already used by another user.") % self._secondaryEmai)
        self._user.addSecondaryEmail(self._secondaryEmail, reindex=True)
        return True


class UserSetPersistentSignatures(UserModifyBase):

    def _checkParams(self):
        UserModifyBase._checkParams(self)
        if self._target == None:
            raise ServiceAccessError((_("The user with does not exist")))

    def _getAnswer(self):
        ak = self._target.getAPIKey()
        ak.setPersistentAllowed(not ak.isPersistentAllowed())
        return ak.isPersistentAllowed()


class UserCreateKeyEnablePersistent(LoggedOnlyService):

    def _checkParams(self):
        LoggedOnlyService._checkParams(self)
        self._target = self._avatar = self.getAW().getUser()
        pm = ParameterManager(self._params)
        self._enablePersistent = pm.extract("enablePersistent", bool, False, False)

    def _getAnswer( self):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        ak = APIKey(self._avatar)
        ak.create()
        if minfo.isAPIPersistentAllowed() and self._enablePersistent:
            ak.setPersistentAllowed(True)
        return True


class UserRefreshRedisLinks(AdminService):
    def _checkParams(self):
        AdminService._checkParams(self)
        self._pm = ParameterManager(self._params)
        userId = self._pm.extract("userId", pType=str, allowEmpty=True)
        if userId is not None:
            ah = AvatarHolder()
            self._avatar = ah.getById(userId)
        else:
            self._avatar = self._aw.getUser()

    def _getAnswer(self):
        avatar_links.delete_avatar(self._avatar)  # clean start
        avatar_links.init_links(self._avatar)


methodMap = {
    "event.list": UserListEvents,
    "favorites.addUsers": UserAddToBasket,
    "favorites.removeUser": UserRemoveFromBasket,
    "favorites.listUsers": UserListBasket,
    "data.email.get": UserGetEmail,
    "timezone.get": UserGetTimezone,
    "session.timezone.get": UserGetSessionTimezone,
    "session.language.get": UserGetSessionLanguage,
    "canBook": UserCanBook,
    "showPastEvents": UserShowPastEvents,
    "hidePastEvents": UserHidePastEvents,
    "getLanguages": UserGetLanguages,
    "setLanguage": UserSetLanguage,
    "getTimezones": UserGetTimezones,
    "setTimezone": UserSetTimezone,
    "getDisplayTimezones": UserGetDisplayTimezones,
    "setDisplayTimezone": UserSetDisplayTimezone,
    "setPersonalData": UserSetPersonalData,
    "syncPersonalData": UserSyncPersonalData,
    "acceptSecondaryEmail": UserAcceptSecondaryEmail,
    "togglePersistentSignatures": UserSetPersistentSignatures,
    "createKeyAndEnablePersistent": UserCreateKeyEnablePersistent,
    "refreshRedisLinks": UserRefreshRedisLinks
}
