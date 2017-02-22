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

"""Contains the machinery that allows to access and modify in a more comfortable
and transparent way the system configuration (this is mainly done through the
Config class).
"""

import ast
import copy
import os
import socket
import sys
import urlparse

import pytz
from flask import g, has_app_context, request
from werkzeug.urls import url_parse

import MaKaC
from indico.util.contextManager import ContextManager


__all__ = ['Config']


FILE_TYPES = {"DOC": ["Ms Word", "application/msword", "word_big.png"],
              "DOCX": ["Ms Word", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "word.png"],
              "WAV": ["Audio", "audio/x-pn-wav", ""],
              "XLS": ["MS Excel", "application/vnd.ms-excel", "xls.png"],
              "XLSX": ["MS Excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xls.png"],
              "PS":  ["PostScript", "application/postscript", "ps.png"],
              "SXC": ["Open Office Calc", "application/vnd.sun.xml.calc", "calc.png"],
              "TAR": ["Tar File", "application/tar", "zip.png"],
              "ODP": ["Open Documents Presentation", "application/vnd.sun.xml.impress", "impress.png"],
              "SXI": ["Open Office Impress", "application/vnd.sun.xml.impress", "impress.png"],
              "ODS": ["Open Office Spreadsheet", "application/vnd.sun.xml.calc", "calc.png"],
              "ODT": ["Open Document Text", "application/vnd.sun.xml.writer", "writer.png"],
              "HTML": ["HTML", "text/html", ""],
              "PPT": ["Ms Powerpoint", "application/vnd.ms-powerpoint", "powerpoint.png"],
              "PPTX": ["Ms Powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "powerpoint.png"],
              "RM": ["Real Video", "application/vnd.rn-realmedia", ""],
              "TXT": ["Plain Text", "text/plain", "txt.png"],
              "XML": ["XML", "text/xml", ""],
              "ZIP": ["ZIP", "application/zip", ""],
              "SXW": ["Open Office Writer", "application/vnd.sun.xml.writer", "writer.png"],
              "GZ":  ["Zipped File", "application/zip", "zip.png"],
              "ICAL": ["ICAL", "text/calendar", ""],
              "PDF": ["Portable Document Format", "application/pdf", "pdf_small.png"],
              "CSV": ["Ms Excel", "application/vnd.ms-excel", "excel.png"],
              "HTM": ["HTML", "text/html", ""],
              "OGV": ["Ogg/Theora Video", "application/ogg", ""],
              "MOV": ["Quicktime Video", "video/quicktime", ""],
              "RTF": ["RTF", "application/rtf", ""],
              "OGG": ["Ogg/Theora Video", "application/ogg", ""],
              "RSS": ["RSS", "application/xhtml+xml", ""],
              "MHT": ["MHT", " message/rfc822", ""],
              "JPG": ["JPEG Image", "image/jpeg", ""],
              "PNG": ["PNG Image", "image/png", ""],
              "GIF": ["GIF Image", "image/gif", ""],
              "TIFF": ["TIFF Image", "image/gif", ""],
              "ATOM": ['Atom', "application/atom+xml", ""]
              }


class Config:
    """This class provides a common way to access and modify the configuration
       parameters of the application. This configuration information will be
       stored in a text file and will contain the minimal information (example:
       db connection parameters) for the system to be initialised.
       It will implement the Singleton pattern so only once instance of the
       Config class can exist at the same time.
    """
    __instance = None

    __systemIcons = {"modify": "link_shadow.png",
                     "submit": "file_shadow.png",
                     "view": "view.png",
                     "group": "group.png",
                     "schedule": "schedule.png",
                     "user": "user.png",
                     "loggedIn": "userloggedin.png",
                     "warning": "warning.png",
                     "warning_yellow": "warning_yellow.png",
                     "signin": "key.png",
                     "paper": "paper.png",
                     "slides": "slides.png",
                     "category": "category.png",
                     "admin": "admins.png",
                     "protected": "protected.png",
                     "clone": "clone.png",
                     "delete": "delete.png",
                     "write_minutes": "write_minutes.png",
                     "move": "move.png",
                     "logo": "logo.png",
                     "upArrow": "upArrow.png",
                     "downArrow": "downArrow.png",
                     "download": "download.png",
                     "print": "print.png",
                     "printer": "printer.png",
                     "mail": "mail.png",
                     "mail_big": "mail_big.png",
                     "mail_grey": "mail_grey.png",
                     "comments": "comments.png",
                     "day": "pict_day_orange.png",
                     "year": "pict_year_orange.png",
                     "document": "pict_doc_orange.png",
                     "conference": "pict_conf_bleu.png",
                     "lecture": "pict_event_bleu.png",
                     "meeting": "pict_meet_bleu.png",
                     "meetingIcon": "meeting.png",
                     "bulletMenuConf": "bulletMenuConf.png",
                     "logoIndico": "logo_indico.png",
                     "logoIndicoWhite": "logo_indico_white.png",
                     "indico_small": "indico_small.png",
                     "indico_co": "indico_co.png",
                     "login": "pict_login.png",
                     "tt_time": "tt_time.png",
                     "miniLogo": "mini_logo_indico.png",
                     "conferenceRoom": "conference_logo.png",
                     "xml": "xml_small.png",
                     "ical": "ical_small.png",
                     "ical_grey": "ical_grey.png",
                     "ical_small": "ical_small.png",
                     "material": "material.png",
                     "calendar": "pict_year_orange.png",
                     "pdf": "pdf_small.png",
                     "smallzip": "smallzip.png",
                     "left_arrow": "left_arrow.png",
                     "right_arrow": "right_arrow.png",
                     "first_arrow": "first_arrow.png",
                     "last_arrow": "last_arrow.png",
                     "info": "info.png",
                     "video": "video.png",
                     "poster": "poster.png",
                     "closed": "closed.png",
                     "closeIcon": "close.png",
                     "badge": "badge.png",
                     "badgeMargins": "badge_margins.png",
                     "loading": "loading.gif",
                     "tick": "tick.png",
                     "cross": "cross.png",
                     "file": "file.png",
                     "clock": "clock.png",
                     "addressBarIcon": "indico.ico",
                     "excel": "excel.png",
                     "checkAll": "checkAll.png",
                     "uncheckAll": "uncheckAll.png",
                     "listing": "listing.png",
                     "add": "add.png",
                     "add_faded": "add_faded.png",
                     "remove": "remove.png",
                     "remove_faded": "remove_faded.png",
                     "edit": "edit.png",
                     "edit_faded": "edit_faded.png",
                     "help": "help.png",
                     "search": "search.png",
                     "search_small": "search_small.png",
                     "stat": "stat.png",
                     "logoCERN": "CERNlogo-grey.png",
                     "timezone": "timezone.png",
                     "cern_small": "cern_small.png",
                     "cern_small_light": "cern_small_light.png",
                     "home": "home.png",
                     "upCategory": "up_arrow.png",
                     "manage": "manage.png",
                     "ui_loading": "load_big.gif",
                     "style": "style.png",
                     "filter": "filter.png",
                     "filter_active": "filter_active.png",
                     "reload": "reload.png",
                     "reload_faded": "reload_faded.png",
                     "room": "room.png",
                     "defaultConferenceLogo": "lecture3.png",
                     "breadcrumbArrow": "breadcrumb_arrow.png",
                     "star": "star.png",
                     "starGrey": "starGrey.png",
                     "calendarWidget": "calendarWidget.png",
                     "facebook": "facebook.png",
                     "twitter": "twitter.png",
                     "gplus": "gplus.png",
                     "gcal": "gcal.png",
                     "link": "link.png"
                     }

    default_values = {
        'DBConnectionParams'        : ("localhost", 9675),
        'DBUserName'                : '',
        'DBPassword'                : '',
        'DBRealm'                   : '',
        'IsRoomBookingActive'       : True,
        'SQLAlchemyDatabaseURI'     : None,
        'SQLAlchemyEcho'            : False,
        'SQLAlchemyRecordQueries'   : False,
        'SQLAlchemyPoolSize'        : 5,
        'SQLAlchemyPoolTimeout'     : 10,
        'SQLAlchemyPoolRecycle'     : 120,
        'SQLAlchemyMaxOverflow'     : 3,
        'EnableRoomBooking'         : True,
        'MaxRetries'                : 10,
        'SanitizationLevel'         : 1,
        'CSRFLevel'                 : 2,
        'BaseURL'                   : 'http://localhost/',
        'BaseSecureURL'             : 'https://localhost/',
        'ConfigurationDir'          : "/opt/indico/etc",
        'DocumentationDir'          : "/opt/indico/doc",
        'HtdocsDir'                 : "/opt/indico/htdocs",
        'LogDir'                    : "/opt/indico/log" ,
        'BinDir'                    : "/opt/indico/bin",
        'UploadedFilesTempDir'      : "/opt/indico/tmp",
        'UploadedFilesSharedTempDir': "",
        'XMLCacheDir'               : "/opt/indico/cache",
        'CacheBackend'              : 'files',
        'MemcachedServers'          : [],
        'RedisCacheURL'             : None,
        'SmtpServer'                : ('localhost', 25),
        'SmtpLogin'                 : '',
        'SmtpPassword'              : '',
        'SmtpUseTLS'                : 'no',
        'SupportEmail'              : 'root@localhost',
        'PublicSupportEmail'        : 'root@localhost',
        'NoReplyEmail'              : 'noreply-root@localhost',
        'Profile'                   : 'no',
        'StaticFileMethod'          : None,
        'AuthenticatedEnforceSecure': 'no',
        'MaxUploadFilesTotalSize'   : 0,
        'MaxUploadFileSize'         : 0,
        'ForceConflicts'            : 0,
        'PropagateAllExceptions'    : False,
        'Debug'                     : False,
        'DebugUnicode'              : 0,
        'EmbeddedWebserver'         : False,
        'OAuthGrantTokenTTL'        : 120,
        'MobileURL'                 : '',
        'CheckinURL'                : 'http://old.indico-software.org/wiki/apps/check-in',
        'SCSSDebugInfo'             : True,
        'SessionLifetime'           : 86400 * 31,
        'UseProxy'                  : False,
        'RouteOldUrls'              : False,
        'CustomCountries'           : {},
        'PDFLatexProgram'           : 'xelatex',
        'StrictLatex'               : True,
        'WorkerName'                : socket.getfqdn(),
        'Loggers'                   : ['files'],
        'SentryDSN'                 : None,
        'SentryLoggingLevel'        : 'WARNING',
        'CategoryCleanup'           : {},
        'JanitorUserId'             : 0,
        'Plugins'                   : {},
        'AuthProviders'             : {},
        'IdentityProviders'         : {},
        'ProviderMap'               : {},
        'LocalIdentities'           : True,
        'LocalRegistration'         : True,
        'LocalModeration'           : False,
        'ExternalRegistrationURL'   : '',
        'SecretKey'                 : None,
        'DefaultTimezone'           : 'UTC',
        'DefaultLocale'             : 'en_GB',
        'CeleryBroker'              : None,
        'CeleryResultBackend'       : None,
        'CeleryConfig'              : {},
        'ScheduledTaskOverride'     : {},
        'CheckinAppClientId'        : None,
        'FlowerClientId'            : None,
        'FlowerURL'                 : None,
        'StorageBackends'           : {'default': 'fs:/opt/indico/archive'},
        'AttachmentStorage'         : 'default',
        'StaticSiteStorage'         : None,
        'TrackerURL'                : 'http://localhost:5000/api'
    }

    if sys.platform == 'win32':
        default_values.update({
            "ConfigurationDir"     : "C:\\indico\\etc",
            "DocumentationDir"     : "C:\\indico\\doc",
            "HtdocsDir"            : "C:\\Program Files\\Apache Group\\Apache2\\htdocs\\MaKaC",
            "LogDir"               : "C:\\indico\\log",
            "BinDir"               : "C:\\indico\\archive",
            "UploadedFilesTempDir" : "C:\\indico\\temp",
            "XMLCacheDir"          : "C:\\indico\\cache",
        })

    def __init__(self, filePath = None):
        self.filePath = filePath
        self.__readConfigFile()
        self._shelf = None

    def reset(self, custom={}):
        """
        Resets the config to the default values (ignoring indico.conf) and
        sets custom options if provided
        """
        self._configVars = copy.deepcopy(self.default_values)
        self._configVars.update(custom)
        self._deriveOptions()

    def update(self, **options):
        """Updates the config with new values"""
        invalid = set(options) - self._configVars.viewkeys()
        if invalid:
            raise ValueError('Tried to add invalid config options: {}'.format(', '.join(invalid)))
        self._configVars.update(options)
        self._deriveOptions()

    def _deriveOptions(self):
        webinterface_dir = os.path.join(os.path.dirname(MaKaC.__file__), 'webinterface')

        override = os.environ.get('INDICO_CONF_OVERRIDE')
        if override:
            override = ast.literal_eval(override)
            assert isinstance(override, dict)
            self._configVars.update(override)

        # Variables whose value is derived automatically
        # THIS IS THE PLACE TO ADD NEW SHORTHAND OPTIONS, DONT CREATE A FUNCTION IF THE VALUE NEVER CHANGES,
        # config.py will become fat again if you don't follow this advice.
        self._configVars.update({
            'TPLVars'                   : {"MaKaCHomeURL": self.getBaseURL()},
            'FileTypes'                 : FILE_TYPES,
            'HelpDir'                   : os.path.join(self.getHtdocsDir(), 'ihelp'),
            'StylesheetsDir'            : os.path.join(webinterface_dir, 'stylesheets'),
            'ImagesDir'                 : os.path.join(self.getHtdocsDir(), 'images'),
            'FontsDir'                  : os.path.join(self.getHtdocsDir(), 'fonts'),
            'JSDir'                     : os.path.join(self.getHtdocsDir(), 'js'),
            'SystemIcons'               : self.__systemIcons,
            'TempDir'                   : self.getUploadedFilesTempDir(),
            'UploadedFilesSharedTempDir': self.getSharedTempDir(),
            'RoomPhotosDir'             : os.path.join(self.getHtdocsDir(), 'images', "rooms", "large_photos"),
            'RoomSmallPhotosDir'        : os.path.join(self.getHtdocsDir(), 'images', "rooms", "small_photos"),
            'CssDir'                    : "%s/css/" % (self.getHtdocsDir()),
            'CssBaseURL'                : self.getCssBaseURL(),
            'CssConfTemplateBaseURL'    : self.getCssConfTemplateBaseURL(),
            'TPLDir'                    : os.path.abspath(os.path.join(webinterface_dir, 'tpls')),
            'HostNameURL'               : urlparse.urlparse(self.getBaseURL())[1].partition(':')[0],
            'PortURL'                   : urlparse.urlparse(self.getBaseURL())[1].partition(':')[2] or '80',
            'ImagesBaseURL'             : self.getImagesBaseURL(),
            'ImagesBaseSecureURL'       : self.getImagesBaseSecureURL(),
            'Version'                   : MaKaC.__version__,
            'StaticSiteStorage'         : self.getStaticSiteStorage() or self.getAttachmentStorage(),
        })

    def __readConfigFile(self):
        """initializes configuration parameters (Search order: indico.conf, default_values)

        IF YOU WANT TO CREATE NEW USER CONFIGURABLE OPTIONS:
        If you need to define a new configuration option you _need_ to specify it here with
        its default value and then you can put it in indico.conf.

                #### Indico will not see options that don't appear here ####
        """

        self._configVars = {}

        from MaKaC.common import MaKaCConfig
        from MaKaC.errors import MaKaCError

        declared_values = dir(MaKaCConfig)

        # When populating configuration variables indico.conf's values have priority
        for k in self.default_values:
            if k in declared_values:
                self._configVars[k] = MaKaCConfig.__getattribute__(k) # declared_values[k] doesn't work, don't ask me why
            else: # key is not declared in indico.conf, using its default value
                self._configVars[k] = self.default_values[k]

        # options that are derived automatically
        self._deriveOptions()

        self.__tplFiles = {}

        if self.getSanitizationLevel() not in range(4):
            raise MaKaCError("Invalid SanitizationLevel value (%s). Valid values: 0, 1, 2, 3" % (self._configVars['SanitizationLevel']))

        if self.getCSRFLevel() not in range(4):
            raise MaKaCError("Invalid CSRFLevel value (%s). Valid values: 0, 1, 2, 3" % (self._configVars['CSRFLevel']))

        if self.getStaticFileMethod() is not None and len(self.getStaticFileMethod()) != 2:
            raise MaKaCError('StaticFileMethod must be None, a string or a 2-tuple')

        if self.getDefaultTimezone() not in pytz.all_timezones_set:
            raise ValueError('Invalid default timezone: {}'.format(self.getDefaultTimezone()))

        if self.getAttachmentStorage() not in self.getStorageBackends():
            raise ValueError('Attachment storage "{}" is not defined in storage backends'.format(
                self.getAttachmentStorage()))

    def __getattr__(self, attr):
        """Dynamic finder for values defined in indico.conf

            For example, if an indico.conf value is "username" this method will
            return its value for a getUsername() call.

            If you add a new pair option = value to indico.conf there is no need to
            create anything here. It will be returned automatically.

            This all means that changing the name of an indico.conf will force you
            to change all references in code to getOldOptionName to getNewOptionName
            including the reference in default_values in this file.
        """
        # The following code intercepts all method calls that start with get and are
        # not already defined (so you can still override a get method if you want)
        # and returns a closure that returns the value of the option being asked for
        if attr[0:3] == 'get':
            def configFinder(k):
                return self._configVars[k]
            return lambda: configFinder(attr[3:])
        else:
            raise AttributeError

    def _yesOrNoVariable(self, varName):
        if self._configVars[varName] in ('yes', True):
            return True
        else:
            return False

    def getShortCategURL(self):
        return '%s/c/' % (self.getBaseSecureURL() or self.getBaseURL())

    def getShortEventURL(self):
        return '%s/e/' % (self.getBaseSecureURL() or self.getBaseURL())

    def getSmtpUseTLS(self):
        return self._yesOrNoVariable('SmtpUseTLS')

    def getProfile(self):
        return self._yesOrNoVariable('Profile')

    def getUseXSendFile(self):
        raise NotImplementedError('Deprecated Method')

    def getStaticFileMethod(self):
        val = self._configVars['StaticFileMethod']
        if not val:
            return None
        elif isinstance(val, basestring):
            return val, None
        elif not val[0]:
            return None
        else:
            return val

    def getAuthenticatedEnforceSecure(self):
        return self._yesOrNoVariable('AuthenticatedEnforceSecure') and self.getBaseSecureURL()

    @classmethod
    def getInstance(cls):
        """returns an instance of the Config class ensuring only a single
           instance is created. All the clients should use this method for
           setting a Config object instead of normal instantiation
        """
        if cls.__instance is None:
            cls.__instance = Config()
        return cls.__instance

    @classmethod
    def setInstance(cls, instance):
        cls.__instance = instance

    def getCurrentDBDir(self):
        """gives back the path of the directory where the current database
           files are kept
        """
        raise NotImplementedError("Deprecated Method")
        # return raw_input("\n\nPlease enter the path to the directory that contains the database files")


    def getDBBackupsDir(self):
        """gives back the path of the directory where the backups of the
           database files are kept
        """
        raise NotImplementedError("Deprecated Method")
        # return raw_input("\n\nPlease enter the path to the directory that will contain the database backups [OPTIONAL]\n\n")


    def getTimezoneList(self):
        # Dont move outside, we need to call Config.getInstance() from setup.py and if
        # the system has no pytz module then the import will break
        from pytz import all_timezones as Timezones
        return Timezones

    def getCssStylesheetName(self):
        return 'Default.css'

    def getCssConfTemplateBaseURL(self):
        rh = ContextManager.get('currentRH', None)

        if rh and request.is_secure and self.getBaseSecureURL():
            baseURL = self.getBaseSecureURL()
        else:
            baseURL = self.getBaseURL()

        return "%s/css/confTemplates" % baseURL

    def getTPLFile(self, tplId):
        """gives back the template file name associated to a certain page of
           the web interface. If no TPL file was specified it returns the
           empty string.
           Params:
                tplId -- unique identifier of the web interface page (normally
                    the web page class string)
        """
        if tplId in self.__tplFiles:
            return self.__tplFiles[tplId]
        else:
            return ""


    def getTPLVars(self):
        """gives back the user configured variables that must be available in
           any template file.
        """
        vars = self._configVars['TPLVars'].copy()
        vars["imagesDir"] = self.getImagesBaseURL()
        return vars


    def getCategoryIconPath(self, categid):
        return "%s/categicon/%s.png" % (self.getImagesDir(), categid)


    def getCategoryIconURL(self, categid):
        return "%s/categicon/%s.png" % (self.getImagesBaseURL(), categid)


    def getFileType(self, fileExtension):
        """returns the file type corresponding to the specified file extension
        """
        if fileExtension.strip().upper() in self.getFileTypes():
            return fileExtension.strip().upper()
        return ""


    def getFileTypeDescription(self, fileType):
        """returns the configured file type description for the specified file
            type.
        """
        if fileType in self.getFileTypes():
            return self.getFileTypes()[fileType][0]
        return ""


    def getFileTypeMimeType(self, fileType):
        """returns the configured mime-type for the specified file type
        """
        if fileType in self.getFileTypes():
            return self.getFileTypes()[fileType][1]
        return "unknown"


    def getFileTypeIconURL(self, fileType):
        if fileType == "":
            return ""
        try:
            icon = self.getFileTypes()[fileType][2]
        except IndexError:
            return ""
        except KeyError:
            return ""
        if icon == "":
            return ""
        iconPath = os.path.join( self.getImagesDir(), icon )
        if not os.access( iconPath, os.F_OK ):
            return ""
        return "%s/%s"%( self.getImagesBaseURL(), icon )


    def getSystemIconURL( self, id ):
        if id not in self.__systemIcons:
            return "%s/%s"%(self.getImagesBaseURL(), id )
        return "%s/%s"%(self.getImagesBaseURL(), self.__systemIcons[ id ])

    def getSystemIconFileName(self, id):
        if id not in self.__systemIcons:
            return id
        return self.__systemIcons[id]

    def getSharedTempDir(self):
        std = self.getUploadedFilesSharedTempDir()
        if std == "":
            std = self.getUploadedFilesTempDir()
        return std

    def getImagesBaseURL(self):
        if has_app_context() and g.get('static_site'):
            return "static/images"
        else:
            return url_parse("%s/images" % self.getBaseURL()).path

    def getImagesBaseSecureURL(self):
        if has_app_context() and g.get('static_site'):
            return "static/images"
        else:
            return url_parse("%s/images" % self.getBaseSecureURL()).path

    def getCssBaseURL(self):
        if has_app_context() and g.get('static_site'):
            return "static/css"
        else:
            return url_parse("%s/css" % self.getBaseURL()).path

    def getFontsBaseURL(self):
        if g.get('static_site'):
            return "static/fonts"
        else:
            return url_parse("%s/fonts" % self.getBaseURL()).path

    def getScriptBaseURL(self):
        if g.get('static_site'):
            return 'static/js'
        else:
            return url_parse('%s/js' % self.getBaseURL()).path
