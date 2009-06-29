# -*- coding: utf-8 -*-
##
## $Id: Configuration.py,v 1.81 2009/06/24 12:13:18 eragners Exp $
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
from MaKaC.errors import MaKaCError
from MaKaC.i18n import _

class Config:
    """This class provides a common way to access and modify the configuration 
       parameters of the application. This configuration information will be 
       stored in a text file and will contain the minimal information (exaple: 
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
                 "star": "star.png"
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
            "atlas":"ATLAS Meeting",
            "text":"Simple text",
            "totem_meeting":"TOTEM Meeting",
            "administrative2":"Administrative style (with time)",
            "cdsagenda":"CDS Agenda style",
            "static":"Parallel",
            "sa":"Staff Association",
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
            "atlas",
            "text",
            "totem_meeting",
            "administrative2",
            "cdsagenda",
            "static",
            "sa",
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
        
    def __readConfigFile(self):
        """private method for mapping the contents of the configuration file
           to the object attributes
        """
        #for the moment the configuration file is just another python file 
        #containing constant definitions
        from MaKaCConfig import DB_params
        self._storageParams = DB_params

        #templating stuff
        try:
            from MaKaCConfig import TPL_dir
            self.__tplDir = TPL_dir
        except Exception:
            self.__tplDir = ""
        try:
            from MaKaCConfig import TPL_files
            self.__tplFiles = TPL_files
        except Exception:
            self.__tplFiles = {}
        try:
            from MaKaCConfig import TPL_vars
            self.__tplVars= TPL_vars
        except Exception:
            self.__tplVars = {}
        #database stuff
        try:
            from MaKaCConfig import CurrentDBPath
            self.__currdbDir = CurrentDBPath
        except Exception:
            self.__currdbDir = ""
        try:
            from MaKaCConfig import DBBackupsPath
            self.__dbbackDir = DBBackupsPath
        except Exception:
            self.__dbbackDir = ""
        #stylesheet stuff
        try:
            from MaKaCConfig import StylesheetPath
            self.__stlDir = StylesheetPath
        except Exception:
            self.__stlDir = ""

        ##################################
        # Fermi timezone awareness       #
        ##################################
 
        try:
            from MaKaCConfig import Timezones
            self.__timezones = Timezones
        except:
            self.__timezones = []

        ##################################
        # Fermi timezone awareness(end)  #
        ##################################
        try:
            from MaKaCConfig import cssStylesheetName
            self._cssStlName = cssStylesheetName
        except Exception:
            self._cssStlName = ""
        try:
            from MaKaCConfig import publicFolder
            self._publicFolder = publicFolder
        except Exception:
            self._publicFolder = ""
        try:
            from MaKaCConfig import worker
            self._worker = worker
        except Exception:
            self._worker = ""
        try:
            from MaKaCConfig import htdocsDir
            self._htdocsDir = htdocsDir
        except Exception:
            self._htdocsDir = ""
        try:
            from MaKaCConfig import URL_base
            self.__baseURL = URL_base
        except Exception:
            self.__baseURL = ""
        try:
            from MaKaCConfig import Secure_URL_base
            self.__baseSecureURL = Secure_URL_base
        except Exception:
            self.__baseSecureURL = ""
        try:
            from MaKaCConfig import supportEmail
            self._supportEmail = supportEmail
        except Exception:
            self._supportEmail = ""
        try:
            from MaKaCConfig import publicSupportAddress
            self._publicSupportAddress = publicSupportAddress
        except Exception:
            self._publicSupportAddress = ""
        from MaKaCConfig import ArchivePath
        self._archivePath = ArchivePath
        from MaKaCConfig import UploadedFilesTempDir
        self.__upFilesPath = UploadedFilesTempDir
        if not os.access( self.__upFilesPath, os.F_OK ):
            os.makedirs( self.__upFilesPath )
        from MaKaCConfig import FileTypes
        self.__fileTypes = FileTypes
        from MaKaCConfig import ImagesDir
        self.__imagesDir = ImagesDir
        from MaKaCConfig import ImagesBaseURL
        self.__imagesURL = ImagesBaseURL
        try:
            from MaKaCConfig import ImagesBaseSecureURL
            self.__imagesSecureURL = ImagesBaseSecureURL
        except ImportError:
            self.__imagesSecureURL = "" 
        try:
            from MaKaCConfig import iM2RegisterURL
        except ImportError:
            iM2RegisterURL = ""
        self.__iM2RegisterURL = iM2RegisterURL
        try:
            from MaKaCConfig import iM2SupportEmail
        except ImportError:
            iM2SupportEmail = ""
        self.__iM2SupportEmail = iM2SupportEmail
        try:
            from MaKaCConfig import iM2Password
        except ImportError:
            iM2Password = ""
        self.__iM2Password = iM2Password
        try:
            from MaKaCConfig import OAILogFile
        except ImportError:
            OAILogFile = ""
        self.__OAILogFile = OAILogFile

        try:
            from MaKaCConfig import logDir
        except ImportError:
            logDir = ""
        self.__logDir = logDir
        
        try:
            from MaKaCConfig import namespace
        except ImportError:
            namespace = ""
        self._namespace = namespace
    
        try:
            from MaKaCConfig import iconfNamespace
        except ImportError:
            iconfNamespace = ""
        self._iconfNamespace = iconfNamespace
        
        try:
            from MaKaCConfig import iconfXSD
        except ImportError:
            iconfXSD=""
        self._iconfXSD = iconfXSD
        
        try:
            from MaKaCConfig import repositoryName
        except ImportError:
            repositoryName = ""
        self._repositoryName = repositoryName
        
        try:
            from MaKaCConfig import repositoryIdentifier
        except ImportError:
            repositoryIdentifier = ""
        self._repositoryIdentifier = repositoryIdentifier
        
        try:
            from MaKaCConfig import nb_records_in_resume
        except ImportError:
            nb_records_in_resume = ""
        self._nb_records_in_resume = nb_records_in_resume
        
        try:
            from MaKaCConfig import nb_identifiers_in_resume
        except ImportError:
            nb_identifiers_in_resume = ""
        self._nb_identifiers_in_resume = nb_identifiers_in_resume
        
        try:
            from MaKaCConfig import oai_rt_expire
        except ImportError:
            oai_rt_expire = ""
        self._oai_rt_expire = oai_rt_expire
        
        try:
            from MaKaCConfig import SMTPServer
        except ImportError:
            SMTPServer = ""
        self.smtpServer = SMTPServer
        
        try:
            from MaKaCConfig import SMTPLogin
        except ImportError:
            SMTPLogin = ""
        self.smtpLogin = SMTPLogin
        try:
            from MaKaCConfig import SMTPPassword
        except ImportError:
            SMTPPassword = ""
        self.smtpPassword = SMTPPassword
        try:
            from MaKaCConfig import SMTPUseTLS
        except ImportError:
            SMTPUseTLS = ""
        self.smtpUseTLS = SMTPUseTLS

        try:
            from MaKaCConfig import indicoSearchServer
        except ImportError:
            indicoSearchServer = ""
        self.indicoSearchServer = indicoSearchServer
                
        try:
            from MaKaCConfig import indicoFooter
        except ImportError:
            indicoFooter = ""
        self.indicoFooter = indicoFooter

        try:
            from MaKaCConfig import loginURL
        except ImportError:
            loginURL = ""
        self.loginURL = loginURL

        try:
            from MaKaCConfig import regURL
        except ImportError:
            regURL = ""
        self.regURL = regURL

        try:
            from MaKaCConfig import shortEventURL
        except ImportError:
            shortEventURL = ""
        self.shortEventURL = shortEventURL

        try:
            from MaKaCConfig import shortCategURL
        except ImportError:
            shortCategURL = ""
        self.shortCategURL = shortCategURL

        try:
            from MaKaCConfig import authenticatorList
        except ImportError:
            authenticatorList = ""
        self.authenticatorList = authenticatorList
        
        try:
            from MaKaCConfig import NiceLogin
        except ImportError:
            NiceLogin = ""
        self.NiceLogin = NiceLogin
        
        try:
            from MaKaCConfig import NicePassword
        except ImportError:
            NicePassword = ""
        self.NicePassword = NicePassword
        
        try:
            from MaKaCConfig import XMLAbstractPath
        except ImportError:
            XMLAbstractPath = ""
        self.XMLAbstractPath = XMLAbstractPath

        try:
            from MaKaCConfig import DBCacheDir
        except ImportError:
            DBCacheDir=""
        self._dbCacheDir=DBCacheDir
        
        try:
            from MaKaCConfig import XMLCacheDir
        except ImportError:
            XMLCacheDir=""
        self._XMLCacheDir=XMLCacheDir
        
        try:
            from MaKaCConfig import DBUserName
        except ImportError:
            DBUserName=""
        self._DBUserName=DBUserName
        
        try:
            from MaKaCConfig import DBPassword
        except ImportError:
            DBPassword=""
        self._DBPassword=DBPassword
        
        try:
            from MaKaCConfig import DBRealm
        except ImportError:
            DBRealm=""
        self._DBRealm=DBRealm
        
        try:
            from MaKaCConfig import version
        except ImportError:
            version=""
        self._version=version

        try:
            from MaKaCConfig import ReportNumberSystems
        except ImportError:
            ReportNumberSystems={}
        self._reportNumberSystems=ReportNumberSystems

        try:
            from MaKaCConfig import fileConverter
        except ImportError:
            fileConverter={}
        self._fileConverter=fileConverter
        
        try:
            from MaKaCConfig import sanitaryLevel
        except ImportError:
            sanitaryLevel="1"
        self._sanitaryLevel=sanitaryLevel


    def getInstance( cls ):
        """returns an instance of the Config class ensuring only a single 
           instance is created. All the clients should use this method for
           setting a Config object instead of normal instantiation
        """
        if cls.__instance == None:
            cls.__instance = Config()
        return cls.__instance
    
    getInstance = classmethod( getInstance )

    def getDBConnectionParams( self ):
        """gives back the params for connecting to the DB"""
        return self._storageParams
    
    def getCurrentDBDir(self):
        """gives back the path of the directory where the current database
           files are kept
        """
        return self.__currdbDir

    def getDBBackupsDir(self):
        """gives back the path of the directory where the backups of the
           database files are kept
        """
        return self.__dbbackDir

    ######################################
    # Fermi timezone awareness           #
    ######################################
 
    def getTimezoneList(self):
        try:
            return self.__timezones
        except KeyError:
            return []
 
    ######################################
    # Fermi timezone awareness(end)      #
    ######################################

    def getStylesheetsDir(self):
        """gives back the path of the directory where the stylesheet files
           are kept
        """
        return self.__stlDir

    def getStylesheets(self):
        """gives back the entire stylesheet list. 
        """
        return self.__stylesheets
    
    def getEventStylesheets(self):
        """gives back the entire stylesheet/event association list. 
        """
        return self.__eventStylesheets
    
    def getDefaultEventStylesheet(self):
        """gives back the default stylesheet/event association
        """
        return self.__defaultEventStylesheet

    def getCssDir(self):
        return "%s/css/" % (self._htdocsDir)

    def getCssBaseURL(self):
        return "%s/css"%self.getBaseURL()
    
    def getCssConfTemplateBaseURL(self):
        return "%s/confTemplates"%self.getCssBaseURL()

    
    def getCssStylesheetName( self , default = False ):
        """gives back the css stylesheet name used by Indico"""
        template = 'Default'
        
        # TODO: CHECK IF DB IS OPEN
        
        if not default:        
            import MaKaC.common.info as info
            
            defTemplate = info.HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultTemplateSet()    
            
            if ((defTemplate != None) and
                os.path.exists("%s/css/%s.css" % (self._htdocsDir, defTemplate))):
                template = defTemplate
            
        return template+'.css'

    def getHtdocsDir( self ):
        """gives back the path of the directory where the htdocs are kept"""
        return self._htdocsDir

    def getWorkerName( self ):
        """gives back the name of the local worker in case of load balancing"""
        return self._worker

    def getPublicDir( self ):
        """gives back the path of the directory where the public files are kept"""
        publicFolderPath = os.path.join(self._htdocsDir, self._publicFolder)
        try:
            if not os.path.exists(publicFolderPath):
                os.mkdir(publicFolderPath)
        except:
            raise MaKaCError( _("It is not possible to create the folder \"results\" to store the dvd zip file. \
                    Please contact with the system administrator"))
        return publicFolderPath

    def getPublicURL( self ):
        """gives back the path of the directory where the public files are kept"""
        return "%s/%s"%(self.getBaseURL(), self._publicFolder)

    def getTPLDir(self):
        """gives back the path of the directory where the web template files
           are kept
        """
        return self.__tplDir

    def getTPLFile(self, tplId):
        """gives back the template file name associated to a certain page of 
           the web interface. If no TPL file was specified it returns the 
           empty string.
           Params:
                tplId -- unique identifier of the web interface page (normally
                    the web page class string)
        """
        try:
            return self.__tplFiles[tplId]
        except KeyError:
            return ""

    def getTPLVars(self):
        """gives back the user configured variables that must be available in
           any template file.
        """
        vars = self.__tplVars.copy()
        vars["imagesDir"] = self.getImagesBaseURL()
        return vars

    def getBaseURL(self):
        """gives back the base URL of the access point to the web interface.
        """
        return self.__baseURL
    
    def getBaseSecureURL(self):
        return self.__baseSecureURL
        
    def getHostNameURL(self):
        """gives back the host name of the base URL.
        """
        hostName = urlparse.urlparse(self.getBaseURL())[1]
        return hostName.split(':')[0]

    def getImagesBaseURL(self):
        return self.__imagesURL
        
    def getImagesBaseSecureURL(self):
        return self.__imagesSecureURL

    def getImagesDir( self ):
        return self.__imagesDir

    def getRoomPhotosDir( self ):
        return os.path.join( self.getImagesDir(), "rooms", "large_photos" )
        #return os.path.join( self.getArchivePath(), "rooms" )
    
    def getRoomSmallPhotosDir( self ):
        return os.path.join( self.getImagesDir(), "rooms", "small_photos" )
        #return os.path.join( self.getArchivePath(), "small_rooms" )

    def getCategoryIconPath( self, categid ):
        return "%s/categicon/%s.png" % (self.getImagesDir(), categid)
        
    def getCategoryIconURL( self, categid ):
        return "%s/categicon/%s.png" % (self.getImagesBaseURL(), categid)
        
    def getArchivePath( self ):
        """returns the path to the local repository file system space"""
        return self._archivePath

    def getUploadedFilesPath( self ):
        """returns the path to the temporary directory where uploaded files
            can be temporarily kept"""
        return self.__upFilesPath   
    
    getTempDir = getUploadedFilesPath

    def getFileType( self, fileExtension ):
        """returns the file type corresponding to the specified file extension
        """
        if fileExtension.strip().upper() in self.__fileTypes:
            return fileExtension.strip().upper()
        return ""

    def getFileTypeDescription( self, fileType ):
        """returns the configured file type description for the specified file
            type.
        """
        if fileType in self.__fileTypes:
            return self.__fileTypes[fileType][0]
        return ""
    
    def getFileTypeMimeType( self, fileType ):
        """returns the configured mime-type for the specified file type
        """
        if fileType in self.__fileTypes:
            return self.__fileTypes[fileType][1]
        return "unknown"

    def getFileTypeIconURL( self, fileType ):
        if fileType == "":
            return ""
        try:
            icon = self.__fileTypes[fileType][2]
        except IndexError:
            return ""
        except KeyError:
            return ""
        if icon == "":
            return ""
        iconPath = os.path.join( self.__imagesDir, icon )
        if not os.access( iconPath, os.F_OK ):
            return ""
        return "%s/%s"%( self.__imagesURL, icon )

    def getIconDir(self):
        return self.__imagesDir

    def getSystemIconURL( self, id ):
        if id not in self.__systemIcons:
            return "%s/%s"%(self.getImagesBaseURL(), id )
        return "%s/%s"%(self.getImagesBaseURL(), self.__systemIcons[ id ])
    
    def getSystemIconFileName(self, id):
        if id not in self.__systemIcons:
            return id
        return self.__systemIcons[id]

    def getSystemIcons(self):
        return self.__systemIcons

    def getArchivedFileURL( self, localFile ):
        return "%s/getFile.py?%s"%(self.getBaseURL(), localFile.getLocator().getURLForm() )

    def getOAILogFile(self):
        return self.__OAILogFile
    
    def getOAINameSpace(self):
        return self._namespace

    def getLogDir(self):
        return self.__logDir
    
    def getIconfNamespace(self):
        return self._iconfNamespace
    
    def getIconfXSD(self):
        return self._iconfXSD
    
    def getRepositoryName(self):
        return self._repositoryName
    
    def getRepositoryIdentifier(self):
        return self._repositoryIdentifier
    
    def getNb_records_in_resume(self):
        return self._nb_records_in_resume
    
    def getNb_identifiers_in_resume(self):
        return self._nb_identifiers_in_resume
    
    def getOai_rt_expire(self):
        return self._oai_rt_expire
    
    def getSmtpServer(self):
        return self.smtpServer
    
    def getSmtpLogin(self):
        return self.smtpLogin
    
    def getSmtpPassword(self):
        return self.smtpPassword
    
    def getSmtpUseTLS(self):
        if self.smtpUseTLS.lower() == "yes":
            return True
        return False

    def getIndicoSearchServer(self):
        return self.indicoSearchServer
    
    def getIndicoFooter(self):
        return self.indicoFooter
    
    def getLoginURL(self):
        return self.loginURL

    def getRegistrationURL(self):
        return self.regURL

    def getShortEventURL(self):
        return self.shortEventURL

    def getShortCategURL(self):
        return self.shortCategURL

    def getAuthenticatorList(self):
        return self.authenticatorList
    
    def getNiceLogin(self):
        return self.NiceLogin
    
    def getNicePassword(self):
        return self.NicePassword
    
    def getXMLAbstractPath(self):
        return self.XMLAbstractPath

    def getSupportEmail( self ):
        return self._supportEmail
    
    def getPublicSupportEmail( self ):
        return self._publicSupportAddress
    
    def getDBCacheDir( self ):
        return self._dbCacheDir
    
    def getXMLCacheDir( self ):
        return self._XMLCacheDir
    
    def getDBUserName( self ):
        return self._DBUserName
    
    def getDBPassword( self ):
        return self._DBPassword
    
    def getDBRealm( self ):
        return self._DBRealm

    def getVersion( self ):
        return self._version

    def hasFileConverter(self):
        return self._fileConverter.get("conversion_server","") != ""

    def getFileConverterServerURL( self ):
        return self._fileConverter.get("conversion_server","")

    def getFileConverterResponseURL( self ):
        return self._fileConverter.get("response_url","")

    def getReportNumberSystems(self):
        return self._reportNumberSystems

    def getSanitaryLevel(self):
        return self._sanitaryLevel


    # === ROOM BOOKING RELATED ===============================================

    def getLightboxCssStylesheetName( self ):
        return "lightbox/lightbox.css"

    def getLightboxJavascriptName( self ):
        return "lightbox/lightbox.js"


#if __name__ == "__main__":
#
# a=Config.getInstance()
# print a
#  print a.getDBConnection()
#  print "hola"
