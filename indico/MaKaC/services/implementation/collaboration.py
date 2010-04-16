# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from datetime import timedelta
from MaKaC.services.implementation.base import ParameterManager, AdminService
from MaKaC.services.implementation.conference import ConferenceModifBase
from MaKaC.common.PickleJar import DictPickler
from MaKaC.plugins.Collaboration.base import CollaborationException, CollaborationServiceException
from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin,\
    RCCollaborationPluginAdmin, RCVideoServicesManager
from MaKaC.i18n import _
from MaKaC.common.indexes import IndexesHolder
from MaKaC.plugins.base import PluginsHolder
from MaKaC.common.timezoneUtils import nowutc, setAdjustedDate
from MaKaC.common.utils import parseDateTime
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.webinterface.user import UserListModificationBase,\
    UserModificationBase
from MaKaC.common.fossilize import fossilize


## Base classes
class CollaborationBase(ConferenceModifBase):
    """ This base class stores the _CSBookingManager attribute
        so that inheriting classes can use it.
    """
    def _checkParams(self):
        ConferenceModifBase._checkParams(self) #sets self._target = self._conf = the Conference object
        self._checkCollaborationEnabled()
        self._CSBookingManager = self._conf.getCSBookingManager()

    def _checkCollaborationEnabled(self):
        """ Checks if the Collaboration plugin system is active
        """
        if not PluginsHolder().hasPluginType("Collaboration"):
            raise CollaborationServiceException("Collaboration plugin system is not active")

    def _checkCanManagePlugin(self, plugin):
        isAdminOnlyPlugin = CollaborationTools.isAdminOnlyPlugin(plugin)

        hasAdminRights = RCCollaborationAdmin.hasRights(self) or \
                         RCCollaborationPluginAdmin.hasRights(self, None, [plugin])

        if not hasAdminRights and isAdminOnlyPlugin:
            raise CollaborationException(_("Cannot acces service of admin-only plugin if user is not admin, for event: ") + str(self._conf.getId()) + _(" with the service ") + str(self.__class__) )

        elif not hasAdminRights and not RCVideoServicesManager.hasRights(self, [plugin]):
            #we check if it's an event creator / manager (this will call ConferenceModifBase._checkProtection)
            CollaborationBase._checkProtection(self)

    def process(self):
        try:
            return ConferenceModifBase.process(self)
        except CollaborationException, e:
            raise CollaborationServiceException(e.getMsg(), str(e.getInner()))

class CollaborationBookingModifBase(CollaborationBase):
    """ Base class for services that are passed a booking id.
        It is stored in self._bookingId
    """
    def _checkParams(self):
        CollaborationBase._checkParams(self)
        if self._params.has_key('bookingId'):
            self._bookingId = self._params['bookingId']
            booking = self._CSBookingManager.getBooking(self._bookingId)
            self._bookingType = booking.getType()
            self._bookingPlugin = booking.getPlugin()

        else:
            raise CollaborationException(_("Booking id not set when trying to modify a booking on meeting ") + str(self._conf.getId()) + _(" with the service ") + str(self.__class__) )

    def _checkProtection(self):
        CollaborationBase._checkCanManagePlugin(self, self._bookingPlugin)

class CollaborationAdminBookingModifBase(CollaborationBookingModifBase):
    """ Base class for services on booking objects that can only be requested by Server Admins,
        Video Services Admins, or Plugin admins, such as accept or reject a request, etc.
    """

    def _checkProtection(self):
        if not RCCollaborationAdmin.hasRights(self) and not RCCollaborationPluginAdmin.hasRights(self, None, [self._bookingPlugin]):
            raise CollaborationException(_("You don't have the rights to perform this operation on this booking"))

class AdminCollaborationBase(AdminService):
    """ Base class for admin services in the Video Services Overview page, not directed towards a specific booking.
    """

    def _checkParams(self):
        AdminService._checkParams(self)
        if not PluginsHolder().hasPluginType("Collaboration"):
            raise CollaborationServiceException(_("Collaboration plugin system is not active"))

    def _checkProtection(self):
        if not RCCollaborationAdmin.hasRights(self, None):
            AdminService._checkProtection(self)

