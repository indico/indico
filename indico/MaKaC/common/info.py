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

import os
import warnings

from flask import current_app as app
from persistent import Persistent
from persistent.dict import PersistentDict
from BTrees import OOBTree

from indico.core.config import Config
from indico.core import db

DEFAULT_PROTECTION_DISCLAINER_RESTRICTED = ("Circulation to people other than the intended audience is not authorized. "
                                            "You are obliged to treat the information with the appropriate level of "
                                            "confidentiality.")
DEFAULT_PROTECTION_DISCLAINER_PROTECTED = ("As such, this information is intended for an internal audience only. "
                                           "You are obliged to treat the information with the appropriate level of "
                                           "confidentiality.")


class MaKaCInfo(Persistent):
    """Holds and manages general information and data concerning each system
    """

    def __init__(self):
        # server description fields
        self._title = ""
        self._organisation = ""
        self._city = ""
        self._country = ""
        self._lang = "en_GB"

        # Account-related features
        self._authorisedAccountCreation = True
        self._notifyAccountCreation = False
        self._moderateAccountCreation = False
        self._moderators = []

        # Global poster/badge templates
        self._defaultConference = None

        # News management
        self._news = ""

        # special features
        self._newsActive = False
        self._debugActive = False

        # template set
        self._defaultTemplateSet = None

        # social sites
        self.getSocialAppConfig()

        # Define if Indico use a proxy (load balancing)
        self. _proxy = False
        # Define the volume used in archiving:
        # e.g. /afs/cern.ch/project/indico/XXXX/2008/...
        # XXXX will be replaced by self._archivingVolume
        # if self._archivingVolume is empty the path would be:
        # /afs/cern.ch/project/indico/2008/...
        self._archivingVolume = ""

        self._ip_based_acl_mgr = IPBasedACLMgr()

        # http api
        self._apiHTTPSRequired = False
        self._apiPersistentAllowed = False
        self._apiMode = 0
        self._apiCacheTTL = 600
        self._apiSignatureTTL = 600

        # Event display style manager
        self._styleMgr = StyleManager()

        self._protectionDisclaimerRestricted = DEFAULT_PROTECTION_DISCLAINER_RESTRICTED
        self._protectionDisclaimerProtected = DEFAULT_PROTECTION_DISCLAINER_PROTECTED

    def getStyleManager( self ):
        try:
            return self._styleMgr
        except:
            self._styleMgr = StyleManager()
            return self._styleMgr

    def getSocialAppConfig( self ):
        if not hasattr(self, '_socialAppConfig'):
            self._socialAppConfig = PersistentDict({'active': False, 'facebook': {}})
        return self._socialAppConfig

    def isDebugActive(self):
        msg = 'MaKaCinfo.isDebugActive() is deprecated; use app.debug or Config.getInstance().getDebug() instead'
        warnings.warn(msg, DeprecationWarning, 2)
        return app.debug

    def getNews( self ):
        try:
            return self._news
        except:
            self._news = ""
            return ""

    def setNews( self, news ):
        self._news = news

    def getModerators( self ):
        try:
            return self._moderators
        except:
            self._moderators = []
            return self._moderators

    def addModerator( self, av ):
        if av not in self.getModerators():
            self._moderators.append(av)
            self._p_changed=1

    def removeModerator( self, av ):
        if av in self.getModerators():
            self._moderators.remove( av )
            self._p_changed=1

    def isModerator( self, av ):
        if av in self.getModerators():
            return True
        else:
            return False

    def getAuthorisedAccountCreation( self ):
        try:
            return self._authorisedAccountCreation
        except:
            self.setAuthorisedAccountCreation()
            return self._authorisedAccountCreation

    def setAuthorisedAccountCreation( self, flag=True ):
        self._authorisedAccountCreation = flag

    def getNotifyAccountCreation( self ):
        try:
            return self._notifyAccountCreation
        except:
            self.setNotifyAccountCreation()
            return self._notifyAccountCreation

    def setNotifyAccountCreation( self, flag=False ):
        self._notifyAccountCreation = flag

    def getModerateAccountCreation( self ):
        try:
            return self._moderateAccountCreation
        except:
            self.setModerateAccountCreation()
            return self._moderateAccountCreation

    def setModerateAccountCreation( self, flag=False ):
        self._moderateAccountCreation = flag

    def getTitle( self ):
        return self._title

    def isNewsActive( self ):
        if hasattr( self, "_newsActive" ):
            return self._newsActive
        else:
            self._newsActive = False
            return False

    def setNewsActive( self, bool=True ):
        self._newsActive = bool

    def setTitle( self, newTitle ):
        self._title = newTitle.strip()

    def getOrganisation( self ):
        return self._organisation

    def getAffiliation( self ):
        return self._organisation

    def setOrganisation( self, newOrg ):
        self._organisation = newOrg.strip()

    def getCity( self ):
        return self._city

    def setCity( self, newCity ):
        self._city = newCity.strip()

    def getCountry( self ):
        return self._country

    def setCountry( self, newCountry ):
        self._country = newCountry

    def getTimezone(self):
        msg = 'MaKaCinfo.getTimezone() is deprecated; use Config.getInstance().getDefaultTimezone() instead'
        warnings.warn(msg, DeprecationWarning, 2)
        return Config.getInstance().getDefaultTimezone()

    def getDefaultConference( self ):
        try:
            self._defaultConference
        except AttributeError:
            self._defaultConference = None

        return self._defaultConference

    def setDefaultConference( self, dConf ):
        self._defaultConference = dConf
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

    def getLang( self ):
        try:
            return self._lang
        except:
            self._lang = "en_GB"
            #Logger.get('i18n').warning('No language set in MaKaCInfo... using %s by default' % self._lang)
            return self._lang

    def setLang( self, lang ):
        self._lang = lang

    def setArchivingVolume(self, volume):
        if isinstance(volume, str):
            self._archivingVolume = volume

    def getArchivingVolume(self):
        if not hasattr(self, "_archivingVolume"):
            self._archivingVolume = ""
        return self._archivingVolume

    def getIPBasedACLMgr(self):
        return self._ip_based_acl_mgr

    def getProtectionDisclaimerProtected(self):
        if not hasattr(self, '_protectionDisclaimerProtected'):
            self._protectionDisclaimerProtected = DEFAULT_PROTECTION_DISCLAINER_PROTECTED
        return self._protectionDisclaimerProtected

    def setProtectionDisclaimerProtected(self, v):
        self._protectionDisclaimerProtected = v

    def getProtectionDisclaimerRestricted(self):
        if not hasattr(self, '_protectionDisclaimerRestricted'):
            self._protectionDisclaimerRestricted = DEFAULT_PROTECTION_DISCLAINER_RESTRICTED
        return self._protectionDisclaimerRestricted

    def setProtectionDisclaimerRestricted(self, v):
        self._protectionDisclaimerRestricted = v


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


