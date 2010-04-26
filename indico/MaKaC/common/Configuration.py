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

"""Contains the machinery that allows to access and modify in a more comfortable
and transparent way the system configuration (this is mainly done through the
Config class).
"""
import os
import urlparse
import socket
import sys

import MaKaCConfig

from MaKaC.errors import MaKaCError
from MaKaC.i18n import _
import MaKaC

class Config:
    """This class provides a common way to access and modify the configuration
       parameters of the application. This configuration information will be
       stored in a text file and will contain the minimal information (example:
       db connection parameters) for the system to be initialised.
       It will implement the Singleton pattern so only once instance of the
       Config class can exist at the same time.
    """
    __instance = None

    __systemIcons = { "new": "newleft.png",
                 "modify": "link_shadow.png",
                 "submit": "file_shadow.png",
                 "view": "view.png",
                 "group": "group.png",
                 "groupNICE": "groupNICE.png",
                 "itemCollapsed": "collapsd.png",
                 "itemExploded": "exploded.png",
                 "schedule": "schedule.png",
                 "user": "user.png",
                 "loggedIn": "userloggedin.png",
                 "warning": "warning.png",
                 "warning_yellow": "warning_yellow.png",
                 "signin": "key.png",
                 "currentMenuItem": "collapsd.png",
                 "paper": "paper.png",
                 "slides": "slides.png",
                 "category": "category.png",
                 "admin": "admins.png",
                 "protected": "protected.png",
                 "clone": "clone.png",
                 "delete": "delete.png",
                 "smallDelete": "smallDelete.png",
                 "smallCopy": "smallCopy.png",
                 "write_minutes": "write_minutes.png",
                 "move": "move.png",
                 "logo": "logo.png",
                 "track_bullet": "track_bullet.png",
                 "upArrow": "upArrow.png",
                 "downArrow": "downArrow.png",
                 "download": "download.png",
                 "print": "print.png",
                 "printer": "printer.png",
                 "as_rejected": "as_rejected.png",
                 "as_prop_reject": "as_prop_reject.png",
                 "as_accepted": "as_accepted.png",
                 "as_prop_accept": "as_prop_accept.png",
                 "as_submitted": "as_submitted.png",
                 "as_review": "as_review.png",
                 "as_conflict": "as_conflict.png",
                 "as_withdrawn": "as_withdrawn.png",
                 "ats_rejected": "as_rejected.png",
                 "ats_prop_accept": "as_prop_accept.png",
                 "ats_accepted": "as_accepted.png",
                 "ats_prop_reject": "as_prop_reject.png",
                 "ats_submitted": "as_submitted.png",
                 "ats_accepted_other": "ats_accepted_other.png",
                 "ats_withdrawn": "as_withdrawn.png",
                 "ats_prop_other_track": "ats_prop_other_track.png",
                 "mail": "mail.png",
                 "mail_big": "mail_big.png",
                 "comments": "comments.png",
                 "day": "pict_day_orange.png",
                 "year": "pict_year_orange.png",
                 "document": "pict_doc_orange.png",
                 "conference": "pict_conf_bleu.png",
                 "lecture": "pict_event_bleu.png",
                 "meeting": "pict_meet_bleu.png",
                 "arrowBottom": "pict_fleche_bottom.png",
                 "arrowRight": "pict_fleche_right.png",
                 "arrowLeft": "pict_fleche_left.png",
                 "meetingIcon": "meeting.png",
                 "arrowBottomMenuConf": "arrowBottomMenuConf.png",
                 "arrowRightMenuConf": "arrowRightMenuConf.png",
                 "arrowRightMenuConfSelected": "arrowRightMenuConfSelected.png",
                 "bulletMenuConf": "bulletMenuConf.png",
                 "logoIndico": "logo_indico.png",
                 "indico_small": "indico_small.png",
                 "login": "pict_login.png",
                 "table": "img_table.png",
                 "lectureMenu": "pict_event_negb.png",
                 "meetingMenu": "pict_meet_negb.png",
                 "conferenceMenu": "pict_conf_negb.png",
                 "gestionOrg": "pict_gestion1_orange_trans.png",
                 "gestionGrey": "pict_gestion2_gris.png",
                 "miniLogo": "mini_logo_indico.png",
                 "conferenceRoom": "conference_logo.png",
                 "xml": "xml_small.png",
                 "ical": "ical_small.png",
                 "ical_grey": "ical_grey.png",
                 "ical_small": "ical_small.png",
                 "material": "material.png",
                 "calendar": "pict_year_orange.png",
                 "live": "live.png",
                 "addlive": "live_add.png",
                 "colortable": "colortable.png",
                 "colorchart": "colorchart.png",
                 "closeMenuIcon": "closeMenuIcon.png",
                 "openMenuIcon": "openMenuIcon.png",
                 "pdf": "pdf_small.png",
                 "smallzip": "smallzip.png",
                 "left_arrow": "left_arrow.png",
                 "right_arrow": "right_arrow.png",
                 "first_arrow": "first_arrow.png",
                 "last_arrow": "last_arrow.png",
                 "openMenuIcon": "openMenuIcon.png",
                 "envelope": "envelope.png",
                 "info": "info.png",
                 "materialPkg": "diskettes.png",
                 "video": "video.png",
                 "poster": "poster.png",
                 "smallVideo": "smallVideo.png",
                 "smallPaper": "smallPaper.png",
                 "smallSlides": "smallSlides.png",
                 "smallPoster": "smallPoster.png",
                 "smallEmail": "smallEmail.png",
                 "closed": "closed.png",
                 "closeIcon": "close.png",
                 "alarmIcon": "alarm.png",
                 "new": "newleft.png",
                 "dvd": "dvd.png",
                 "badge": "badge.png",
                 "badgeMargins": "badge_margins.png",
                 "loading": "loading.gif",
                 "enabledSection": "enabledSection.png",
                 "disabledSection": "disabledSection.png",
                 "tick": "tick.png",
                 "cross": "cross.png",
                 "cofee": "coffee.png",
                 "subfile": "subfile.png",
                 "file": "file.png",
                 "bigfile": "bigfile.png",
                 "clock": "clock.png",
                 "existingfile": "existingfile.png",
                 "subsection": "disabledSubSection.png",
                 "addressBarIcon": "indico.ico",
                 "excel": "excel.png",
                 "openMenu": "menu_open.png",
                 "closeMenu": "menu_close.png",
                 "checkAll": "checkAll.png",
                 "uncheckAll": "uncheckAll.png",
                 "listing": "listing.png",
                 "egee_small": "egee_small.png",
                 "smallClone": "smallClone.png",
                 "file_edit": "file_edit.png",
                 "file_protect": "file_protect.png",
                 "form_CheckBox": "form_CheckBox.png",
                 "form_Select": "form_Select.png",
                 "form_PasswordBox": "form_PasswordBox.png",
                 "form_RadioButton": "form_RadioButton.png",
                 "form_TextArea": "form_TextArea.png",
                 "form_TextBox": "form_TextBox.png",
                 "form_TextBox_": "form_TextBox_.png",
                 "form_CheckBox_": "form_CheckBox_.png",
                 "form_Select_": "form_Select_.png",
                 "form_PasswordBox_": "form_PasswordBox_.png",
                 "form_RadioButton_": "form_RadioButton_.png",
                 "form_Text_": "form_Text_.png",
                 "form_TextArea_": "form_TextArea_.png",
                 "add": "add.png",
                 "add_faded": "add_faded.png",
                 "remove": "remove.png",
                 "remove_faded": "remove_faded.png",
                 "archive": "archive_small.png",
                 "unarchive": "unarchive_small.png",
                 "edit": "edit.png",
                 "edit_faded": "edit_faded.png",
                 "help": "help.png",
                 "search": "search.png",
                 "search_small": "search_small.png",
                 "stat": "stat.png",
                 "logoCERN": "CERNlogo-grey.png",
                 "timezone": "timezone.png",
                 "cern_small": "cern_small.png",
                 "home": "home.png",
                 "upCategory": "up_arrow.png",
                 "manage": "manage.png",
                 "wsignout": "wsignout.gif",
                 "arrow_next":"arrow_next.png",
                 "arrow_previous":"arrow_previous.png",
                 "dot_gray":"dot_gray.png",
                 "dot_red":"dot_red.png",
                 "dot_blue":"dot_blue.png",
                 "dot_green":"dot_green.png",
                 "dot_orange":"dot_orange.png",
                 "basket":"basket.png",
                 "ui_loading":"load_big.gif",
                 "style":"style.png",
                 "filter":"filter.png",
                 "filter_active":"filter_active.png",
                 "play":"play.png",
                 "stop":"stop.png",
                 "reload":"reload.png",
                 "play_faded":"play_faded.png",
                 "stop_faded":"stop_faded.png",
                 "accept":"accept.png",
                 "reject":"reject.png",
                 "room": "room.png",
                 "popupMenu":"popupMenu.png",
                 "roomwidgetArrow":"roomwidget_arrow.png",
                 "defaultConferenceLogo":"lecture3.png",
                 "breadcrumbArrow": "breadcrumb_arrow.png",
                 "invenio": "invenio.png",
                 "heart": "heart.png",
                 "star": "star.png",
                 "starGrey": "starGrey.png"
    }


    # default values - Administrators can update this list from the Indico
    # administration web interface
    __stylesheets = {
            "cdsagenda_olist": "CDS Agenda ordered list",
            "nicecompact":"Compact style",
            "ilc":"ILC style",
            "standard_inline_minutes":"Indico style - inline minutes",
            "lhcrrb":"LHC RRB",
            "xml":"Simple xml",
            "alice_meeting":"ALICE meeting",
            "administrative3": "Administrative style 2",
            "administrative4": "Administrative style (all material)",
            "atlas":"ATLAS Meeting",
            "text":"Simple text",
            "totem_meeting":"TOTEM Meeting",
            "administrative2":"Administrative style (with time)",
            "cdsagenda":"CDS Agenda style",
            "static":"Parallel",
            "sa":"Staff Association",
            "sa2":"Staff Association (with time)",
            "it":"IT style",
            "cdsagenda_inline_minutes":"CDS Agenda inline minutes",
            "lcg":"LCG style",
            "lhcb_meeting":"LHCb meeting",
            "egee_meeting":"EGEE meeting",
            "administrative":"Administrative style",
            "cms":"CMS Meeting",
            "standard":"Indico style",
            "lecture":"Lecture",
            "egee_lecture":"EGEE lecture",
            "event": "Event" }

    # default values - Administrators can update this list from the Indico
    # administration web interface
    __eventStylesheets = {
        "conference": [
            "it",
            "administrative3",
            "administrative4",
            "cdsagenda",
            "text",
            "egee_meeting",
            "administrative",
            "cdsagenda_olist",
            "standard",
            "nicecompact",
            "cdsagenda_inline_minutes",
            "lhcb_meeting",
            "xml",
            "static" ],
        "simple_event": [
            "it",
            "cdsagenda",
            "static",
            "lecture",
            "egee_lecture",
            "xml",
            "event" ],
        "meeting": [
            "cdsagenda_olist",
            "nicecompact",
            "ilc",
            "standard_inline_minutes",
            "lhcrrb",
            "xml",
            "alice_meeting",
            "administrative3",
            "administrative4",
            "atlas",
            "text",
            "totem_meeting",
            "administrative2",
            "cdsagenda",
            "static",
            "sa",
            "sa2",
            "it",
            "cdsagenda_inline_minutes",
            "lcg",
            "lhcb_meeting",
            "egee_meeting",
            "administrative",
            "cms",
            "standard" ]
        }

    # default values - Administrators can update this list from the Indico
    # administration web interface
    __defaultEventStylesheet = {
            "conference":"static",
            "simple_event":"lecture",
            "meeting":"standard" }

    def __init__(self, filePath = None):
        self.filePath = filePath
        self.__readConfigFile()
        self._shelf = None


    def forceReload(self):
        '''Forces Config to reread indico.conf and repopulate all of its variables'''
        # We don't use __import__ or reload because if the file changes are done too fast
        # Python doesn't see the changes and inconsistencies appear.
        #     __import__('MaKaC.common.MaKaCConfig') < DOESNT WORK
        #     reload(MaKaCConfig)                    < DOESNT WORK
        execfile(os.path.abspath(os.path.join(os.path.dirname(__file__), 'MaKaCConfig.py')))
        new_vals = locals()
        for k in self._configVars:
            if k in new_vals:
                self._configVars[k] = new_vals[k]


    def __readConfigFile(self):
        """initializes configuration parameters (Search order: indico.conf, default_values)

        IF YOU WANT TO CREATE NEW USER CONFIGURABLE OPTIONS:
        If you need to define a new configuration option you _need_ to specify it here with
        its default value and then you can put it in indico.conf.

                #### Indico will not see options that don't appear here ####
        """

        default_values = {
            'DBConnectionParams'        : ("localhost", 9675),
            'DBUserName'                : '',
            'DBPassword'                : '',
            'DBRealm'                   : '',
            'SanitizationLevel'         : 1,
            'BaseURL'                   : 'http://localhost/',
            'BaseSecureURL'             : 'https://localhost/',
            'LoginURL'                  : "",
            'RegistrationURL'           : "",
            'ShortEventTag'             : "/event/",
            'ShortCategTag'             : "/categ/",
            'ConfigurationDir'          : "/opt/indico/etc",
            'DocumentationDir'          : "/opt/indico/doc",
            'HtdocsDir'                 : "/opt/indico/htdocs",
            'LogDir'                    : "/opt/indico/log" ,
            'ArchiveDir'                : "/opt/indico/archive",
            'BinDir'                    : "/opt/indico/bin",
            'UploadedFilesTempDir'      : "/opt/indico/tmp",
            'UploadedFilesSharedTempDir': "",
            'XMLCacheDir'               : "/opt/indico/cache",
            'SmtpServer'                : 'localhost',
            'SmtpLogin'                 : '',
            'SmtpPassword'              : '',
            'SmtpUseTLS'                : 'no',
            'SupportEmail'              : 'root@localhost',
            'PublicSupportEmail'        : 'root@localhost',
            'NoReplyEmail'              : 'noreply-root@localhost',
            'IndicoSearchServer'        : '',
            'IndicoSearchClass'         : 'MaKaC.search.invenioSEA.InvenioSEA',
            'FileConverter'             : {"conversion_server": "", "response_url": "http://localhost/getConvertedFile.py"},
            'AuthenticatorList'         : ['Local'],
            'NiceLogin'                 : '',
            'NicePassword'              : '',
            'CssStylesheetName'         : 'indico.css',
            'PublicFolder'              : "/opt/indico/htdocs/results",
            'ReportNumberSystems'       : {},
            'OAILogFile'                : "/opt/indico/log/oai.log",
            'NbRecordsInResume'         : 100,
            'NbIdentifiersInResume'     : 100,
            'OAIRtExpire'               : 90000,
            'OAINamespace'              : '',
            'IconfNamespace'            : "http://localhost/",
            'IconfXSD'                  : "http://localhost/iconf.xsd",
            'RepositoryName'            : '',
            'RepositoryIdentifier'      : '',
            'ApacheUser'                : 'nobody',
            'ApacheGroup'               : 'nogroup',
            'Profile'                   : False,

            # Room Booking Related
            'LightboxCssStylesheetName' : "lightbox/lightbox.css",
            'LightboxJavascriptName'    : "lightbox/lightbox.js",
            }


        if sys.platform == 'win32':
            default_values.update({
                "ConfigurationDir"     : "C:\\indico\\etc",
                "DocumentationDir"     : "C:\\indico\\doc",
                "HtdocsDir"            : "C:\\Program Files\\Apache Group\\Apache2\\htdocs\\MaKaC",
                "LogDir"               : "C:\\indico\\log",
                "ArchiveDir"           : "C:\\indico\\archive",
                "BinDir"               : "C:\\indico\\archive",
                "UploadedFilesTempDir" : "C:\\indico\\temp",
                "XMLCacheDir"          : "C:\\indico\\cache",
                                   })


        self._configVars = {}
        declared_values = dir(MaKaCConfig)

        # When populating configuration variables indico.conf's values have priority
        for k in default_values:
            if k in declared_values:
                self._configVars[k] = MaKaCConfig.__getattribute__(k) # declared_values[k] doesn't work, don't ask me why
            else: # key is not declared in indico.conf, using its default value
                self._configVars[k] = default_values[k]


        # Variables whose value is derived automatically
        # THIS IS THE PLACE TO ADD NEW SHORTHAND OPTIONS, DONT CREATE A FUNCTION IF THE VALUE NEVER CHANGES,
        # Configuration.py will become fat again if you don't follow this advice.
        self._configVars.update({
            'TPLVars'                   : {"MaKaCHomeURL": "%sindex.py" % self.getBaseURL()},
            'FileTypes'                 : MaKaCConfig.FileTypes,
            'HelpDir'                   : os.path.join(self.getHtdocsDir(), 'ihelp'),
            'WorkerName'                : socket.getfqdn(),
            'StylesheetsDir'            : os.path.join(os.path.dirname(__file__), '..', 'webinterface', 'stylesheets'),
            'ImagesDir'                 : os.path.join(self.getHtdocsDir(), 'images'),
            'PublicURL'                 : "%s/%s" % (self.getBaseURL(), self.getPublicFolder()),
            'SystemIcons'               : self.__systemIcons,
            'Stylesheets'               : self.__stylesheets,
            'EventStylesheets'          : self.__eventStylesheets,
            'TempDir'                   : self.getUploadedFilesTempDir(),
            'UploadedFilesSharedTempDir': self.getSharedTempDir(),
            'RoomPhotosDir'             : os.path.join(self.getHtdocsDir(), 'images', "rooms", "large_photos"),
            'RoomSmallPhotosDir'        : os.path.join(self.getHtdocsDir(), 'images', "rooms", "small_photos"),
            'CssDir'                    : "%s/css/" % (self.getHtdocsDir()),
            'CssBaseURL'                : "%s/css" % self.getBaseURL(),
            'CssConfTemplateBaseURL'    : "%s/css/confTemplates" % self.getBaseURL(),
            'DefaultEventStylesheet'    : self.__defaultEventStylesheet,
            'ShortCategURL'             : '%s%s' % (self.getBaseURL(), self.getShortCategTag()),
            'ShortEventURL'             : '%s%s' % (self.getBaseURL(), self.getShortEventTag()),
            'TPLDir'                    : os.path.join(os.path.dirname(__file__), '..', 'webinterface', 'tpls'),
            'HostNameURL'               : urlparse.urlparse(self.getBaseURL())[1].split(':')[0],
            'FileConverterServerURL'    : self.getFileConverter().get("conversion_server", ""),
            'FileConverterResponseURL'  : self.getFileConverter().get("response_url", ""),
            'ImagesBaseURL'             : "%s/images" % self._configVars['BaseURL'],
            'ImagesBaseSecureURL'       : "%s/images" % self._configVars['BaseSecureURL'],
            'Version'                   : MaKaC.__version__,
                                 })

        self.__tplFiles = {}

        if self.getSanitizationLevel() not in range(4):
            raise "Invalid SanitizationLevel value (%s). Valid values: 0, 1, 2, 3" % (self._configVars['SanitizationLevel'])


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


    def getSmtpUseTLS(self):
        if self._configVars['SmtpUseTLS'] == 'yes':
            return True
        else:
            return False


    def getInstance(cls):
        """returns an instance of the Config class ensuring only a single
           instance is created. All the clients should use this method for
           setting a Config object instead of normal instantiation
        """
        if cls.__instance == None:
            cls.__instance = Config()
        return cls.__instance

    getInstance = classmethod( getInstance )


    def getCurrentDBDir(self):
        """gives back the path of the directory where the current database
           files are kept
        """
        raise "Deprecated Method"
        # return raw_input("\n\nPlease enter the path to the directory that contains the database files")


    def getDBBackupsDir(self):
        """gives back the path of the directory where the backups of the
           database files are kept
        """
        raise "Deprecated Method"
        # return raw_input("\n\nPlease enter the path to the directory that will contain the database backups [OPTIONAL]\n\n")


    def getTimezoneList(self):
        # Dont move outside, we need to call Config.getInstance() from setup.py and if
	    # the system has no pytz module then the import will break
        from pytz import all_timezones as Timezones
        return Timezones


    def getCssStylesheetName(self):
        """gives back the css stylesheet name used by Indico"""
        template = 'Default'

        # TODO: CHECK IF DB IS OPEN

        # NOTE: don't move the import outside because we need Configuration.py
        # to be loaded from setup.py and at that point we don't have db access
        # and therefore the import will fail.
        import MaKaC.common.info as info
        defTemplate = info.HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultTemplateSet()

        if (defTemplate != None and os.path.exists("%s/css/%s.css" % (self.getHtdocsDir(), defTemplate))):
            template = defTemplate

        return '%s.css' % template


    def getPublicDir(self):
        """gives back the path of the directory where the public files are kept"""
        publicFolderPath = os.path.join(self._configVars['htdocsDir'], self._configVars['publicFolder'])
        try:
            if not os.path.exists(publicFolderPath):
                os.mkdir(publicFolderPath)
        except:
            raise MaKaCError( _("It is not possible to create the folder \"results\" to store the dvd zip file. \
                    Please contact with the system administrator"))
        return publicFolderPath


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


    def getArchivedFileURL(self, localFile):
        return "%s/getFile.py?%s" % (self.getBaseURL(), localFile.getLocator().getURLForm() )


    def hasFileConverter(self):
        return self.getFileConverter().get("conversion_server", "") != ""

    def getSharedTempDir(self):
        std = self.getUploadedFilesSharedTempDir()
        if std == "":
            std = self.getUploadedFilesTempDir()
        return std