##! End of base classes


class CollaborationCreateCSBooking(CollaborationBase):
    """ Adds a new booking
    """
    def _checkParams(self):
        CollaborationBase._checkParams(self)

        if 'type' in self._params:
            self._type = self._params['type']
        else:
            raise CollaborationException(_("type parameter not set when trying to create a booking on meeting ") + str(self._conf.getId() ))

        if 'bookingParams' in self._params:
            pm = ParameterManager(self._params)
            self._bookingParams = pm.extract("bookingParams", pType=dict, allowEmpty = True)
        else:
            raise CollaborationException(_("Custom parameters for plugin ") + str(self._type) + _(" not set when trying to create a booking on meeting ") + str(self._conf.getId() ))

    def _checkProtection(self):
        CollaborationBase._checkCanManagePlugin(self, self._type)

    def _getAnswer(self):
        return fossilize(self._CSBookingManager.createBooking(self._type, bookingParams = self._bookingParams),
                         None, tz = self._conf.getTimezone())

class CollaborationRemoveCSBooking(CollaborationBookingModifBase):
    """ Removes a booking
    """
    def _getAnswer(self):
        return fossilize(self._CSBookingManager.removeBooking(self._bookingId),
                         None, tz = self._conf.getTimezone())


class CollaborationEditCSBooking(CollaborationBookingModifBase):
    """ Edits a booking
    """
    def _checkParams(self):
        CollaborationBookingModifBase._checkParams(self)

        if self._params.has_key('bookingParams'):
            pm = ParameterManager(self._params)
            self._bookingParams = pm.extract("bookingParams", pType=dict, allowEmpty = True)
        else:
            raise CollaborationException(_("Custom parameters for booking ") + str(self._bookingId) + _(" not set when trying to edit a booking on meeting ") + str(self._conf.getId() ))

    def _getAnswer(self):
        return fossilize(self._CSBookingManager.changeBooking(self._bookingId, self._bookingParams),
                         None, tz = self._conf.getTimezone())


class CollaborationStartCSBooking(CollaborationBookingModifBase):
    """ Performs server-side actions when a booking is started
    """
    def _getAnswer(self):
        return fossilize(self._CSBookingManager.startBooking(self._bookingId),
                         None, tz = self._conf.getTimezone())

class CollaborationStopCSBooking(CollaborationBookingModifBase):
    """ Performs server-side actions when a booking is stopped
    """
    def _getAnswer(self):
        return fossilize(self._CSBookingManager.stopBooking(self._bookingId),
                                  timezone = self._conf.getTimezone())

class CollaborationCheckCSBookingStatus(CollaborationBookingModifBase):
    """ Performs server-side actions when a booking's status is checked
    """
    def _getAnswer(self):
        return fossilize(self._CSBookingManager.checkBookingStatus(self._bookingId),
                         None, tz = self._conf.getTimezone())

class CollaborationAcceptCSBooking(CollaborationAdminBookingModifBase):
    """ Performs server-side actions when a booking / request is accepted
    """
    def _getAnswer(self):
        return fossilize(self._CSBookingManager.acceptBooking(self._bookingId),
                                  None, tz = self._conf.getTimezone())

class CollaborationRejectCSBooking(CollaborationAdminBookingModifBase):
    """ Performs server-side actions when a booking / request is rejected
    """
    def _checkParams(self):
        CollaborationAdminBookingModifBase._checkParams(self)
        self._reason = self._params.get("reason", "")

    def _getAnswer(self):
        return fossilize(self._CSBookingManager.rejectBooking(self._bookingId, self._reason),
                                  None, tz = self._conf.getTimezone())

