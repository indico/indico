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

import MaKaC.conference as conference
import MaKaC.errors as errors
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


class WebLocator:
    def __init__(self):
        self.__categId = None
        self.__confId = None
        self.__materialId = None
        self.__resId = None
        self.__trackId = None
        self.__abstractId = None
        self.__notifTplId = None

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

    def setMaterial(self, params, mustExist=1):
        if "confId" in params and params["confId"] is not None and "abstractId" in params:
            self.setAbstract(params, mustExist)

    def setResource(self, params, mustExist=1):
        if "resId" not in params and "resourceId" in params:
            params["resId"] = params["resourceId"]

        if not params.get("resId", '').strip():
            self.setMaterial(params, mustExist)
            if mustExist:
                raise errors.MaKaCError(_("material id not set"))
        else:
            self.setMaterial(params, 1)
            self.__resId = params["resId"]

    def getObject(self):
        if self.__categId:
            if not conference.CategoryManager().hasKey(self.__categId):
                raise errors.NoReportError(_("There is no category with id '%s', or it has been deleted") % self.__categId)
            obj = conference.CategoryManager().getById(self.__categId)
            if self.__materialId is not None or self.__resId is not None:
                return None  # obsolete - attachments don't use WebLocator
            return obj
        if not self.__confId:
            return None
        obj = conference.ConferenceHolder().getById(self.__confId)
        if obj is None:
            raise errors.NoReportError("The event you are trying to access does not exist or has been deleted")
        if self.__notifTplId:
            obj = obj.getAbstractMgr().getNotificationTplById(self.__notifTplId)
            return obj
        if self.__trackId:
            obj = obj.getTrackById(self.__trackId)
            return obj
        if self.__abstractId:
            obj = obj.getAbstractMgr().getAbstractById(self.__abstractId)
            if obj == None:
                raise errors.NoReportError("The abstract you are trying to access does not exist or has been deleted")
            if self.__resId:
                return obj.getAttachmentById(self.__resId)
        if not self.__materialId:
            return obj