class StyleManager(Persistent):
    """This class manages the styles used by the server for the display
       of events timetables
    """

    def __init__( self ):
        self._styles = Config.getInstance().getStyles()
        self._eventStylesheets = Config.getInstance().getEventStylesheets()
        self._defaultEventStylesheet = Config.getInstance().getDefaultEventStylesheet()

    def getStyles(self):
        try:
            return self._styles
        except AttributeError:
            self._styles = Config.getInstance().getStyles()
            return self._styles

    def setStyles(self, newStyles):
        self._styles = newStyles

    def getEventStyles(self):
        """gives back the entire style/event association list.
        """
        return self._eventStylesheets

    def setEventStyles(self, sDict={}):
        self._eventStylesheets = sDict

    def getDefaultEventStyles(self):
        """gives back the default styles/event association
        """
        return self._defaultEventStylesheet

    def setDefaultEventStyle(self, sDict={}):
        self._defaultEventStylesheet = sDict

    def getDefaultStyleForEventType(self, eventType):
        """gives back the default stylesheet for the given type of event
        """
        return self._defaultEventStylesheet.get(eventType, "")

    def removeStyle(self, styleId, type=""):
        if type == "":
            # style globally removed
            styles = self.getStyles()
            if styles.has_key(styleId):
                del styles[styleId]
                self.setStyles(styles)
                self.removeStyleFromAllTypes(styleId)
        else:
            # style removed only in the type list
            self.removeStyleFromEventType(styleId, type)

    def addStyleToEventType( self, style, type ):
        dict = self.getEventStyles()
        styles = dict.get(type,[])
        if style not in styles:
            styles.append(style)
            dict[type] = styles
            self.setEventStyles(dict)

    def removeStyleFromEventType( self, style, type ):
        # style removed only in the type list
        dict = self.getEventStyles()
        styles = dict.get(type,[])
        defaultStyle = self.getDefaultStyleForEventType(type)
        if style != "" and style in styles:
            styles.remove(style)
            dict[type] = styles
            self.setEventStyles(dict)
            if style.strip() == defaultStyle.strip():
                if len(styles) > 0:
                    newDefaultStyle = styles[0]
                else:
                    newDefaultStyle = None
                self.setDefaultStyle( newDefaultStyle, type )

    def setDefaultStyle( self, style, type ):
        if style != "":
            dict = self.getDefaultEventStyles()
            dict[type] = style
            self.setDefaultEventStyle(dict)

    def removeStyleFromAllTypes( self, style ):
        for type in ["simple_event", "meeting", "conference"]:
            self.removeStyleFromEventType(style, type)

    def getStyleListForEventType(self, eventType):
        """gives back the style list associated to a given type of event.
        If no event was specified it returns the empty list.
           Params:
                type -- unique identifier of the event type
        """
        return self._eventStylesheets.get(eventType, [])

    def isCorrectStyle(self, styleId):
        if styleId not in self.getStyles():
            return False

        correctCSS = self.existsCSSFile(styleId) or not self.getCSSFilename(styleId)
        return styleId == 'static' or (self.existsTPLFile(styleId) and correctCSS) or (self.existsXSLFile(styleId) and correctCSS)

    def getExistingStylesForEventType(self, eventType):
        result = []
        for style in self.getStyleListForEventType(eventType):
            if self.isCorrectStyle(style):
                result.append(style)
        return result

    def getStyleDictForEventType(self, type):
        """gives back the style list associated to a given type of event.
        If no event was specified it returns the empty list.
           Params:
                type -- unique identifier of the event type
        """
        styles = self.getStyles()
        return dict((styleID, styles[styleID]) for styleID in self._eventStylesheets.get(type, []))

    def getStyleName(self, styleId):
        styles = self.getStyles()
        if styleId in styles:
            return styles[styleId][0]
        else:
            return ""

    def getBaseTPLPath(self):
        tplDir = Config.getInstance().getTPLDir()
        return os.path.join(tplDir, "events")

    def getBaseXSLPath(self):
        xslDir = Config.getInstance().getStylesheetsDir()
        return os.path.join(xslDir, "events")

    def existsTPLFile(self, styleId):
        if styleId.strip() != "":
            tplFile = self.getTemplateFilename(styleId)
            if not tplFile:
                return False
            path = os.path.join(self.getBaseTPLPath(), tplFile)
            if os.path.exists(path):
                return True
        return False

    def existsXSLFile(self, styleId):
        if styleId.strip() != "":
            xslFile = self.getTemplateFilename(styleId)
            if not xslFile:
                return False
            path = os.path.join(self.getBaseXSLPath(), xslFile)
            if os.path.exists(path):
                return True
        return False

    def getXSLPath(self, styleId):
        if styleId.strip() != "":
            xslFile = self.getTemplateFilename(styleId)
            if not xslFile:
                return False
            path = os.path.join(self.getBaseXSLPath(), xslFile)
            if os.path.exists(path):
                return path
        return None

    def getTemplateFilename(self, styleId):
        styles = self.getStyles()
        if styleId in styles:
            fileName = styles[styleId][1]
            return fileName
        else:
            return None

    def getBaseCSSPath( self ):
        return os.path.join(Config.getInstance().getHtdocsDir(),"css", "events")

    def existsCSSFile(self, styleId):
        if styleId.strip() != "":
            basepath = self.getBaseCSSPath()
            filename = self.getCSSFilename(styleId)
            if not filename:
                return False
            path = os.path.join(basepath, filename)
            if os.path.exists(path):
                return True
        return False

    def getCSSFilename( self, stylesheet ):
        if stylesheet.strip() != "" and stylesheet in self.getStyles():
            return self._styles[stylesheet][2]
        return None

    def getXSLStyles(self):
        xslStyles = []
        for style in self.getStyles():
            if self._styles[style][1]!= None and self._styles[style][1].endswith(".xsl"):
                xslStyles.append(style)
        return xslStyles

    def existsStyle(self, styleId):
        styles = self.getStyles()
        if styleId in styles:
            return True
        else:
            return False

class IPBasedACLMgr(Persistent):

    def __init__(self):
        self._full_access_acl = set()

    def get_full_access_acl(self):
        return self._full_access_acl

    def grant_full_access(self, ip):
        self._full_access_acl.add(ip)
        self.notify_modification()

    def revoke_full_access(self, ip):
        if ip in self._full_access_acl:
            self._full_access_acl.remove(ip)
        self.notify_modification()

    def notify_modification(self):
        self._p_changed = 1

