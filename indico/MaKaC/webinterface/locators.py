# -*- coding: utf-8 -*-
##
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

import MaKaC.conference as conference
import MaKaC.errors as errors
import MaKaC.domain as domain
import MaKaC.roomMapping as roomMapping
import MaKaC.webinterface.materialFactories as materialFactories
from MaKaC.i18n import _

class CategoryWebLocator:

    def __init__( self, params, mustExist=1 ):
        self._categList = []
        categIds = params.get("categId", [])
        if categIds == [] or params["categId"] == "":
            if mustExist:
                raise errors.MaKaCError( _("category ids not set"))
        if isinstance(categIds, basestring):
            categIds = [categIds]
        ch = conference.CategoryManager()
        for id in categIds:
            try:
                self._categList.append(ch.getById(id))
            except KeyError:
                continue


    def getObjectList( self ):
        return self._categList

    def getObject( self ):
        if len(self.getObjectList()) == 0:
            return None
        if len(self.getObjectList()) == 1:
            return self.getObjectList()[0]
        return self.getObjectList()


class DomainWebLocator:

    def __init__( self, params ):
        domId = params.get("domainId", "")
        if domId == "":
            raise errors.MaKaCError( _("domain id not set"))
        dh = domain.DomainHolder()
        self._dom = dh.getById( domId )

    def getObject( self ):
        return self._dom

class RoomMapperWebLocator:

    def __init__( self, params ):
        rmId = params.get("roomMapperId", "")
        if rmId == "":
            raise errors.MaKaCError( _("room mapper id not set"))
        rmh = roomMapping.RoomMapperHolder()
        self._rm = rmh.getById( rmId )

    def getObject( self ):
        return self._rm

