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
from flask import request
from indico.util.contextManager import ContextManager

"""Contains the machinery that allows to access and modify in a more comfortable
and transparent way the system configuration (this is mainly done through the
Config class).
"""
import copy
import os
import urlparse
import socket
import sys

import MaKaC


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

    __systemIcons = {"new": "newleft.png",
                     "modify": "link_shadow.png",
                     "submit": "file_shadow.png",
                     "view": "view.png",
                     "group": "group.png",
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
                     "mail_grey": "mail_grey.png",
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
                     "indico_co": "indico_co.png",
                     "login": "pict_login.png",
                     "tt_time": "tt_time.png",
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
                     "badge": "badge.png",
                     "badgeMargins": "badge_margins.png",
                     "loading": "loading.gif",
                     "enabledSection": "enabledSection.png",
                     "disabledSection": "disabledSection.png",
                     "greyedOutSection": "greyedOutSection.png",
                     "tick": "tick.png",
                     "cross": "cross.png",
                     "cofee": "coffee.png",
                     "subfile": "subfile.png",
                     "file": "file.png",
                     "bigfile": "bigfile.png",
                     "smallfile": "file_small.png",
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
                     "cern_small_light": "cern_small_light.png",
                     "home": "home.png",
                     "upCategory": "up_arrow.png",
                     "manage": "manage.png",
                     "wsignout": "wsignout.gif",
                     "arrow_next": "arrow_next.png",
                     "arrow_previous": "arrow_previous.png",
                     "dot_gray": "dot_gray.png",
                     "dot_red": "dot_red.png",
                     "dot_blue": "dot_blue.png",
                     "dot_green": "dot_green.png",
                     "dot_orange": "dot_orange.png",
                     "basket": "basket.png",
                     "ui_loading": "load_big.gif",
                     "style": "style.png",
                     "filter": "filter.png",
                     "filter_active": "filter_active.png",
                     "reload": "reload.png",
                     "reload_faded": "reload_faded.png",
                     "accept": "accept.png",
                     "reject": "reject.png",
                     "room": "room.png",
                     "popupMenu": "popupMenu.png",
                     "roomwidgetArrow": "roomwidget_arrow.png",
                     "defaultConferenceLogo": "lecture3.png",
                     "breadcrumbArrow": "breadcrumb_arrow.png",
                     "heart": "heart.png",
                     "star": "star.png",
                     "starGrey": "starGrey.png",
                     "calendarWidget": "calendarWidget.png",
                     "American Express": "americanExpress.gif",
                     "Diners Club": "dinersClub.gif",
                     "JCB": "JCB.gif",
                     "Maestro": "maestro.gif",
                     "MasterCard": "masterCard.gif",
                     "PAYPAL": "PAYPAL.gif",
                     "PostFinance + card": "postFinanceCard.gif",
                     "PostFinance e-finance": "postFinanceEFinance.gif",
                     "VISA": "VISA.gif",
                     "syncOff": "sync_off.png",
                     "syncOn": "sync_on.png",
                     "facebook": "facebook.png",
                     "twitter": "twitter.png",
                     "gplus": "gplus.png",
                     "gcal": "gcal.png",
                     "link": "link.png"
                     }

    # default values - Administrators can update this list from the Indico
    # administration web interface
    __styles = {
        # Lecture styles
        "lecture":          ("Lecture",
                             os.path.join("lectures", "IndicoLecture.tpl"),
                             os.path.join("lectures", "IndicoLecture.css")),
        "egee_lecture":     ("EGEE lecture",
                             os.path.join("lectures", "IndicoLecture.tpl"),
                             os.path.join("lectures", "EGEELecture.css")),
        "event":            ("Event",
                             os.path.join("lectures", "IndicoLecture.tpl"),
                             os.path.join("lectures", "IndicoLecture.css")),

        # Administrative styles (black on white, centered)
        "administrative":   ("Administrative style",
                             os.path.join("meetings", "administrative", "Administrative.tpl"),
                             os.path.join("meetings", "administrative", "Administrative.css")),
        "administrative2":  ("Administrative style (with time)",
                             os.path.join("meetings", "administrative", "AdministrativeWithTime.tpl"),
                             os.path.join("meetings", "administrative", "AdministrativeWithTime.css")),
        "administrative4":  ("Administrative style (all material)",
                             os.path.join("meetings", "administrative", "AdministrativeAllMaterial.tpl"),
                             os.path.join("meetings", "administrative", "AdministrativeAllMaterial.css")),
        "pf":               ("Pension Fund",
                             os.path.join("meetings", "administrative", "PensionFund.tpl"),
                             os.path.join("meetings", "administrative", "PensionFund.css")),
        "lhcrrb":           ("LHC RRB",
                             os.path.join("meetings", "administrative", "LHCRBB.tpl"),
                             os.path.join("meetings", "administrative", "LHCRBB.css")),
        "sa":               ("Staff Association",
                             os.path.join("meetings", "administrative", "StaffAssociation.tpl"),
                             os.path.join("meetings", "administrative", "StaffAssociation.css")),

        # More or less standardly looking meeting styles
        "standard":         ("Indico style",
                             os.path.join("meetings", "IndicoMeeting.tpl"),
                             os.path.join("meetings", "IndicoMeeting.css")),
        "standard_inline_minutes":
                            ("Indico style - inline minutes",
                             os.path.join("meetings", "IndicoMeetingWithMinutes.tpl"),
                             os.path.join("meetings", "IndicoMeetingWithMinutes.css")),
        "ilc":              ("ILC style",
                             os.path.join("meetings", "IndicoMeeting.tpl"),
                             os.path.join("meetings", "ILC.css")),
        "alice_meeting":    ("ALICE meeting",
                             os.path.join("meetings", "IndicoMeeting.tpl"),
                             os.path.join("meetings", "ALICE.css")),
        "atlas":            ("ATLAS meeting",
                             os.path.join("meetings", "IndicoMeeting.tpl"),
                             os.path.join("meetings", "ATLAS.css")),
        "totem_meeting":    ("TOTEM meeting",
                             os.path.join("meetings", "IndicoMeeting.tpl"),
                             os.path.join("meetings", "TOTEM.css")),
        "sa2":              ("Staff Association (with time)",
                             os.path.join("meetings", "IndicoMeeting.tpl"),
                             os.path.join("meetings", "StaffAssociation.css")),
        "lcg":              ("LCG style",
                             os.path.join("meetings", "IndicoMeeting.tpl"),
                             os.path.join("meetings", "LCG.css")),
        "lhcb_meeting":     ("LHCb meeting",
                             os.path.join("meetings", "IndicoMeeting.tpl"),
                             os.path.join("meetings", "LHCb.css")),
        "egee_meeting":     ("EGEE meeting",
                             os.path.join("meetings", "IndicoMeeting.tpl"),
                             os.path.join("meetings", "EGEE.css")),
        "cms":              ("CMS meeting",
                             os.path.join("meetings", "IndicoMeeting.tpl"),
                             os.path.join("meetings", "CMS.css")),
        "endotofpet":       ("EndoTOFPET",
                             os.path.join("meetings", "Openlab.tpl"),
                             os.path.join("meetings", "EndoTOFPET.css")),
        "crystal_clear":    ("Crystal Clear",
                             os.path.join("meetings", "Openlab.tpl"),
                             os.path.join("meetings", "CrystalClear.css")),
        "openlab":          ("Openlab",
                             os.path.join("meetings", "Openlab.tpl"),
                             os.path.join("meetings", "Openlab.css")),

        # CDS Agenda styles
        "cdsagenda":        ("CDS Agenda style",
                             os.path.join("meetings", "cdsagenda", "CDSAgenda.tpl"),
                             os.path.join("meetings", "cdsagenda", "CDSAgenda.css")),
        "cdsagenda_inline_minutes":
                            ("CDS Agenda inline minutes",
                             os.path.join("meetings", "cdsagenda", "CDSAgendaWithMinutes.tpl"),
                             os.path.join("meetings", "cdsagenda", "CDSAgendaWithMinutes.css")),
        "cdsagenda_olist":  ("CDS Agenda ordered list",
                             os.path.join("meetings", "cdsagenda", "CDSAgendaOrdered.tpl"),
                             os.path.join("meetings", "cdsagenda", "CDSAgendaOrdered.css")),

        # Standard conference style
        "static":           ("Parallel", None, None),

        # Other meeting styles
        "nicecompact":      ("Compact style",
                             os.path.join("meetings", "Compact.tpl"),
                             os.path.join("meetings", "Compact.css")),
        "weeks":            ("Compact weeks",
                             os.path.join("meetings", "Weeks.tpl"),
                             os.path.join("meetings", "Weeks.css")),

        "xml":              ("Simple xml", "XML.xsl", None),
        "jacow":            ("JACoW XML", "JACoW.xsl", None),
        "text":             ("Simple text", "Text.tpl", None),
    }

    # default values - Administrators can update this list from the Indico
    # administration web interface
    __eventStylesheets = {
        "conference": [
            "administrative",
            "cdsagenda",
            "cdsagenda_inline_minutes",
            "cdsagenda_olist",
            "egee_meeting",
            "jacow",
            "lhcb_meeting",
            "nicecompact",
            "weeks",
            "standard",
            "static",
            "text",
            "xml"],
        "simple_event": [
            "cdsagenda",
            "static",
            "lecture",
            "egee_lecture",
            "jacow",
            "xml",
            "event"],
        "meeting": [
            "administrative",
            "administrative2",
            "administrative4",
            "alice_meeting",
            "atlas",
            "cdsagenda",
            "cdsagenda_inline_minutes",
            "cdsagenda_olist",
            "cms",
            "crystal_clear",
            "egee_meeting",
            "endotofpet",
            "ilc",
            "lcg",
            "lhcb_meeting",
            "lhcrrb",
            "nicecompact",
            "weeks",
            "openlab",
            "pf",
            "sa",
            "sa2",
            "standard",
            "standard_inline_minutes",
            "static",
            "text",
            "totem_meeting",
            "xml"]
        }

    # default values - Administrators can update this list from the Indico
    # administration web interface
    __defaultEventStylesheet = {
            "conference": "static",
            "simple_event": "lecture",
            "meeting": "standard" }

    default_values = {
        'DBConnectionParams'        : ("localhost", 9675),
        'DBUserName'                : '',
        'DBPassword'                : '',
        'DBRealm'                   : '',
        'RedisConnectionURL'        : None,
        'SanitizationLevel'         : 1,
        'CSRFLevel'                 : 2,
        'BaseURL'                   : 'http://localhost/',
        'BaseSecureURL'             : 'https://localhost/',
        'LoginURL'                  : "",
        'RegistrationURL'           : "",
        'ConfigurationDir'          : "/opt/indico/etc",
        'DocumentationDir'          : "/opt/indico/doc",
        'HtdocsDir'                 : "/opt/indico/htdocs",
        'LogDir'                    : "/opt/indico/log" ,
        'ArchiveDir'                : "/opt/indico/archive",
        'BinDir'                    : "/opt/indico/bin",
        'UploadedFilesTempDir'      : "/opt/indico/tmp",
        'UploadedFilesSharedTempDir': "",
        'XMLCacheDir'               : "/opt/indico/cache",
        'OfflineStore'              : "",
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
        'FileConverter'             : {"conversion_server": "", "response_url": "http://localhost/getConvertedFile.py"},
        'DisplayLoginPage'          : "yes",
        'AuthenticatorList'         : [('Local',{})],
        'ReportNumberSystems'       : {},
        'Profile'                   : 'no',
        'StaticFileMethod'          : None,
        'AuthenticatedEnforceSecure': 'no',
        'MaxUploadFilesTotalSize'   : '0',
        'MaxUploadFileSize'         : '0',
        'ForceConflicts'            : 0,
        'PropagateAllExceptions'    : False,
        'EmbeddedWebserver'         : False,
        'EmbeddedWebserverBaseURL'  : None,
        'OAuthAccessTokenTTL'       : 10000,
        'MobileURL'                 : '',
        'CheckinURL'                : 'http://indico-software.org/wiki/apps/check-in',
        'SCSSDebugInfo'             : True,
        'SessionLifetime'           : 86400 * 31,
        'RouteOldUrls'              : False,
        'CustomCountries'           : {},
        'PDFLatexProgram'           : 'pdflatex',
        'StrictLatex'               : True,
        'WorkerName'                : socket.getfqdn(),
        'CategoryCleanup'           : {}
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

    def __init__(self, filePath = None):
        self.filePath = filePath
        self.__readConfigFile()
        self._shelf = None


    def updateValues(self, newValues):
        """The argument is a dictionary.
        This function updates only the values provided by the dictionary"""
        for k in newValues:
            if k in self._configVars:
                self._configVars[k] = newValues[k]

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

    def reset(self, custom={}):
        """
        Resets the config to the default values (ignoring indico.conf) and
        sets custom options if provided
        """
        self._configVars = copy.deepcopy(self.default_values)
        self._configVars.update(custom)
        self._deriveOptions()

    def _deriveOptions(self):

        webinterface_dir = os.path.join(os.path.dirname(MaKaC.__file__), 'webinterface')

        # Variables whose value is derived automatically
        # THIS IS THE PLACE TO ADD NEW SHORTHAND OPTIONS, DONT CREATE A FUNCTION IF THE VALUE NEVER CHANGES,
        # Configuration.py will become fat again if you don't follow this advice.
        self._configVars.update({
            'TPLVars'                   : {"MaKaCHomeURL": self.getBaseURL()},
            'FileTypes'                 : FILE_TYPES,
            'HelpDir'                   : os.path.join(self.getHtdocsDir(), 'ihelp'),
            'StylesheetsDir'            : os.path.join(webinterface_dir, 'stylesheets'),
            'ImagesDir'                 : os.path.join(self.getHtdocsDir(), 'images'),
            'FontsDir'                  : os.path.join(self.getHtdocsDir(), 'fonts'),
            'JSDir'                     : os.path.join(self.getHtdocsDir(), 'js'),
            'SystemIcons'               : self.__systemIcons,
            'Styles'                    : self.__styles,
            'EventStylesheets'          : self.__eventStylesheets,
            'TempDir'                   : self.getUploadedFilesTempDir(),
            'UploadedFilesSharedTempDir': self.getSharedTempDir(),
            'RoomPhotosDir'             : os.path.join(self.getHtdocsDir(), 'images', "rooms", "large_photos"),
            'RoomSmallPhotosDir'        : os.path.join(self.getHtdocsDir(), 'images', "rooms", "small_photos"),
            'CssDir'                    : "%s/css/" % (self.getHtdocsDir()),
            'CssBaseURL'                : self.getCssBaseURL(),
            'CssConfTemplateBaseURL'    : self.getCssConfTemplateBaseURL(),
            'DefaultEventStylesheet'    : self.__defaultEventStylesheet,
            'TPLDir'                    : os.path.abspath(os.path.join(webinterface_dir, 'tpls')),
            'HostNameURL'               : urlparse.urlparse(self.getBaseURL())[1].partition(':')[0],
            'PortURL'                   : urlparse.urlparse(self.getBaseURL())[1].partition(':')[2] or '80',
            'FileConverterServerURL'    : self.getFileConverter().get("conversion_server", ""),
            'FileConverterResponseURL'  : self.getFileConverter().get("response_url", ""),
            'ImagesBaseURL'             : self.getImagesBaseURL(),
            'ImagesBaseSecureURL'       : self.getImagesBaseSecureURL(),
            'Version'                   : MaKaC.__version__,
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

        if self.getRedisConnectionURL():
            # Rest if redis is available and if we can connect
            try:
                import redis
                redis.StrictRedis.from_url(self.getRedisConnectionURL())
                # a redis ping here would be nice but we do not have a working logger yet
            except ImportError, e:
                raise MaKaCError('Could not import redis: %s' % e.message)

        if self.getStaticFileMethod() is not None and len(self.getStaticFileMethod()) != 2:
            raise MaKaCError('StaticFileMethod must be None, a string or a 2-tuple')

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
        return '%s/c/' % self.getBaseURL()

    def getShortEventURL(self):
        return '%s/e/' % self.getBaseURL()

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

    def getDisplayLoginPage(self):
        return self._yesOrNoVariable('DisplayLoginPage')

    def getAuthenticatedEnforceSecure(self):
        return self._yesOrNoVariable('AuthenticatedEnforceSecure') and self.getBaseSecureURL()

    def getInstance(cls):
        """returns an instance of the Config class ensuring only a single
           instance is created. All the clients should use this method for
           setting a Config object instead of normal instantiation
        """
        if cls.__instance == None:
            cls.__instance = Config()
        return cls.__instance

    getInstance = classmethod( getInstance )

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
        """gives back the css stylesheet name used by Indico"""
        template = 'Default'

        # TODO: CHECK IF DB IS OPEN

        # NOTE: don't move the import outside because we need Configuration.py
        # to be loaded from setup.py and at that point we don't have db access
        # and therefore the import will fail.
        import MaKaC.common.info as info
        defTemplate = info.HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultTemplateSet()

        if (defTemplate is not None and os.path.exists("%s/css/Default.%s.css" % (self.getHtdocsDir(), defTemplate))):
            template = "Default.%s" % defTemplate

        return '%s.css' % template

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

    def getPluginIconURL( self, pluginName, iconId ):
        rh = ContextManager.get('currentRH', None)

        if rh and request.is_secure and self.getBaseSecureURL():
            baseURL = self.getBaseSecureURL()
        else:
            baseURL = self.getBaseURL()
        return "%s/%s/images/%s.png"%(baseURL, pluginName, iconId)

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

    def getAuthenticatorConfigById(self, authId):
        for auth, config in self.getAuthenticatorList():
            if auth == authId:
                return config
        return {}

    def getImagesBaseURL(self):
        if ContextManager.get('offlineMode', False):
            return "static/images"
        else:
            return "%s/images" % self.getBaseURL()

    def getImagesBaseSecureURL(self):
        if ContextManager.get('offlineMode', False):
            return "static/images"
        else:
            return "%s/images" % self.getBaseSecureURL()

    def getCssBaseURL(self):
        if ContextManager.get('offlineMode', False):
            return "static/css"
        else:
            return "%s/css" % self.getBaseURL()

    def getFontsBaseURL(self):
        if ContextManager.get('offlineMode', False):
            return "static/fonts"
        else:
            return "%s/fonts" % self.getBaseURL()