class CollaborationChangePluginManagersBase(CollaborationBase):
    """ Base class for adding and removing plugin managers in an event
        self._plugin will be a string with the plugin name.
    """

    def _checkParams(self):
        CollaborationBase._checkParams(self)
        if self._params.has_key('plugin'):
            self._plugin = self._params['plugin']
        else:
            raise CollaborationException(_("Plugin name not set when trying to add or remove a manager on event: ") + str(self._conf.getId()) + _(" with the service ") + str(self.__class__) )

        if CollaborationTools.getCollaborationPluginType().hasPlugin(self._plugin) and CollaborationTools.isAdminOnlyPlugin(self._plugin):
            raise CollaborationException(_("Tried to add or remove a manager for an admin-only plugin on event : ") + str(self._conf.getId()) + _(" with the service ") + str(self.__class__) )

    def _checkProtection(self):
        if not RCVideoServicesManager.hasRights(self):
            CollaborationBase._checkProtection(self)

class CollaborationAddPluginManager(CollaborationChangePluginManagersBase, UserListModificationBase):
    """ Adds a user as Plugin Manager for an event and plugin
    """

    def _checkParams(self):
        CollaborationChangePluginManagersBase._checkParams(self)
        UserListModificationBase._checkParams(self)

    def _getAnswer(self):
        existingManagerIds = set([u.getId() for u in self._CSBookingManager.getPluginManagers(self._plugin)])
        for u in self._avatars:
            if not u.getId() in existingManagerIds:
                self._CSBookingManager.addPluginManager(self._plugin, u)

        return True


class CollaborationRemovePluginManager(CollaborationChangePluginManagersBase, UserModificationBase):
    """ Removes a user as Plugin Manager for an event and plugin
    """

    def _checkParams(self):
        CollaborationChangePluginManagersBase._checkParams(self)
        UserModificationBase._checkParams(self)

    def _getAnswer(self):
        self._CSBookingManager.removePluginManager(self._plugin, self._targetUser)
        return True


class CollaborationBookingIndexQuery(AdminCollaborationBase):
    """ Performs a query to the Collaboration index of bookings / request objects.
    """

    def _checkProtection(self):
        if not RCCollaborationPluginAdmin.hasRights(self, None, "any"):
            AdminCollaborationBase._checkProtection(self)

    def _checkParams(self):
        AdminCollaborationBase._checkParams(self)
        user = self.getAW().getUser()
        if user: #someone is logged in. if not, AdminCollaborationBase's _checkProtection will take care of it
            self._tz = user.getTimezone()

            try:
                self._page = self._params.get("page", None)
                self._resultsPerPage = self._params.get("resultsPerPage", None)
                self._indexName = self._params['indexName']
                self._viewBy = self._params['viewBy']
                self._orderBy = self._params['orderBy']

                minKey = None
                maxKey = None
                if self._params['sinceDate']:
                    minKey = setAdjustedDate(parseDateTime(self._params['sinceDate'].strip()), tz = self._tz)
                if self._params['toDate']:
                    maxKey = setAdjustedDate(parseDateTime(self._params['toDate'].strip()), tz = self._tz)
                if self._params['fromTitle']:
                    minKey = self._params['fromTitle'].strip()
                if self._params['toTitle']:
                    maxKey = self._params['toTitle'].strip()
                if self._params['fromDays']:
                    try:
                        fromDays = int(self._params['fromDays'])
                    except ValueError, e:
                        raise CollaborationException(_("Parameter 'fromDays' is not an integer"), inner = e)
                    minKey = nowutc() - timedelta(days = fromDays)
                if self._params['toDays']:
                    try:
                        toDays = int(self._params['toDays'])
                    except ValueError, e:
                        raise CollaborationException(_("Parameter 'toDays' is not an integer"), inner = e)
                    maxKey = nowutc() + timedelta(days = toDays)

                self._minKey = minKey
                self._maxKey = maxKey

                self._onlyPending = self._params['onlyPending']
                categoryId = self._params['categoryId'].strip()
                if categoryId:
                    self._categoryId = categoryId
                else:
                    self._categoryId = None
                conferenceId = self._params['conferenceId'].strip()
                if conferenceId:
                    self._conferenceId = conferenceId
                else:
                    self._conferenceId = None

            except KeyError, e:
                raise CollaborationException(_("One of the necessary parameters to query the booking index is missing"), inner = e)

    def _getAnswer(self):
        ci = IndexesHolder().getById('collaboration')

        return ci.getBookings(self._indexName,
                              self._viewBy,
                              self._orderBy,
                              self._minKey,
                              self._maxKey,
                              tz = self._tz,
                              onlyPending = self._onlyPending,
                              conferenceId = self._conferenceId,
                              categoryId = self._categoryId,
                              pickle = True,
                              dateFormat='%a %d %b %Y',
                              page = self._page,
                              resultsPerPage = self._resultsPerPage)