class WebLocator:

    def __init__(self):
        self.__categId = None
        self.__confId = None
        self.__sessionId = None
        self.__contribId = None
        self.__subContribId = None
        self.__reviewId = None
        self.__materialId = None
        self.__resId = None
        self.__alarmId = None
        self.__trackId = None
        self.__abstractId = None
        self.__menuLinkId = None
        self.__contribTypeId = None
        self.__slotId = None
        self.__notifTplId = None
        self.__resvID = None
        self.__location = None
        self.__roomID = None
        self.__registrantId = None

    def setCategory( self, params, mustExist=1 ):
        if not ("categId" in params.keys()) or params["categId"].strip()=="":
            if mustExist:
                raise errors.MaKaCError( _("category id not set"))
        self.__categId = params["categId"]

    def setConference( self, params ):
        if not ("confId" in params.keys()) and "confid" in params.keys():
            params["confId"] = params["confid"]
        if not ("confId" in params.keys()) and "conference" in params.keys():
            params["confId"] = params["conference"]
        if isinstance(params.get("confId", ""), list):
            params["confId"] = params["confId"][0]
        if not ("confId" in params.keys()) or \
           params["confId"] == None or \
               params["confId"].strip()=="":
            raise errors.MaKaCError( _("conference id not set"))
        self.__confId = params["confId"]

    def getConference( self ):
        return conference.ConferenceHolder().getById( self.__confId )

    def setNotificationTemplate( self, params, mustExist=1 ):
        self.setConference(params)
        if not ("notifTplId" in params.keys()) or params["notifTplId"].strip == "":
            if mustExist:
                raise errors.MaKaCError( _("notificationTemplate id not set"))
        else:
            self.__notifTplId = params["notifTplId"]

    def setMenuLink( self, params, mustExist=1 ):
        self.setConference(params)
        if not ("linkId" in params.keys()) or params["linkId"].strip=="":
            if mustExist:
                raise errors.MaKaCError( _("link id not set"))
        else:
            self.__menuLinkId = params["linkId"]

    def setContribType( self, params ):
        self.setConference(params)
        if not ("contribTypeId" in params.keys()) or params["contribTypeId"].strip=="":
            raise errors.MaKaCError( _("contribType id not set"))
        else:
            self.__contribTypeId = params["contribTypeId"]

    def setAbstract( self, params, mustExist=1  ):
        self.setConference( params )
        if not ("abstractId" in params.keys()) or \
           params["abstractId"].strip()=="":
            if mustExist:
                raise errors.MaKaCError( _("abstract id not set"))
        else:
            self.__abstractId = params["abstractId"]

    def setTrack( self, params, mustExist=1 ):
        self.setConference( params )
        if not ("trackId" in params.keys()) or \
           params["trackId"].strip()=="":
            if mustExist:
                raise errors.MaKaCError( _("track id not set"))
        else:
            self.__trackId = params["trackId"]

    def setSession( self, params, mustExist=1 ):
        self.setConference( params )
        if not ("sessionId" in params.keys()) or \
           params["sessionId"] == None or \
           params["sessionId"].strip()=="":
            if not ("session" in params.keys()) or \
                params["session"] == None or \
                params["session"].strip()=="":
                if mustExist:
                    raise errors.MaKaCError( _("session id not set"))
            else:
                self.__sessionId = params["session"]
        else:
            self.__sessionId = params["sessionId"]

    def setSlot( self, params, mustExist=1 ):
        self.setSession( params, mustExist )
        if not ("slotId" in params.keys()) or \
           params["slotId"].strip()=="":
            if not ("sessionSlotId" in params.keys()) or \
                params["sessionSlotId"].strip()=="":
                if not ("slot" in params.keys()) or \
                    params["slot"].strip()=="":
                    if mustExist:
                        raise errors.MaKaCError( _("slot id not set"))
                else:
                    self.__slotId = params["slot"]
            else:
                self.__slotId = params["sessionSlotId"]
        else:
            self.__slotId = params["slotId"]

    def setContribution( self, params, mustExist=1 ):
        #self.setSession( params, 0 )
        #self.setConference( params )
        self.setSlot( params, 0)

        if not ("contribId" in params.keys()) or \
           params["contribId"] == None or \
           params["contribId"].strip()=="":
            if mustExist:
                raise errors.MaKaCError( _("contribution id not set"))
        else:
            self.__contribId = params["contribId"]


    def setSubContribution( self, params, mustExist=1 ):

        self.setContribution( params, 0 )

        #self.setConference( params )
        if not ("subContId" in params.keys()) or \
               params["subContId"] == None or \
               params["subContId"].strip()=="":
            if mustExist:
                raise errors.MaKaCError( _("sub contribution id not set"))
        else:
            self.__subContribId = params["subContId"]

    def setReview(self, params, mustExist=1):

        self.setContribution( params, 0 )

        if not ("reviewId" in params.keys()) or \
            params["reviewId"].strip()=="":
            if mustExist:
                raise errors.MaKaCError( _("review id not set"))
        else:
            self.__reviewId = params["reviewId"]

    def setAlarm(self, params, mustExist=1 ):
        self.setConference( params )
        #self.setConference( params )
        if not ("alarmId" in params.keys()) or \
            params["alarmId"].strip()=="":
            if mustExist:
                raise errors.MaKaCError( _("alarm id not set"))
        else:
            self.__alarmId = params["alarmId"]

    def setRegistrant( self, params, mustExist=1  ):
        self.setConference( params )
        if not ("registrantId" in params.keys()) or \
           params["registrantId"].strip()=="":
            if mustExist:
                raise errors.MaKaCError( _("registrant id not set"))
        else:
            self.__registrantId = params["registrantId"]

    def setMaterial( self, params, mustExist=1 ):
        if "confId" in params.keys() and params["confId"] != None:
            if "reviewId" in params.keys():
                self.setReview(params, 0)
            elif "abstractId" in params.keys():
                self.setAbstract(params, mustExist)
                return
            elif "registrantId" in params.keys():
                self.setRegistrant(params, mustExist)
                return
            else:
                self.setSubContribution( params, 0 )

        else:
            self.setCategory( params )
        if not ("materialId" in params.keys()) or \
           params["materialId"].strip()=="":
            if mustExist:
                raise errors.MaKaCError( _("material id not set"))
        else:
            self.__materialId = params["materialId"]

    def setResource( self, params, mustExist=1 ):
        if not ("resId" in params.keys()) and "resourceId" in params.keys():
            params["resId"] = params["resourceId"]

        if not ("resId" in params.keys()) or params["resId"].strip()=="":
            self.setMaterial( params, mustExist )
            if mustExist:
                raise errors.MaKaCError( _("material id not set"))
        else:
            self.setMaterial( params, 1 )
            self.__resId = params["resId"]

    def setRoomBooking( self, params ):
        if not params.has_key( 'resvID' ):
            raise errors.MaKaCError( _("resvID not set"))
        if not params.has_key( 'roomLocation' ):
            raise errors.MaKaCError( _("roomLocation not set"))
        self.__resvID = int( params['resvID'] )
        self.__location = params['roomLocation']

    def setRoom( self, params ):
        if not params.has_key( 'roomID' ):
            raise errors.MaKaCError( _("roomID not set"))
        if not params.has_key( 'roomLocation' ):
            raise errors.MaKaCError( _("roomLocation not set"))
        self.__roomID = int( params['roomID'] )
        self.__location = params['roomLocation']

    def getObject( self ):
        """
        """
        if self.__resvID:
            from MaKaC.rb_location import CrossLocationQueries, Location
            obj = CrossLocationQueries.getReservations( resvID = self.__resvID, location = self.__location )
            return obj
        if self.__roomID:
            from MaKaC.rb_location import CrossLocationQueries, Location
            obj = CrossLocationQueries.getRooms( roomID = self.__roomID, location = self.__location )
            return obj
        if self.__categId:
            if not conference.CategoryManager().hasKey(self.__categId):
                raise errors.NoReportError(_("There is no category with id '%s', or it has been deleted") % self.__categId)
            obj = conference.CategoryManager().getById(self.__categId)
            if self.__materialId:
                obj=obj.getMaterialById(self.__materialId)
            if self.__resId:
                obj=obj.getResourceById( self.__resId )
            return obj
        if not self.__confId:
            return None
        obj = conference.ConferenceHolder().getById( self.__confId )
        if obj == None:
            raise errors.NoReportError("The event you are trying to access does not exist or has been deleted")
        fr = materialFactories.ConfMFRegistry
        if self.__notifTplId:
            obj = obj.getAbstractMgr().getNotificationTplById(self.__notifTplId)
            return obj
        if self.__alarmId:
            obj = obj.getAlarmById( self.__alarmId )
            return obj
        if self.__trackId:
            obj = obj.getTrackById( self.__trackId )
            return obj
        if self.__menuLinkId:
            obj = obj.getDisplayMgr().getMenu().getLinkById(self.__menuLinkId)
            return obj
        if self.__contribTypeId:
            obj = obj.getContribTypeById(self.__contribTypeId)
            return obj
        if self.__abstractId:
            obj = obj.getAbstractMgr().getAbstractById( self.__abstractId )
            if obj == None:
                raise errors.NoReportError("The abstract you are trying to access does not exist or has been deleted")
            if self.__resId:
                return obj.getAttachmentById( self.__resId )
        if self.__registrantId:
            obj = obj.getRegistrantById( self.__registrantId )
            if obj == None:
                raise errors.NoReportError("The registrant you are trying to access does not exist or has been deleted")
            if self.__resId:
                return obj.getAttachmentById( self.__resId )
        if self.__sessionId:
            obj = obj.getSessionById( self.__sessionId )
            fr = materialFactories.SessionMFRegistry
            if obj == None:
                raise errors.NoReportError("The session you are trying to access does not exist or has been deleted")
        if self.__slotId:
            obj = obj.getSlotById( self.__slotId )
        if self.__contribId:
            obj = obj.getContributionById( self.__contribId )
            fr = materialFactories.ContribMFRegistry
            if obj == None:
                raise errors.NoReportError("The contribution you are trying to access does not exist or has been deleted")
        if self.__reviewId:
            #obj must be a Contribution
            obj = obj.getReviewManager().getReviewById(self.__reviewId)
            if obj == None:
                raise errors.NoReportError("The review you are tring to access does not exist or has been deleted")
        if self.__subContribId and self.__contribId:
            obj = obj.getSubContributionById( self.__subContribId )
            fr = materialFactories.ContribMFRegistry
            if obj == None:
                raise errors.NoReportError("The subcontribution you are trying to access does not exist or has been deleted")
        if not self.__materialId:
            return obj
        #first we check if it refers to a special type of material
        mat = None
        f = fr.getById( self.__materialId )
        if f:
            mat = f.get( obj )
        if not mat:
            mat = obj.getMaterialById( self.__materialId )
        if not self.__resId:
            return mat
        return mat.getResourceById( self.__resId )
