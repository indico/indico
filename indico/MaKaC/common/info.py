# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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
from persistent.dict import PersistentDict
from BTrees import OOBTree

from indico.core import db


class MaKaCInfo(Persistent):
    """Holds and manages general information and data concerning each system
    """

    def __init__(self):
        # server description fields
        self._title = ""
        self._organisation = ""

        # Global poster/badge templates
        self._defaultConference = None

        # template set
        self._defaultTemplateSet = None

        # social sites
        self.getSocialAppConfig()

        # Define the volume used in archiving:
        # e.g. /afs/cern.ch/project/indico/XXXX/2008/...
        # XXXX will be replaced by self._archivingVolume
        # if self._archivingVolume is empty the path would be:
        # /afs/cern.ch/project/indico/2008/...
        self._archivingVolume = ""

    def getSocialAppConfig( self ):
        if not hasattr(self, '_socialAppConfig'):
            self._socialAppConfig = PersistentDict({'active': False, 'facebook': {}})
        return self._socialAppConfig

    def getTitle( self ):
        return self._title

    def setTitle( self, newTitle ):
        self._title = newTitle.strip()

    def getOrganisation( self ):
        return self._organisation

    def getAffiliation( self ):
        return self._organisation

    def setOrganisation( self, newOrg ):
        self._organisation = newOrg.strip()

    def getDefaultConference(self):
        from MaKaC.conference import DefaultConference
        if self._defaultConference is None:
            self._defaultConference = DefaultConference()
        return self._defaultConference

    def getDefaultTemplateSet( self ):
        try:
            return self._defaultTemplateSet
        except:
            self._defaultTemplateSet = None
            return None

    def setDefaultTemplateSet( self, defTemp ):
        self._defaultTemplateSet = defTemp
        return self._defaultTemplateSet

    def setArchivingVolume(self, volume):
        if isinstance(volume, str):
            self._archivingVolume = volume

    def getArchivingVolume(self):
        if not hasattr(self, "_archivingVolume"):
            self._archivingVolume = ""
        return self._archivingVolume


class HelperMaKaCInfo:
    """Helper class used for getting and instance of MaKaCInfo.
        It will be migrated into a static method in MaKaCInfo class once the
        ZODB4 is released and the Persistent classes are no longer Extension
        ones.
    """
    @classmethod
    def getMaKaCInfoInstance(cls):
        dbmgr = db.DBMgr.getInstance()
        root = dbmgr.getDBConnection().root()
        try:
            minfo = root['MaKaCInfo']['main']
        except KeyError:
            minfo = MaKaCInfo()
            root['MaKaCInfo'] = OOBTree.OOBTree()
            root['MaKaCInfo']['main'] = minfo
        return minfo