class CollaborationCustomPluginService(CollaborationBase):
    """ Class to support plugin-defined services.
        Plugins have to call 'collaboration.pluginService' and
        specify a 'plugin' and 'service' arguments.
        Then they have to create a class that inherits from
        CollaborationPluginServiceBase with the same name
        as the 'service' argument, plus 'Service' at the end.
        The classes can have _checkParams, _checkProtetion methods,
        and must have a _getAnswer method.
        They will have the following attributes available:
        _params, _aw, _conf, _target, _CSBookingManager.
    """

    def _checkParams(self):
        CollaborationBase._checkParams(self)

        self._pluginName = self._params.pop('plugin')
        if not self._pluginName:
            raise CollaborationException(_("No 'plugin' paramater in CollaborationPluginService"))

        serviceName = self._params.pop('service')
        if not serviceName:
            raise CollaborationException(_("No 'service' paramater in CollaborationPluginService"))

        self._serviceClass = CollaborationTools.getServiceClass(self._pluginName, serviceName)
        if not self._serviceClass:
            raise CollaborationException(_("Service " + str(serviceName) + _("Service not found for plugin ") + str(self._pluginName) + _("in CollaborationPluginService")))

    def _checkProtection(self):
        CollaborationBase._checkCanManagePlugin(self, self._pluginName)

    def _getAnswer(self):
        serviceObject = self._serviceClass(self._params, self._aw)
        serviceObject._checkParams()
        serviceObject._checkProtection()
        return serviceObject._getAnswer()


class CollaborationPluginServiceBase(CollaborationBase):
    """ Base class that plugin-defined services need to inherit from.
        The _params and _aw attributes will be available for them,
        and also _target and _conf and _CSBookingManager from CollaborationBase.
        If they implement a _checkParams method, they need to call
        their parent's (this class's) method first.
        This class _checkParam method calls CollaborationBase's
    """

    def __init__(self, params, aw):
        self._params = params
        self._aw = aw

    def _checkParams(self):
        CollaborationBase._checkParams(self)

    def _checkProtection(self):
        pass

    def _getAnswer(self):
        raise CollaborationException("No answer was returned")


class CollaborationCreateTestCSBooking(CollaborationCreateCSBooking):
    """ Service that creates a 'test' booking for performance test.
        Avoids to use any of the plugins except DummyPlugin
    """
    def _checkParams(self):
        CollaborationBase._checkParams(self)

        if 'bookingParams' in self._params:
            pm = ParameterManager(self._params)
            self._bookingParams = pm.extract("bookingParams", pType=dict, allowEmpty = True)
        else:
            raise CollaborationException(_("Custom parameters for plugin ") + str(self._type) + _(" not set when trying to create a booking on meeting ") + str(self._conf.getId() ))

    def _getAnswer(self):
        return fossilize(self._CSBookingManager.createTestBooking(bookingParams = self._bookingParams),
                         None, tz = self._conf.getTimezone())


methodMap = {
    "createCSBooking": CollaborationCreateCSBooking,
    "removeCSBooking": CollaborationRemoveCSBooking,
    "editCSBooking": CollaborationEditCSBooking,
    "startCSBooking": CollaborationStartCSBooking,
    "stopCSBooking": CollaborationStopCSBooking,
    "checkCSBookingStatus": CollaborationCheckCSBookingStatus,
    "acceptCSBooking": CollaborationAcceptCSBooking,
    "rejectCSBooking": CollaborationRejectCSBooking,
    "bookingIndexQuery": CollaborationBookingIndexQuery,
    "addPluginManager": CollaborationAddPluginManager,
    "removePluginManager": CollaborationRemovePluginManager,
    "pluginService": CollaborationCustomPluginService
}
