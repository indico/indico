# -*- coding: utf-8 -*-
##
## $Id: collaboration.py,v 1.14 2009/06/18 15:14:43 pferreir Exp $
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

from MaKaC.services.implementation.base import ParameterManager,\
    ProtectedService
from MaKaC.services.implementation.conference import ConferenceModifBase
from MaKaC.common.PickleJar import DictPickler
from MaKaC.plugins.Collaboration.base import CollaborationException, CollaborationServiceException
from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin,\
    RCCollaborationPluginAdmin
from MaKaC.i18n import _
from MaKaC.common.indexes import IndexesHolder
from MaKaC.plugins.base import PluginsHolder
from MaKaC.errors import PluginError


## Base classes
class CollaborationBase(ConferenceModifBase):
    """ This base class stores the _CSBookingManager attribute
        so that inheriting classes can use it.
    """
    def _checkParams(self):
        ConferenceModifBase._checkParams(self) #sets self._target = self._conf = the Conference object
        self._CSBookingManager = self._conf.getCSBookingManager()
    
    def _checkCollaborationEnabled(self):
        """ Checks if the Collaboration plugin system is active
        """
        if not PluginsHolder().hasPluginType("Collaboration"):
            raise PluginError("Collaboration plugin system is not active")
        
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
        CollaborationBase._checkCollaborationEnabled(self)
        #check that the user can modify the target booking
        if not RCCollaborationAdmin.hasRights(self) and not RCCollaborationPluginAdmin.hasRights(self, None, [self._bookingPlugin]):
            CollaborationBase._checkProtection(self)

class CollaborationAdminBookingModifBase(CollaborationBookingModifBase):
    
    def _checkProtection(self):
        CollaborationBase._checkCollaborationEnabled(self)
        if not RCCollaborationAdmin.hasRights(self) and not RCCollaborationPluginAdmin.hasRights(self, None, [self._bookingPlugin]):
            raise CollaborationException(_("You don't have the rights to perform this operation on this booking"))

class AdminCollaborationBase(ProtectedService):
    
    def _checkProtection(self):
        if not PluginsHolder().hasPluginType("Collaboration"):
            raise PluginError("Collaboration plugin system is not active")
        if not RCCollaborationAdmin.hasRights(self, None):
            raise CollaborationException(_("You don't have the rights to perform this operation"))

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
        CollaborationBase._checkCollaborationEnabled(self)
        if not RCCollaborationAdmin.hasRights(self) and not RCCollaborationPluginAdmin.hasRights(self, None, [self._type]):
            CollaborationBase._checkProtection(self)
    
    def _getAnswer(self):
        return DictPickler.pickle(self._CSBookingManager.createBooking(self._type, bookingParams = self._bookingParams),
                                  timezone = self._conf.getTimezone())
    
    
class CollaborationRemoveCSBooking(CollaborationBookingModifBase):
    """ Removes a booking
    """
    def _getAnswer(self):
        return DictPickler.pickle(self._CSBookingManager.removeBooking(self._bookingId),
                                  timezone = self._conf.getTimezone())
        
        
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
        return DictPickler.pickle(self._CSBookingManager.changeBooking(self._bookingId, self._bookingParams),
                                  timezone = self._conf.getTimezone())
    
    
class CollaborationStartCSBooking(CollaborationBookingModifBase):
    """ Performs server-side actions when a booking is started
    """
    def _getAnswer(self):
        return DictPickler.pickle(self._CSBookingManager.startBooking(self._bookingId),
                                  timezone = self._conf.getTimezone())

class CollaborationStopCSBooking(CollaborationBookingModifBase):
    """ Performs server-side actions when a booking is started
    """
    def _getAnswer(self):
        return DictPickler.pickle(self._CSBookingManager.stopBooking(self._bookingId),
                                  timezone = self._conf.getTimezone())

class CollaborationCheckCSBookingStatus(CollaborationBookingModifBase):
    """ Performs server-side actions when a booking is started
    """
    def _getAnswer(self):
        return DictPickler.pickle(self._CSBookingManager.checkBookingStatus(self._bookingId),
                                  timezone = self._conf.getTimezone())
        
class CollaborationAcceptCSBooking(CollaborationAdminBookingModifBase):
    """ Performs server-side actions when a booking is started
    """
    def _getAnswer(self):
        return DictPickler.pickle(self._CSBookingManager.acceptBooking(self._bookingId),
                                  timezone = self._conf.getTimezone())
        
class CollaborationRejectCSBooking(CollaborationAdminBookingModifBase):
    """ Performs server-side actions when a booking is started
    """
    def _checkParams(self):
        CollaborationAdminBookingModifBase._checkParams(self)
        self._reason = self._params.get("reason", "")
    
    def _getAnswer(self):
        return DictPickler.pickle(self._CSBookingManager.rejectBooking(self._bookingId, self._reason),
                                  timezone = self._conf.getTimezone())
    
class CollaborationBookingIndexQuery(AdminCollaborationBase):
    """
    """
    def _checkParams(self):
        AdminCollaborationBase._checkParams(self)
        try:
            self._page = self._params.get("page", None)
            self._resultsPerPage = self._params.get("resultsPerPage", None)
            self._indexName = self._params['indexName']
            self._viewBy = self._params['viewBy']
            self._orderBy = self._params['orderBy']
            minKey = self._params['minKey'].strip()
            if minKey:
                self._minKey = minKey
            else:
                self._minKey = None
            maxKey = self._params['maxKey'].strip()
            if maxKey:
                self._maxKey = maxKey
            else:
                self._maxKey = None
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
        tz = self.getAW().getUser().getTimezone()
        
        return ci.getBookings(self._indexName,
                              self._viewBy,
                              self._orderBy,
                              self._minKey,
                              self._maxKey,
                              tz = tz,
                              onlyPending = self._onlyPending,
                              conferenceId = self._conferenceId,
                              categoryId = self._categoryId,
                              pickle = True,
                              dateFormat='%a %d %b %Y',
                              page = self._page,
                              resultsPerPage = self._resultsPerPage)
    

methodMap = {
    "createCSBooking": CollaborationCreateCSBooking,
    "removeCSBooking": CollaborationRemoveCSBooking,
    "editCSBooking": CollaborationEditCSBooking,
    "startCSBooking": CollaborationStartCSBooking,
    "stopCSBooking": CollaborationStopCSBooking,
    "checkCSBookingStatus": CollaborationCheckCSBookingStatus,
    "acceptCSBooking": CollaborationAcceptCSBooking,
    "rejectCSBooking": CollaborationRejectCSBooking,
    "bookingIndexQuery": CollaborationBookingIndexQuery
}
