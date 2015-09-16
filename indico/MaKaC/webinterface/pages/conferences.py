# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import collections
from flask import session, request, render_template
import os
import re

from datetime import timedelta, datetime
from xml.sax.saxutils import quoteattr

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.linking as linking
import MaKaC.webinterface.navigation as navigation
import MaKaC.schedule as schedule
import MaKaC.conference as conference
import MaKaC.common.filters as filters
from MaKaC.common.utils import isStringHTML
import MaKaC.common.utils
import MaKaC.review as review
from MaKaC.review import AbstractTextField
from MaKaC.webinterface.pages.base import WPDecorated
from MaKaC.webinterface.common.tools import strip_ml_tags, escape_html
from MaKaC.webinterface.common.abstractStatusWrapper import AbstractStatusList
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.common.output import outputGenerator
from MaKaC.webinterface.common.timezones import TimezoneRegistry
from MaKaC.PDFinterface.base import PDFSizes
from pytz import timezone
from MaKaC.common.timezoneUtils import nowutc, DisplayTZ
from MaKaC.conference import EventCloner
from MaKaC.badgeDesignConf import BadgeDesignConfiguration
from MaKaC.posterDesignConf import PosterDesignConfiguration
from MaKaC.webinterface.pages import main
from MaKaC.webinterface.pages import base
import MaKaC.common.info as info
from indico.util.i18n import i18nformat, _, ngettext
from indico.util.date_time import format_time, format_date, format_datetime
from indico.util.string import safe_upper
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.conference import IConferenceEventInfoFossil
from MaKaC.common.Conversion import Conversion
from indico.modules import ModuleHolder
from indico.modules.auth.util import url_for_logout
from MaKaC.conference import Session, Contribution
from indico.core.config import Config
from MaKaC.common.utils import formatDateTime
from MaKaC.webinterface.general import WebFactory
from MaKaC.common.TemplateExec import render

from indico.core import signals
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.modules.events.layout import layout_settings
from indico.modules.events.layout.util import (build_menu_entry_name, get_css_url, get_menu_entry_by_name,
                                               menu_entries_for_event)
from indico.modules.users.util import get_user_by_email
from indico.util import json
from indico.util.signals import values_from_signal
from indico.util.string import to_unicode
from indico.web.flask.util import url_for
from indico.web.menu import render_sidemenu

LECTURE_SERIES_RE = re.compile(r'^part\d+$')


def stringToDate(str):

    # Don't delete this dictionary inside comment. Its purpose is to
    # add the dictionary in the language dictionary during the extraction!
    # months = { _("January"): 1, _("February"): 2, _("March"): 3, _("April"): 4,
    #            _("May"): 5, _("June"): 6, _("July"): 7, _("August"): 8,
    #            _("September"): 9, _("October"): 10, _("November"): 11, _("December"): 12 }

    months = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12
    }
    [day, month, year] = str.split("-")
    return datetime(int(year), months[month], int(day))


class WPConferenceBase(base.WPDecorated):

    def __init__(self, rh, conference, **kwargs):
        WPDecorated.__init__(self, rh, **kwargs)
        self._navigationTarget = self._conf = conference
        tz = self._tz = DisplayTZ(rh._aw, self._conf).getDisplayTZ()
        sDate = self.sDate = self._conf.getAdjustedScreenStartDate(tz)
        eDate = self.eDate = self._conf.getAdjustedScreenEndDate(tz)
        dates = " (%s)" % format_date(sDate, format='long')
        if sDate.strftime("%d%B%Y") != eDate.strftime("%d%B%Y"):
            if sDate.strftime("%B%Y") == eDate.strftime("%B%Y"):
                dates = " (%s-%s)" % (sDate.strftime("%d"), format_date(eDate, format='long'))
            else:
                dates = " (%s - %s)" % (format_date(sDate, format='long'), format_date(eDate, format='long'))
        self._setTitle("%s %s" % (strip_ml_tags(self._conf.getTitle()), dates))

    def _getFooter(self):
        """
        """
        wc = wcomponents.WFooter()

        p = {"modificationDate": format_datetime(self._conf.getModificationDate(), format='d MMMM yyyy H:mm'),
             "subArea": self._getSiteArea()
             }
        return wc.getHTML(p)

    def getLogoutURL(self):
        return url_for_logout(str(urlHandlers.UHConferenceDisplay.getURL(self._conf)))


class WPConferenceDisplayBase(WPConferenceBase):
    pass


class WPConferenceDefaultDisplayBase( WPConferenceBase):
    navigationEntry = None
    menu_entry_plugin = None
    menu_entry_name = None

    def getJSFiles(self):
        return (WPConferenceBase.getJSFiles(self) + self._includeJSPackage('Display') +
                self._includeJSPackage('MaterialEditor'))

    def _getFooter( self ):
        wc = wcomponents.WFooter()
        p = {"modificationDate": format_datetime(self._conf.getModificationDate(), format='d MMMM yyyy H:mm'),
                "subArea": self._getSiteArea()}

        cid = self._conf.getUrlTag().strip() or self._conf.getId()
        p["shortURL"] =  Config.getInstance().getShortEventURL() + cid

        return wc.getHTML(p)

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WConferenceHeader( self._getAW(), self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.getId(), \
                             "dark": True} )

    @property
    def sidemenu_option(self):
        if not self.menu_entry_name:
            return None
        name = build_menu_entry_name(self.menu_entry_name, self.menu_entry_plugin)
        entry = get_menu_entry_by_name(name, self._conf)
        if entry:
            return entry.id

    def _getNavigationBarHTML(self):
        item=None
        if self.navigationEntry:
            item = self.navigationEntry()
        itemList = []
        while item is not None:
            if itemList == []:
                itemList.insert(0, wcomponents.WTemplated.htmlText(item.getTitle()) )
            else:
                itemList.insert(0, """<a href=%s>%s</a>"""%( quoteattr(str(item.getURL(self._navigationTarget))), wcomponents.WTemplated.htmlText(item.getTitle()) ) )
            item = item.getParent(self._navigationTarget)
        itemList.insert(0, i18nformat("""<a href=%s> _("Home")</a>""")%quoteattr(str(urlHandlers.UHConferenceDisplay.getURL(self._conf))) )
        return " &gt; ".join(itemList)

    def _applyConfDisplayDecoration( self, body ):
        drawer = wcomponents.WConfTickerTapeDrawer(self._conf, self._tz)
        frame = WConfDisplayFrame( self._getAW(), self._conf )

        frameParams = {
            "confModifURL": urlHandlers.UHConferenceModification.getURL(self._conf),
            "logoURL": self.logo_url,
            "currentURL": request.url,
            "nowHappening": drawer.getNowHappeningHTML(),
            "simpleTextAnnouncement": drawer.getSimpleText(),
            'active_menu_entry_id': self.sidemenu_option
        }
        if self.event.has_logo:
            frameParams["logoURL"] = self.logo_url

        body = """
            <div class="confBodyBox clearfix">

                                    <div>
                                        <div></div>
                                        <div class="breadcrumps">%s</div>
                                    </div>
                <!--Main body-->
                                    <div class="mainContent">
                                        <div class="col2">
                                        %s
                                        </div>
                                  </div>
            </div>""" % (self._getNavigationBarHTML(), body)
        return frame.getHTML(body, frameParams)

    def _getHeadContent(self):
        path = self._getBaseURL()
        try:
            timestamp = os.stat(__file__).st_mtime
        except OSError:
            timestamp = 0
        printCSS = '<link rel="stylesheet" type="text/css" href="{}/css/Conf_Basic.css?{}">'.format(path, timestamp)
        theme_url = get_css_url(self._conf.as_event)
        if theme_url:
            printCSS += '<link rel="stylesheet" type="text/css" href="{url}">'.format(url=theme_url)

        # Include MathJax

        return '\n'.join([
            printCSS,
            WConfMetadata(self._conf).getHTML(),                   # confMetadata
            render('js/mathjax.config.js.tpl'),                    # mathJax
            '\n'.join('<script src="{0}" type="text/javascript"></script>'.format(url)
                      for url in self._asset_env['mathjax_js'].urls())
        ])

    def _applyDecoration( self, body ):
        self.event = self._conf.as_event
        self.logo_url = self.event.logo_url if self.event.has_logo else None
        body = self._applyConfDisplayDecoration( body )
        return WPConferenceBase._applyDecoration(self, to_unicode(body))


class WConfMetadata(wcomponents.WTemplated):
    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        v = wcomponents.WTemplated.getVars( self )
        minfo =  info.HelperMaKaCInfo.getMaKaCInfoInstance()

        v['site_name'] = minfo.getTitle()
        v['fb_config'] = minfo.getSocialAppConfig().get('facebook', {})

        event = self._conf.as_event
        v['image'] = event.logo_url if event.has_logo else Config.getInstance().getSystemIconURL("logo_indico")
        v['description'] = strip_ml_tags(self._conf.getDescription()[:500])
        return v


class WConfDisplayFrame(wcomponents.WTemplated):

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf
        self.event = self._conf.as_event

    def getHTML(self, body, params):
        self._body = body
        return wcomponents.WTemplated.getHTML( self, params )

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["logo"] = ""
        if self.event.has_logo:
            vars["logoURL"] = self.event.logo_url
            vars["logo"] = "<img src=\"%s\" alt=\"%s\" border=\"0\" class=\"confLogo\" >"%(vars["logoURL"], escape_html(self._conf.getTitle(), escape_quotes = True))
        vars["confTitle"] = self._conf.getTitle()
        vars["displayURL"] = urlHandlers.UHConferenceDisplay.getURL(self._conf)
        vars["imgConferenceRoom"] = Config.getInstance().getSystemIconURL( "conferenceRoom" )
        tz = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        adjusted_sDate = self._conf.getAdjustedScreenStartDate(tz)
        adjusted_eDate = self._conf.getAdjustedScreenEndDate(tz)

        vars["timezone"] = tz
        vars["confDateInterval"] = i18nformat("""_("from") %s _("to") %s""") % (
            format_date(adjusted_sDate, format='long'), format_date(adjusted_eDate, format='long'))
        if adjusted_sDate.strftime("%d%B%Y") == \
                adjusted_eDate.strftime("%d%B%Y"):
            vars["confDateInterval"] = format_date(adjusted_sDate, format='long')
        elif adjusted_sDate.strftime("%B%Y") == adjusted_eDate.strftime("%B%Y"):
            vars["confDateInterval"] = "%s-%s %s"%(adjusted_sDate.day, adjusted_eDate.day, format_date(adjusted_sDate, format='MMMM yyyy'))
        vars["confLocation"] = ""
        if self._conf.getLocationList():
            vars["confLocation"] =  self._conf.getLocationList()[0].getName()
        vars["body"] = self._body
        vars["supportEmail"] = ""
        vars["supportTelephone"] = ""
        vars['menu'] = menu_entries_for_event(self._conf)
        vars['support_info'] = self._conf.getSupportInfo()

        vars["bgColorCode"] = layout_settings.get(self._conf, 'header_background_color').replace("#", "")
        vars["textColorCode"] = layout_settings.get(self._conf, 'header_text_color').replace("#", "")

        vars["confId"] = self._conf.getId()
        vars["conf"] = self._conf
        return vars


class WConfDisplayMenu(wcomponents.WTemplated):

    def __init__(self, menu):
        wcomponents.WTemplated.__init__(self)
        self._menu = menu


class WConfDetailsBase( wcomponents.WTemplated ):

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        tz = DisplayTZ(self._aw,self._conf).getDisplayTZ()
        vars["timezone"] = tz

        description = self._conf.getDescription()
        vars["description_html"] = isStringHTML(description)
        vars["description"] = description

        sdate, edate = self._conf.getAdjustedScreenStartDate(tz), self._conf.getAdjustedScreenEndDate(tz)
        fsdate, fedate = format_date(sdate, format='medium'), format_date(edate, format='medium')
        fstime, fetime = sdate.strftime("%H:%M"), edate.strftime("%H:%M")

        vars["dateInterval"] = (fsdate, fstime, fedate, fetime)

        vars["location"] = None
        vars["address"] = None
        vars["room"] = None

        location = self._conf.getLocation()
        if location:
            vars["location"] = location.getName()
            vars["address"] = location.getAddress()

            room = self._conf.getRoom()
            if room and room.getName():
                roomLink = linking.RoomLinker().getHTMLLink(room, location)
                vars["room"] = roomLink

        vars["chairs"] = self._conf.getChairList()
        vars["attachments"] = self._conf.attached_items
        vars["conf"] = self._conf

        info = self._conf.getContactInfo()
        vars["moreInfo_html"] = isStringHTML(info)
        vars["moreInfo"] = info
        vars["actions"] = ''
        vars["isSubmitter"] = self._conf.as_event.can_manage(session.user, 'submit')

        regform = self._conf.getRegistrationForm()
        if regform:
            vars["registration_enabled"] = regform.isActivated()
            vars["in_registration_period"] = regform.inRegistrationPeriod(nowutc())
            vars["in_modification_period"] = regform.inModificationPeriod()
            vars["registration_deadline"] = format_date(regform.getEndRegistrationDate())
            vars["modification_deadline"] = format_date(regform.getModificationEndDate())
            vars["ticket_enabled"] = regform.getETicket().isEnabled()
            if session.avatar:
                vars["registrant"] = session.avatar.getRegistrantById(self._conf.getId())
        return vars


class WConfDetailsFull(WConfDetailsBase):
    pass


#---------------------------------------------------------------------------


class WConfDetails:

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def getHTML( self, params ):
        return WConfDetailsFull( self._aw, self._conf ).getHTML( params )


class WPConferenceDisplay(WPConferenceDefaultDisplayBase):
    menu_entry_name = 'overview'

    def getCSSFiles(self):
        return (WPConferenceDefaultDisplayBase.getCSSFiles(self)
                + self._asset_env['eventservices_sass'].urls()
                + self._asset_env['event_display_sass'].urls())

    def _getBody(self, params):

        wc = WConfDetails(self._getAW(), self._conf)
        pars = {"modifyURL": urlHandlers.UHConferenceModification.getURL(self._conf),
                "sessionModifyURLGen": urlHandlers.UHSessionModification.getURL,
                "contribModifyURLGen": urlHandlers.UHContributionModification.getURL,
                "subContribModifyURLGen": urlHandlers.UHSubContribModification.getURL}
        return wc.getHTML(pars)

    def _getFooter(self):
        wc = wcomponents.WEventFooter(self._conf)
        return wc.getHTML()


class WSentMail  (wcomponents.WTemplated):
    def __init__(self,conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["BackURL"]=urlHandlers.UHConferenceDisplay.getURL(self._conf)
        return vars


class WPSentEmail( WPConferenceDefaultDisplayBase ):
    def _getBody(self,params):
        wc = WSentMail(self._conf)
        return wc.getHTML()

class WEmail(wcomponents.WTemplated):

    def __init__(self,conf,user,toUsers):
        self._conf = conf
        self._from = user
        self._to = toUsers

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        if vars.get("from", None) is None :
            vars["FromName"] = self._from
        vars["fromUser"] = self._from
        vars["toUsers"] =  self._to
        if vars.get("postURL",None) is None :
            vars["postURL"]=urlHandlers.UHConferenceSendEmail.getURL(self._to)
        if vars.get("subject", None) is None :
            vars["subject"]=""
        if vars.get("body", None) is None :
            vars["body"]=""
        return vars

class WPEMail ( WPConferenceDefaultDisplayBase ):

    def _getBody(self,params):
        toemail = params["emailto"]
        wc = WEmail(self._conf, self._getAW().getUser(), toemail)
        params["fromDisabled"] = True
        params["toDisabled"] = True
        params["ccDisabled"] = True
        return wc.getHTML(params)

class WPXSLConferenceDisplay(WPConferenceBase):
    """
    Use this class just to transform to XML
    """
    menu_entry_name = 'overview'

    def __init__(self, rh, conference, view, type, params):
        WPConferenceBase.__init__(self, rh, conference)
        self._params = params
        self._view = view
        self._conf = conference
        self._type = type
        self._firstDay = params.get("firstDay")
        self._lastDay = params.get("lastDay")
        self._daysPerRow = params.get("daysPerRow")

    def _getFooter(self):
        """
        """
        return ""

    def _getHTMLHeader(self):
        return ""

    def _applyDecoration(self, body):
        """
        """
        return to_unicode(body)

    def _getHTMLFooter(self):
        return ""

    def _getBodyVariables(self):
        pars = { \
        "modifyURL": urlHandlers.UHConferenceModification.getURL( self._conf ), \
        "iCalURL": urlHandlers.UHConferenceToiCal.getURL(self._conf), \
        "cloneURL": urlHandlers.UHConfClone.getURL( self._conf ), \
        "sessionModifyURLGen": urlHandlers.UHSessionModification.getURL, \
        "contribModifyURLGen": urlHandlers.UHContributionModification.getURL, \
        "subContribModifyURLGen": urlHandlers.UHSubContribModification.getURL}

        pars.update({ 'firstDay' : self._firstDay, 'lastDay' : self._lastDay, 'daysPerRow' : self._daysPerRow })
        return pars

    def _getBody(self, params):
        body_vars = self._getBodyVariables()
        view = self._view
        outGen = outputGenerator(self._getAW())
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        if styleMgr.existsXSLFile(self._view):
            if self._params.get("detailLevel", "") == "contribution" or self._params.get("detailLevel", "") == "":
                includeContribution = 1
            else:
                includeContribution = 0
            body = outGen.getFormattedOutput(self._rh, self._conf, styleMgr.getXSLPath(self._view), body_vars, 1,
                                             includeContribution, 1, 1, self._params.get("showSession", ""),
                                             self._params.get("showDate", ""))
            return body
        else:
            return _("Cannot find the %s stylesheet") % view


class WPTPLConferenceDisplay(WPXSLConferenceDisplay, object):
    """
    Overrides XSL related functions in WPXSLConferenceDisplay
    class and re-implements them using normal Indico templates.
    """

    def __init__(self, rh, conference, view, type, params):
        WPXSLConferenceDisplay.__init__(self, rh, conference, view, type, params)
        imagesBaseURL = Config.getInstance().getImagesBaseURL()
        self._types = {
            "pdf"   :{"mapsTo" : "pdf",   "imgURL" : os.path.join(imagesBaseURL, "pdf_small.png"),  "imgAlt" : "pdf file"},
            "doc"   :{"mapsTo" : "doc",   "imgURL" : os.path.join(imagesBaseURL, "word.png"),       "imgAlt" : "word file"},
            "docx"  :{"mapsTo" : "doc",   "imgURL" : os.path.join(imagesBaseURL, "word.png"),       "imgAlt" : "word file"},
            "ppt"   :{"mapsTo" : "ppt",   "imgURL" : os.path.join(imagesBaseURL, "powerpoint.png"), "imgAlt" : "powerpoint file"},
            "pptx"  :{"mapsTo" : "ppt",   "imgURL" : os.path.join(imagesBaseURL, "powerpoint.png"), "imgAlt" : "powerpoint file"},
            "xls"   :{"mapsTo" : "xls",   "imgURL" : os.path.join(imagesBaseURL, "excel.png"),      "imgAlt" : "excel file"},
            "xlsx"  :{"mapsTo" : "xls",   "imgURL" : os.path.join(imagesBaseURL, "excel.png"),      "imgAlt" : "excel file"},
            "sxi"   :{"mapsTo" : "odp",   "imgURL" : os.path.join(imagesBaseURL, "impress.png"),    "imgAlt" : "presentation file"},
            "odp"   :{"mapsTo" : "odp",   "imgURL" : os.path.join(imagesBaseURL, "impress.png"),    "imgAlt" : "presentation file"},
            "sxw"   :{"mapsTo" : "odt",   "imgURL" : os.path.join(imagesBaseURL, "writer.png"),     "imgAlt" : "writer file"},
            "odt"   :{"mapsTo" : "odt",   "imgURL" : os.path.join(imagesBaseURL, "writer.png"),     "imgAlt" : "writer file"},
            "sxc"   :{"mapsTo" : "ods",   "imgURL" : os.path.join(imagesBaseURL, "calc.png"),       "imgAlt" : "spreadsheet file"},
            "ods"   :{"mapsTo" : "ods",   "imgURL" : os.path.join(imagesBaseURL, "calc.png"),       "imgAlt" : "spreadsheet file"},
            "other" :{"mapsTo" : "other", "imgURL" : os.path.join(imagesBaseURL, "file_small.png"), "imgAlt" : "unknown type file"},
            "link"  :{"mapsTo" : "link",  "imgURL" : os.path.join(imagesBaseURL, "link.png"),       "imgAlt" : "link"}
        }

    def _getVariables(self, conf):
        wvars = {}
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        wvars['INCLUDE'] = '../include'

        wvars['accessWrapper'] = accessWrapper = self._rh._aw
        wvars['conf'] = conf
        if conf.getOwnerList():
            wvars['category'] = conf.getOwnerList()[0].getName()
        else:
            wvars['category'] = ''

        timezoneUtil = DisplayTZ(accessWrapper, conf)
        tz = timezoneUtil.getDisplayTZ()
        wvars['startDate'] = conf.getAdjustedStartDate(tz)
        wvars['endDate'] = conf.getAdjustedEndDate(tz)
        wvars['timezone'] = tz

        if conf.getParticipation().displayParticipantList() :
            wvars['participants']  = conf.getParticipation().getPresentParticipantListText()

        attached_items = conf.attached_items

        lectures, folders = [], []

        for folder in attached_items.get('folders', []):
            if LECTURE_SERIES_RE.match(folder.title):
                lectures.append(folder)
            elif folder.title != "Internal Page Files":
                folders.append(folder)

        cmp_title_number = lambda x, y: int(x.title[4:]) - int(y.title[4:])

        wvars.update({
            'files': attached_items.get('files', []),
            'folders': folders,
            'lectures': sorted(lectures, cmp=cmp_title_number)
        })

        if (conf.getType() in ("meeting", "simple_event")
                and conf.getParticipation().isAllowedForApplying()
                and conf.getStartDate() > nowutc()
                and not conf.getParticipation().isFull()):
            wvars['registrationOpen'] = True
        wvars['supportEmailCaption'] = conf.getSupportInfo().getCaption()

        wvars['types'] = self._types

        wvars['entries'] = []
        confSchedule = conf.getSchedule()
        showSession = self._params.get("showSession","all")
        detailLevel = self._params.get("detailLevel", "contribution")
        showDate = self._params.get("showDate", "all")
        # Filter by day
        if showDate == "all":
            entrylist = confSchedule.getEntries()
        else:
            entrylist = confSchedule.getEntriesOnDay(timezone(tz).localize(stringToDate(showDate)))
        # Check entries filters and access rights
        for entry in entrylist:
            sessionCand = entry.getOwner().getOwner()
            # Filter by session
            if isinstance(sessionCand, Session) and (showSession != "all" and sessionCand.getId() != showSession):
                continue
            # Hide/Show contributions
            if isinstance(entry.getOwner(), Contribution) and detailLevel != "contribution":
                continue
            if entry.getOwner().canView(accessWrapper):
                if type(entry) is schedule.BreakTimeSchEntry:
                    newItem = entry
                else:
                    newItem = entry.getOwner()
                wvars['entries'].append(newItem)

        wvars['entries'].sort(key=lambda entry: entry.getEndDate(), reverse=True)
        wvars['entries'].sort(key=lambda entry: (entry.getStartDate(),
                                                 entry.getFullTitle() if hasattr(entry, 'getFullTitle') else None))
        wvars["daysPerRow"] = self._daysPerRow
        wvars["firstDay"] = self._firstDay
        wvars["lastDay"] = self._lastDay
        wvars["currentUser"] = self._rh._aw.getUser()
        wvars["reportNumberSystems"] = Config.getInstance().getReportNumberSystems()
        return wvars

    def _getItemType(self, item):
        itemClass = item.__class__.__name__
        if itemClass == 'BreakTimeSchEntry':
            return 'Break'
        elif itemClass == 'SessionSlot':
            return 'Session'
        elif itemClass == 'AcceptedContribution':
            return 'Contribution'
        else:
            # return Conference, Contribution or SubContribution
            return itemClass

    def _extractInfoForButton(self, item):
        info = {}
        for key in ['sessId', 'slotId', 'contId', 'subContId']:
            info[key] = 'null'
        info['confId'] = self._conf.getId()

        itemType = self._getItemType(item)
        info['uploadURL'] = 'Indico.Urls.UploadAction.%s' % itemType.lower()

        if itemType == 'Conference':
            info['parentProtection'] = item.getAccessController().isProtected()
            if item.canModify(self._rh._aw):
                info["modifyLink"] = urlHandlers.UHConferenceModification.getURL(item)
                info["minutesLink"] = True
                info["materialLink"] = True
                info["cloneLink"] = urlHandlers.UHConfClone.getURL(item)
            elif item.as_event.can_manage(session.user, 'submit'):
                info["minutesLink"] = True
                info["materialLink"] = True

        elif itemType == 'Session':
            sess = item.getSession()
            info['parentProtection'] = sess.getAccessController().isProtected()
            if sess.canModify(self._rh._aw) or sess.canCoordinate(self._rh._aw):
                info["modifyLink"] = urlHandlers.UHSessionModification.getURL(item)
            info['slotId'] = item.getId()
            info['sessId'] = sess.getId()
            if sess.canModify(self._rh._aw) or sess.canCoordinate(self._rh._aw):
                info["minutesLink"] = True
                info["materialLink"] = True
                url = urlHandlers.UHSessionModifSchedule.getURL(sess)
                ttLink = "%s#%s.s%sl%s" % (url, sess.getStartDate().strftime('%Y%m%d'), sess.getId(), info['slotId'])
                info["sessionTimetableLink"] = ttLink

        elif itemType == 'Contribution':
            info['parentProtection'] = item.getAccessController().isProtected()
            if item.canModify(self._rh._aw):
                info["modifyLink"] = urlHandlers.UHContributionModification.getURL(item)
            if item.canModify(self._rh._aw) or item.canUserSubmit(self._rh._aw.getUser()):
                info["minutesLink"] = True
                info["materialLink"] = True
            info["contId"] = item.getId()
            owner = item.getOwner()
            if self._getItemType(owner) == 'Session':
                info['sessId'] = owner.getId()

        elif itemType == 'SubContribution':
            info['parentProtection'] = item.getContribution().getAccessController().isProtected()
            if item.canModify(self._rh._aw):
                info["modifyLink"] = urlHandlers.UHSubContributionModification.getURL(item)
            if item.canModify(self._rh._aw) or item.canUserSubmit(self._rh._aw.getUser()):
                info["minutesLink"] = True
                info["materialLink"] = True
            info["subContId"] = item.getId()
            info["contId"] = item.getContribution().getId()
            owner = item.getOwner()
            if self._getItemType(owner) == 'Session':
                info['sessId'] = owner.getId()

        return info

    def _getHTMLHeader( self ):
        return WPConferenceBase._getHTMLHeader(self)

    def _getHeadContent( self ):
        config = Config.getInstance()
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        htdocs = config.getHtdocsDir()
        baseurl = self._getBaseURL()
        # First include the default Indico stylesheet
        try:
            timestamp = os.stat(__file__).st_mtime
        except OSError:
            timestamp = 0
        styleText = """<link rel="stylesheet" href="%s/css/%s?%d">\n""" % \
            (baseurl, Config.getInstance().getCssStylesheetName(), timestamp)
        # Then the common event display stylesheet
        if os.path.exists("%s/css/events/common.css" % htdocs):
            styleText += """        <link rel="stylesheet" href="%s/css/events/common.css?%d">\n""" % (baseurl,
                                                                                                       timestamp)

        # And finally the specific display stylesheet
        if styleMgr.existsCSSFile(self._view):
            cssPath = os.path.join(baseurl, 'css', 'events', styleMgr.getCSSFilename(self._view))
            styleText += """<link rel="stylesheet" href="%s?%d">\n""" % (cssPath, timestamp)

        theme_url = get_css_url(self._conf.as_event)
        if theme_url:
            link = '<link rel="stylesheet" type="text/css" href="{url}">'.format(url=theme_url)
            styleText += link

        confMetadata = WConfMetadata(self._conf).getHTML()

        mathJax = render('js/mathjax.config.js.tpl') + \
                  '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url) for url in
                             self._asset_env['mathjax_js'].urls()])

        return styleText + confMetadata + mathJax

    def _getFooter( self ):
        """
        """
        wc = wcomponents.WEventFooter(self._conf)
        p = {"modificationDate":format_datetime(self._conf.getModificationDate(), format='d MMMM yyyy H:mm'),"subArea": self._getSiteArea(),"dark":True}
        if Config.getInstance().getShortEventURL():
            id=self._conf.getUrlTag().strip()
            if not id:
                id = self._conf.getId()
            p["shortURL"] =  Config.getInstance().getShortEventURL() + id
        return wc.getHTML(p)

    def _getHeader( self ):
        """
        """
        if self._type == "simple_event":
            wc = wcomponents.WMenuSimpleEventHeader( self._getAW(), self._conf )
        elif self._type == "meeting":
            wc = wcomponents.WMenuMeetingHeader( self._getAW(), self._conf )
        else:
            wc = wcomponents.WMenuConferenceHeader( self._getAW(), self._conf )
        return wc.getHTML( { "loginURL": self.getLoginURL(),\
                             "logoutURL": self.getLogoutURL(),\
                             "confId": self._conf.getId(),\
                             "currentView": self._view,\
                             "type": self._type,\
                             "selectedDate": self._params.get("showDate",""),\
                             "selectedSession": self._params.get("showSession",""),\
                             "detailLevel": self._params.get("detailLevel",""),\
                             "filterActive": self._params.get("filterActive",""),\
                            "dark": True } )

    def getCSSFiles(self):
        return (WPConferenceBase.getCSSFiles(self) +
                self._asset_env['eventservices_sass'].urls() +
                self._asset_env['event_display_sass'].urls())

    def getJSFiles(self):
        modules = WPConferenceBase.getJSFiles(self)

        # TODO: find way to check if the user is able to manage
        # anything inside the conference (sessions, ...)
        modules += (self._includeJSPackage('Management') +
                    self._includeJSPackage('MaterialEditor') +
                    self._includeJSPackage('Display') +
                    self._asset_env['modules_vc_js'].urls() +
                    self._asset_env['modules_event_display_js'].urls() +
                    self._asset_env['zero_clipboard_js'].urls())
        return modules

    def _applyDecoration( self, body ):
        """
        """
        if self._params.get("frame","")=="no" or self._params.get("fr","")=="no":
                return to_unicode(WPrintPageFrame().getHTML({"content":body}))
        return WPConferenceBase._applyDecoration(self, body)

    def _getHTMLFooter( self ):
        if self._params.get("frame","")=="no" or self._params.get("fr","")=="no":
            return ""
        return WPConferenceBase._getHTMLFooter(self)

    @staticmethod
    def getLocationInfo(item, roomLink=True, fullName=False):
        """Return a tuple (location, room, url) containing
        information about the location of the item."""
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        location = item.getLocation().getName() if item.getLocation() else ""
        customRoom = item.getRoom()
        if not customRoom:
            roomName = ''
        elif fullName and location and Config.getInstance().getIsRoomBookingActive():
            # if we want the full name and we have a RB DB to search in
            roomName = customRoom.getFullName()
            if not roomName:
                customRoom.retrieveFullName(location) # try to fetch the full name
                roomName = customRoom.getFullName() or customRoom.getName()
        else:
            roomName = customRoom.getName()
        # TODO check if the following if is required
        if roomName in ['', '0--', 'Select:']:
            roomName = ''
        if roomLink:
            url = linking.RoomLinker().getURL(item.getRoom(), item.getLocation())
        else:
            url = ""
        return (location, roomName, url)

    def _getBody(self, params):
        """Return main information about the event."""

        if self._view != 'xml':
            vars = self._getVariables(self._conf)
            vars['getTime'] = lambda date : format_time(date.time(), format="HH:mm")
            vars['isTime0H0M'] = lambda date : (date.hour, date.minute) == (0,0)
            vars['getDate'] = lambda date : format_date(date, format='yyyy-MM-dd')
            vars['prettyDate'] = lambda date : format_date(date, format='full')
            vars['prettyDuration'] = MaKaC.common.utils.prettyDuration
            vars['parseDate'] = MaKaC.common.utils.parseDate
            vars['isStringHTML'] = MaKaC.common.utils.isStringHTML
            vars['extractInfoForButton'] = lambda item : self._extractInfoForButton(item)
            vars['getItemType'] = lambda item : self._getItemType(item)
            vars['getLocationInfo'] = WPTPLConferenceDisplay.getLocationInfo
            vars['dumps'] = json.dumps
            vars['timedelta'] = timedelta
        else:
            outGen = outputGenerator(self._rh._aw)
            varsForGenerator = self._getBodyVariables()
            vars = {}
            vars['xml'] = outGen._getBasicXML(self._conf, varsForGenerator, 1, 1, 1, 1)

        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        if styleMgr.existsTPLFile(self._view):
            fileName = os.path.splitext(styleMgr.getTemplateFilename(self._view))[0]
            body = wcomponents.WTemplated(os.path.join("events", fileName)).getHTML(vars)
        else:
            return _("Template could not be found.")
        return body


class WPrintPageFrame (wcomponents.WTemplated):
    pass


class WConfDisplayBodyBase(wcomponents.WTemplated):

    def _getTitle(self):
        entry = get_menu_entry_by_name(self._linkname, self._conf)
        return entry.localized_title


class WConfProgram(WConfDisplayBodyBase):

    _linkname = 'program'

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def buildTrackData(self, track):
        """
        Returns a dict representing the data of the track and its Sub-tracks
        should it have any.
        """
        description = track.getDescription()

        formattedTrack = {
            'title': track.getTitle(),
            'description': description
        }

        if track.getConference().getAbstractMgr().isActive() and \
           track.getConference().hasEnabledSection("cfa") and \
           track.canCoordinate(self._aw):

            if track.getConference().canModify(self._aw):
                formattedTrack['url'] = urlHandlers.UHTrackModification.getURL(track)
            else:
                formattedTrack['url'] = urlHandlers.UHTrackModifAbstracts.getURL(track)

        return formattedTrack

    def getVars(self):
        pvars = wcomponents.WTemplated.getVars(self)
        pvars["body_title"] = self._getTitle()
        pvars['description'] = self._conf.getProgramDescription()
        pvars['program'] = [self.buildTrackData(t) for t in self._conf.getTrackList()]
        pvars['pdf_url'] = urlHandlers.UHConferenceProgramPDF.getURL(self._conf)

        return pvars


class WPConferenceProgram(WPConferenceDefaultDisplayBase):
    menu_entry_name = 'program'

    def _getBody(self, params):
        wc = WConfProgram(self._getAW(), self._conf)
        return wc.getHTML()


class WConferenceTimeTable(WConfDisplayBodyBase):

    _linkname = 'timetable'

    def __init__(self, conference, aw):
        self._conf = conference
        self._aw = aw

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        tz = DisplayTZ(self._aw, self._conf).getDisplayTZ()
        sf = schedule.ScheduleToJson.process(self._conf.getSchedule(),
                                             tz, self._aw,
                                             useAttrCache=True,
                                             hideWeekends=True)
        # TODO: Move to beginning of file when proved useful
        try:
            import ujson
            jsonf = ujson.encode
        except ImportError:
            jsonf = json.dumps
        wvars["ttdata"] = jsonf(sf)
        eventInfo = fossilize(self._conf, IConferenceEventInfoFossil, tz=tz)
        eventInfo['isCFAEnabled'] = self._conf.getAbstractMgr().isActive()
        wvars['eventInfo'] = eventInfo
        wvars['timetableLayout'] = wvars.get('ttLyt', '')
        return wvars


class WPConferenceTimeTable(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEConferenceTimeTable
    menu_entry_name = 'timetable'

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
               self._includeJSPackage('Timetable')

    def _getHeadContent(self):
        content = WPConferenceDefaultDisplayBase._getHeadContent(self)
        return content + '<link rel="stylesheet" type="text/css" href="{}/css/timetable.css">'.format(
            self._getBaseURL())

    def _getBody( self, params ):
        wc = WConferenceTimeTable( self._conf, self._getAW()  )
        return wc.getHTML(params)


class WPMeetingTimeTable( WPTPLConferenceDisplay ):

    def getJSFiles(self):
        return WPXSLConferenceDisplay.getJSFiles(self) + \
               self._includeJSPackage('Timetable')

    def _getBody( self, params ):
        wc = WConferenceTimeTable( self._conf, self._getAW()  )
        return wc.getHTML(params)


class WPConferenceModifBase(main.WPMainBase):

    _userData = ['favorite-user-ids']

    def __init__(self, rh, conference, **kwargs):
        main.WPMainBase.__init__(self, rh, **kwargs)
        self._navigationTarget = self._conf = conference

    def getJSFiles(self):
        return main.WPMainBase.getJSFiles(self) + \
               self._includeJSPackage('Management') + \
               self._includeJSPackage('MaterialEditor')

    def _getSiteArea(self):
        return "ModificationArea"

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WHeader( self._getAW() )
        return wc.getHTML( { "subArea": self._getSiteArea(), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())),\
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())) } )

    def _getNavigationDrawer(self):
        pars = {"target": self._conf, "isModif": True }
        return wcomponents.WNavigationDrawer( pars, bgColor="white" )

    def _createSideMenu(self):
        pass

    def _applyFrame(self, body):
        frame = wcomponents.WConferenceModifFrame(self._conf, self._getAW())

        params = {
            "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL,
            "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL,
            "event": "Conference",
            "sideMenu": render_sidemenu('event-management-sidemenu', active_item=self.sidemenu_option, old_style=True,
                                        event=self._conf)
        }

        wf = self._rh.getWebFactory()
        if wf:
            params["event"] = wf.getName()
        return frame.getHTML(body, **params)

    def _getBody( self, params ):
        return self._applyFrame( self._getPageContent( params ) )

    def _getTabContent( self, params ):
        return "nothing"

    def _getPageContent( self, params ):
        return "nothing"


class WPConferenceModifAbstractBase( WPConferenceModifBase ):

    sidemenu_option = 'abstracts'

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabCFA = self._tabCtrl.newTab( "cfasetup", _("Setup"), urlHandlers.UHConfModifCFA.getURL( self._conf ) )
        self._tabCFAPreview = self._tabCtrl.newTab("cfapreview", _("Preview"), urlHandlers.UHConfModifCFAPreview.getURL(self._conf))
        self._tabAbstractList = self._tabCtrl.newTab( "abstractList", _("List of Abstracts"), urlHandlers.UHConfAbstractList.getURL( self._conf ) )
        self._tabBOA = self._tabCtrl.newTab("boa", _("Book of Abstracts Setup"), urlHandlers.UHConfModAbstractBook.getURL(self._conf))
        self._tabCFAR = self._tabCtrl.newTab("reviewing", _("Reviewing"), urlHandlers.UHAbstractReviewingSetup.getURL(self._conf))

        # Create subtabs for the reviewing
        self._subTabARSetup = self._tabCFAR.newSubTab( "revsetup", _("Settings"),\
                    urlHandlers.UHAbstractReviewingSetup.getURL(self._conf))
        self._subTabARTeam = self._tabCFAR.newSubTab( "revteam", _("Team"),\
                    urlHandlers.UHAbstractReviewingTeam.getURL(self._conf))
        self._subTabARNotifTpl = self._tabCFAR.newSubTab( "notiftpl", _("Notification templates"),\
                    urlHandlers.UHAbstractReviewingNotifTpl.getURL(self._conf))

        if not self._conf.hasEnabledSection("cfa"):
            self._tabBOA.disable()
            self._tabCFA.disable()
            self._tabAbstractList.disable()
            self._tabCFAPreview.disable()
            self._tabCFAR.disable()

        self._setActiveTab()

    def _getPageContent(self, params):
        self._createTabCtrl()

        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

    def _getTabContent(self, params):
        return "nothing"

    def _setActiveTab(self):
        pass


class WConfModifMainData(wcomponents.WTemplated):

    def __init__(self, conference, ct, rh):
        self._conf = conference
        self._ct = ct
        self._rh = rh

    def _getChairPersonsList(self):
        result = fossilize(self._conf.getChairList())
        for chair in result:
            user = get_user_by_email(chair['email'])
            chair['showManagerCB'] = True
            chair['showSubmitterCB'] = True
            email_submitters = {x.email for x in self._conf.as_event.acl_entries
                                if x.type == PrincipalType.email and x.has_management_role('submit', explicit=True)}
            if chair['email'] in email_submitters or (user and self._conf.as_event.can_manage(user, 'submit',
                                                                                              explicit_role=True)):
                chair['showSubmitterCB'] = False
            email_managers = {x.email for x in self._conf.as_event.acl_entries if x.type == PrincipalType.email}
            if chair['email'] in email_managers or (user and self._conf.as_event.can_manage(user, explicit_role=True)):
                chair['showManagerCB'] = False
        return result

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        type = vars["type"]
        vars["defaultStyle"] = self._conf.getDefaultStyle()
        vars["visibility"] = self._conf.getVisibility()
        vars["dataModificationURL"]=quoteattr(str(urlHandlers.UHConfDataModif.getURL(self._conf)))
        vars["addTypeURL"]=urlHandlers.UHConfAddContribType.getURL(self._conf)
        vars["removeTypeURL"]=urlHandlers.UHConfRemoveContribType.getURL(self._conf)
        vars["title"]=self._conf.getTitle()
        if isStringHTML(self._conf.getDescription()):
            vars["description"] = self._conf.getDescription()
        elif self._conf.getDescription():
            vars["description"] = self._conf.getDescription()
        else:
            vars["description"] = ""

        ###################################
        # Fermi timezone awareness        #
        ###################################
        tz = self._conf.getTimezone()
        vars["timezone"] = tz
        vars["startDate"]=formatDateTime(self._conf.getAdjustedStartDate())
        vars["endDate"]=formatDateTime(self._conf.getAdjustedEndDate())
        ###################################
        # Fermi timezone awareness(end)   #
        ###################################
        vars["chairText"] = self.htmlText(self._conf.getChairmanText())
        place=self._conf.getLocation()

        vars["locationName"]=vars["locationAddress"]=""
        if place:
            vars["locationName"]=self.htmlText(place.getName())
            vars["locationAddress"]=self.htmlText(place.getAddress())
        room=self._conf.getRoom()
        vars["locationRoom"]=""
        if room:
            vars["locationRoom"]=self.htmlText(room.getName())
        if isStringHTML(self._conf.getContactInfo()):
            vars["contactInfo"]=self._conf.getContactInfo()
        else:
            vars["contactInfo"] = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._conf.getContactInfo()
        vars["supportEmailCaption"] = self._conf.getSupportInfo().getCaption()
        vars["supportEmail"] = i18nformat("""--_("not set")--""")
        if self._conf.getSupportInfo().hasEmail():
            vars["supportEmail"] = self.htmlText(self._conf.getSupportInfo().getEmail())
        typeList = []
        for type in self._conf.getContribTypeList():
            typeList.append("""<input type="checkbox" name="types" value="%s"><a href="%s">%s</a><br>
<table><tr><td width="30"></td><td><font><pre>%s</pre></font></td></tr></table>"""%( \
                type.getId(), \
                str(urlHandlers.UHConfEditContribType.getURL(type)), \
                type.getName(), \
                type.getDescription()))
        vars["typeList"] = "".join(typeList)
        #------------------------------------------------------
        vars["reportNumbersTable"]=wcomponents.WReportNumbersTable(self._conf).getHTML()
        vars["eventType"] = self._conf.getType()
        vars["keywords"] = self._conf.getKeywords()
        vars["shortURLBase"] = Config.getInstance().getShortEventURL()
        vars["shortURLTag"] = self._conf.getUrlTag()
        vars["screenDatesURL"] = urlHandlers.UHConfScreenDatesEdit.getURL(self._conf)
        ssdate = format_datetime(self._conf.getAdjustedScreenStartDate(), format='EEEE d MMMM yyyy H:mm')
        if self._conf.getScreenStartDate() == self._conf.getStartDate():
            ssdate += i18nformat(""" <i> _("(normal)")</i>""")
        else:
            ssdate += i18nformat(""" <font color='red'>_("(modified)")</font>""")
        sedate = format_datetime(self._conf.getAdjustedScreenEndDate(), format='EEEE d MMMM yyyy H:mm')
        if self._conf.getScreenEndDate() == self._conf.getEndDate():
            sedate += i18nformat(""" <i> _("(normal)")</i>""")
        else:
            sedate += i18nformat(""" <font color='red'> _("(modified)")</font>""")
        vars['rbActive'] = Config.getInstance().getIsRoomBookingActive()
        vars["screenDates"] = "%s -> %s" % (ssdate, sedate)
        vars["timezoneList"] = TimezoneRegistry.getList()
        vars["chairpersons"] = self._getChairPersonsList()

        loc = self._conf.getLocation()
        room = self._conf.getRoom()
        vars["currentLocation"] = { 'location': loc.getName() if loc else "",
                                    'room': room.name if room else "",
                                    'address': loc.getAddress() if loc else "" }
        return vars

class WPConferenceModificationClosed( WPConferenceModifBase ):

    def __init__(self, rh, target):
        WPConferenceModifBase.__init__(self, rh, target)

    def _getPageContent( self, params ):
        message = _("The event is currently locked and you cannot modify it in this status. ")
        if self._conf.canModify(self._rh.getAW()):
            message += _("If you unlock the event, you will be able to modify its details again.")
        return wcomponents.WClosed().getHTML({"message": message,
                                             "postURL": urlHandlers.UHConferenceOpen.getURL(self._conf),
                                             "showUnlockButton": self._conf.canModify(self._rh.getAW()),
                                             "unlockButtonCaption": _("Unlock event")})


class WPConferenceModification( WPConferenceModifBase ):

    sidemenu_option = 'general'

    def __init__(self, rh, target, ct=None):
        WPConferenceModifBase.__init__(self, rh, target)
        self._ct = ct

    def _getPageContent( self, params ):
        wc = WConfModifMainData(self._conf, self._ct, self._rh)
        pars = { "type": params.get("type","") , "conferenceId": self._conf.getId()}
        return wc.getHTML( pars )

class WConfModScreenDatesEdit(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfScreenDatesEdit.getURL(self._conf)))
        ###################################
        # Fermi timezone awareness        #
        ###################################
        csd = self._conf.getAdjustedStartDate()
        ced = self._conf.getAdjustedEndDate()
        ###################################
        # Fermi timezone awareness(end)   #
        ###################################
        vars["conf_start_date"]=self.htmlText(format_datetime(csd, format='EEEE d MMMM yyyy H:mm'))
        vars["conf_end_date"]=self.htmlText(format_datetime(ced, format='EEEE d MMMM yyyy H:mm'))
        vars["start_date_own_sel"]=""
        vars["start_date_conf_sel"]=" checked"
        vars["sDay"],vars["sMonth"],vars["sYear"]=csd.day,csd.month,csd.year
        vars["sHour"],vars["sMin"]=csd.hour,csd.minute
        if self._conf.getScreenStartDate() != self._conf.getStartDate():
            vars["start_date_own_sel"]=" checked"
            vars["start_date_conf_sel"]=""
            sd=self._conf.getAdjustedScreenStartDate()
            vars["sDay"]=quoteattr(str(sd.day))
            vars["sMonth"]=quoteattr(str(sd.month))
            vars["sYear"]=quoteattr(str(sd.year))
            vars["sHour"]=quoteattr(str(sd.hour))
            vars["sMin"]=quoteattr(str(sd.minute))
        vars["end_date_own_sel"]=""
        vars["end_date_conf_sel"]=" checked"
        vars["eDay"],vars["eMonth"],vars["eYear"]=ced.day,ced.month,ced.year
        vars["eHour"],vars["eMin"]=ced.hour,ced.minute
        if self._conf.getScreenEndDate() != self._conf.getEndDate():
            vars["end_date_own_sel"]=" checked"
            vars["end_date_conf_sel"]=""
            ed=self._conf.getAdjustedScreenEndDate()
            vars["eDay"]=quoteattr(str(ed.day))
            vars["eMonth"]=quoteattr(str(ed.month))
            vars["eYear"]=quoteattr(str(ed.year))
            vars["eHour"]=quoteattr(str(ed.hour))
            vars["eMin"]=quoteattr(str(ed.minute))
        return vars

class WPScreenDatesEdit(WPConferenceModification):

    def _getPageContent( self, params ):
        wc = WConfModScreenDatesEdit(self._conf)
        return wc.getHTML()

class WConferenceDataModificationAdditionalInfo(wcomponents.WTemplated):

    def __init__( self, conference ):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["contactInfo"] = self._conf.getContactInfo()
        return vars


class WConferenceDataModification(wcomponents.WTemplated):

    def __init__( self, conference, rh ):
        self._conf = conference
        self._rh = rh

    def _getVisibilityHTML(self):
        visibility = self._conf.getVisibility()
        topcat = self._conf.getOwnerList()[0]
        level = 0
        selected = ""
        if visibility == 0:
            selected = "selected"
        vis = [ i18nformat("""<option value="0" %s> _("Nowhere")</option>""") % selected]
        while topcat:
            level += 1
            selected = ""
            if level == visibility:
                selected = "selected"
            if topcat.getId() != "0":
                from MaKaC.common.TemplateExec import truncateTitle
                vis.append("""<option value="%s" %s>%s</option>""" % (level, selected, truncateTitle(topcat.getName(), 120)))
            topcat = topcat.getOwner()
        selected = ""
        if visibility > level:
            selected = "selected"
        vis.append( i18nformat("""<option value="999" %s> _("Everywhere")</option>""") % selected)
        vis.reverse()
        return "".join(vis)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()

        navigator = ""
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        type = self._conf.getType()
        vars["timezoneOptions"] = TimezoneRegistry.getShortSelectItemsHTML(self._conf.getTimezone())
        styles=styleMgr.getExistingStylesForEventType(type)
        styleoptions = ""
        defStyle = self._conf.getDefaultStyle()
        if defStyle not in styles:
            defStyle = ""
        for styleId in styles:
            if styleId == defStyle or (defStyle == "" and styleId == "static"):
                selected = "selected"
            else:
                selected = ""
            styleoptions += "<option value=\"%s\" %s>%s</option>" % (styleId,selected,styleMgr.getStyleName(styleId))
        vars["conference"] = self._conf
        vars["useRoomBookingModule"] = Config.getInstance().getIsRoomBookingActive()
        vars["styleOptions"] = styleoptions
        import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
        wr = webFactoryRegistry.WebFactoryRegistry()
        types = [ "conference" ]
        for fact in wr.getFactoryList():
            types.append(fact.getId())
        vars["types"] = ""
        for id in types:
            typetext = id
            if typetext == "simple_event":
                typetext = "lecture"
            if self._conf.getType() == id:
                vars["types"] += "<option value=\"%s\" selected>%s" % (id,typetext)
            else:
                vars["types"] += "<option value=\"%s\">%s" % (id,typetext)
        vars["title"] = quoteattr( self._conf.getTitle() )
        vars["description"] = self._conf.getDescription()
        vars["keywords"] = self._conf.getKeywords()
        tz = self._conf.getTimezone()
        vars["sDay"] = str( self._conf.getAdjustedStartDate(tz).day )
        vars["sMonth"] = str( self._conf.getAdjustedStartDate(tz).month )
        vars["sYear"] = str( self._conf.getAdjustedStartDate(tz).year )
        vars["sHour"] = str( self._conf.getAdjustedStartDate(tz).hour )
        vars["sMinute"] = str( self._conf.getAdjustedStartDate(tz).minute )
        vars["eDay"] = str( self._conf.getAdjustedEndDate(tz).day )
        vars["eMonth"] = str( self._conf.getAdjustedEndDate(tz).month )
        vars["eYear"] = str( self._conf.getAdjustedEndDate(tz).year )
        vars["eHour"] = str( self._conf.getAdjustedEndDate(tz).hour )
        vars["eMinute"] = str( self._conf.getAdjustedEndDate(tz).minute )
        vars["chairText"] = quoteattr( self._conf.getChairmanText() )
        vars["orgText"] = quoteattr( self._conf.getOrgText() )
        vars["visibility"] = self._getVisibilityHTML()
        vars["shortURLTag"] = quoteattr( self._conf.getUrlTag() )
        locName, locAddress, locRoom = "", "", ""
        location = self._conf.getLocation()
        if location:
            locName = location.getName()
            locAddress = location.getAddress()
        room = self._conf.getRoom()
        if room:
            locRoom = room.getName()
        vars["locator"] = self._conf.getLocator().getWebForm()

        vars["locationAddress"] = locAddress

        vars["supportCaption"] = quoteattr(self._conf.getSupportInfo().getCaption())
        vars["supportEmail"] = quoteattr( self._conf.getSupportInfo().getEmail() )
        vars["locator"] = self._conf.getLocator().getWebForm()
        vars["event_type"] = ""
        vars["navigator"] = navigator
        eventType = self._conf.getType()
        if eventType == "conference":
            vars["additionalInfo"] = WConferenceDataModificationAdditionalInfo(self._conf).getHTML(vars)
        else:
            vars["additionalInfo"] = ""
        return vars


class WPConfDataModif( WPConferenceModification ):

    def _getPageContent( self, params ):
        p = WConferenceDataModification( self._conf, self._rh )
        pars = {
            "postURL": urlHandlers.UHConfPerformDataModif.getURL(self._conf),
            "type": params.get("type")
        }
        return p.getHTML( pars )


class WConfModifScheduleGraphic(wcomponents.WTemplated):

    def __init__(self, conference, customLinks, **params):
        wcomponents.WTemplated.__init__(self, **params)
        self._conf = conference
        self._customLinks = customLinks

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars(self)
        ################################
        # Fermi timezone awareness     #
        ################################
        tz = self._conf.getTimezone()
        vars["timezone"]= tz
        vars["start_date"]=self._conf.getAdjustedStartDate().strftime("%a %d/%m")
        vars["end_date"]=self._conf.getAdjustedEndDate().strftime("%a %d/%m")
        #################################
        # Fermi timezone awareness(end) #
        #################################
        vars["editURL"]=quoteattr(str(urlHandlers.UHConfModScheduleDataEdit.getURL(self._conf)))

        vars['ttdata'] = schedule.ScheduleToJson.process(self._conf.getSchedule(), tz, None,
                                                         days = None, mgmtMode = True)

        vars['customLinks'] = self._customLinks

        eventInfo = fossilize(self._conf, IConferenceEventInfoFossil, tz = tz)
        eventInfo['isCFAEnabled'] = self._conf.getAbstractMgr().isActive()
        vars['eventInfo'] = eventInfo

        return vars


class WPConfModifScheduleGraphic( WPConferenceModifBase ):

    sidemenu_option = 'timetable'
    _userData = ['favorite-user-list', 'favorite-user-ids']

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._contrib = None

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + self._includeJSPackage('Timetable')

    def _getSchedule(self):
        custom_links = dict(values_from_signal(signals.event.timetable_buttons.send(self)))
        return WConfModifScheduleGraphic(self._conf, custom_links)

    def _getTTPage( self, params ):
        wc = self._getSchedule()
        return wc.getHTML(params)

    def _getPageContent(self, params):
        return self._getTTPage(params)

#------------------------------------------------------------------------------
class WPConfModifSchedule( WPConferenceModifBase ):

    def _setActiveTab( self ):
        self._tabSchedule.setActive()

#------------------------------------------------------------------------------
class WConfModScheduleDataEdit(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfModScheduleDataEdit.getURL(self._conf)))
        #######################################
        # Fermi timezone awareness            #
        #######################################
        csd = self._conf.getAdjustedStartDate()
        ced = self._conf.getAdjustedEndDate()
        #######################################
        # Fermi timezone awareness(end)       #
        #######################################
        vars["sDay"],vars["sMonth"],vars["sYear"]=str(csd.day),str(csd.month),str(csd.year)
        vars["sHour"],vars["sMin"]=str(csd.hour),str(csd.minute)
        vars["eDay"],vars["eMonth"],vars["eYear"]=str(ced.day),str(ced.month),str(ced.year)
        vars["eHour"],vars["eMin"]=str(ced.hour),str(ced.minute)
        return vars

class WPModScheduleDataEdit(WPConfModifSchedule):

    def _getPageContent( self, params ):
        wc = WConfModScheduleDataEdit(self._conf)
        return wc.getHTML()


class WConfModifACSessionCoordinatorRights(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf = conf

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        url = urlHandlers.UHConfModifCoordinatorRights.getURL(self._conf)
        html=[]
        scr = conference.SessionCoordinatorRights()
        for rightKey in scr.getRightKeys():
            url = urlHandlers.UHConfModifCoordinatorRights.getURL(self._conf)
            url.addParam("rightId", rightKey)
            if self._conf.hasSessionCoordinatorRight(rightKey):
                imgurl=Config.getInstance().getSystemIconURL("tick")
            else:
                imgurl=Config.getInstance().getSystemIconURL("cross")
            html.append("""
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href=%s><img class="imglink" src=%s></a> %s
                        """%(quoteattr(str(url)), quoteattr(str(imgurl)), scr.getRight(rightKey)))
        vars["optionalRights"]="<br>".join(html)
        return vars


class WConfModifAC:

    def __init__(self, conference, eventType, user):
        self.__conf = conference
        self._eventType = eventType
        self.__user = user

    def getHTML( self, params ):
        ac = wcomponents.WConfAccessControlFrame().getHTML( self.__conf,\
                                            params["setVisibilityURL"])
        dc = ""
        if not self.__conf.isProtected():
            dc = "<br>%s"%wcomponents.WDomainControlFrame( self.__conf ).getHTML()

        mc = wcomponents.WConfModificationControlFrame().getHTML( self.__conf) + "<br>"

        if self._eventType == "conference":
            rc = wcomponents.WConfRegistrarsControlFrame().getHTML(self.__conf) + "<br>"
        else:
            rc = ""

        tf = ""
        if self._eventType in ["conference", "meeting"]:
            tf = "<br>%s" % wcomponents.WConfProtectionToolsFrame(self.__conf).getHTML()
        cr = ""
        if self._eventType == "conference":
            cr = "<br>%s" % WConfModifACSessionCoordinatorRights(self.__conf).getHTML()

        return """<br><table width="100%%" class="ACtab"><tr><td>%s%s%s%s%s%s<br></td></tr></table>""" % (mc, rc, ac, dc, tf, cr)


class WPConfModifAC(WPConferenceModifBase):

    sidemenu_option = 'protection'

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._eventType = "conference"
        if self._rh.getWebFactory() is not None:
            self._eventType = self._rh.getWebFactory().getId()
        self._user = self._rh._getUser()

    def _getPageContent(self, params):
        wc = WConfModifAC(self._conf, self._eventType, self._user)
        p = {
            'setVisibilityURL': urlHandlers.UHConfSetVisibility.getURL(self._conf)
        }
        return wc.getHTML(p)

class WPConfModifToolsBase(WPConferenceModifBase):

    sidemenu_option = 'utilities'

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabReminders = self._tabCtrl.newTab('reminders', _("Reminders"),
                                                  url_for('event_reminders.list', self._conf))
        self._tabCloneEvent = self._tabCtrl.newTab("clone", _("Clone Event"), \
                urlHandlers.UHConfClone.getURL(self._conf))
        self._tabPosters = self._tabCtrl.newTab("posters", _("Posters"), \
                urlHandlers.UHConfModifPosterPrinting.getURL(self._conf))
        self._tabBadges = self._tabCtrl.newTab("badges", _("Badges/Tablesigns"), \
                urlHandlers.UHConfModifBadgePrinting.getURL(self._conf))
        self._tabClose = self._tabCtrl.newTab("close", _("Lock"), \
                urlHandlers.UHConferenceClose.getURL(self._conf))
        self._tabDelete = self._tabCtrl.newTab("delete", _("Delete"), \
                urlHandlers.UHConfDeletion.getURL(self._conf))

        if Config.getInstance().getOfflineStore():
            self._tabOffline = self._tabCtrl.newTab("offline", _("Offline copy"),
                                                    url_for('static_site.list', self._conf))

        self._setActiveTab()

        wf = self._rh.getWebFactory()
        if wf:
            wf.customiseToolsTabCtrl(self._tabCtrl)

    def _getPageContent(self, params):
        self._createTabCtrl()

        html = wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))
        return html

    def _setActiveTab(self):
        pass

    def _getTabContent(self, params):
        return "nothing"


class WPConfClosing(WPConfModifToolsBase):

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._eventType = "conference"
        if self._rh.getWebFactory() is not None:
            self._eventType = self._rh.getWebFactory().getId()

    def _setActiveTab(self):
        self._tabClose.setActive()

    def _getTabContent(self, params):
        msg = {'challenge': _("Are you sure that you want to lock the event?"),
               'target': self._conf.getTitle(),
               'subtext': _("Note that if you lock the event, you will not be able to change its details any more. "
                "Only the creator of the event or an administrator of the system / category can unlock an event."),
               }

        wc = wcomponents.WConfirmation()
        return wc.getHTML(msg,
                          urlHandlers.UHConferenceClose.getURL(self._conf),
                          {},
                          severity="warning",
                          confirmButtonCaption=_("Yes, lock this event"),
                          cancelButtonCaption=_("No"))


class WPConfDeletion(WPConfModifToolsBase):

    def _setActiveTab(self):
        self._tabDelete.setActive()

    def _getTabContent(self, params):
        msg = {'challenge': _("Are you sure that you want to delete the conference?"),
               'target': self._conf.getTitle(),
               'subtext': _("Note that if you delete the conference, all the items below it will also be deleted")
               }

        wc = wcomponents.WConfirmation()
        return wc.getHTML(msg,
                          urlHandlers.UHConfDeletion.getURL(self._conf),
                          {},
                          severity="danger",
                          confirmButtonCaption=_("Yes, I am sure"),
                          cancelButtonCaption=_("No"))


class WPConfCloneConfirm(WPConfModifToolsBase):

    def __init__(self, rh, conf, nbClones):
        WPConfModifToolsBase.__init__(self, rh, conf)
        self._nbClones = nbClones

    def _setActiveTab(self):
        self._tabCloneEvent.setActive()

    def _getTabContent(self, params):

        msg = _("This action will create {0} new events. Are you sure you want to proceed").format(self._nbClones)

        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHConfPerformCloning.getURL(self._conf)
        params = self._rh._getRequestParams()
        for key in params.keys():
            url.addParam(key, params[key])
        return wc.getHTML( msg, \
                        url, {}, True, \
                        confirmButtonCaption=_("Yes"), cancelButtonCaption=_("No"))

#---------------------------------------------------------------------------


class WPConferenceModifParticipantBase(WPConferenceModifBase):

    sidemenu_option = 'participants'

    def __init__(self, rh, conf):
        WPConferenceModifBase.__init__(self, rh, conf)

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabParticipantsSetup = self._tabCtrl.newTab("participantsetup", _("Setup"), urlHandlers.UHConfModifParticipantsSetup.getURL(self._conf))
        self._tabParticipantsList = self._tabCtrl.newTab("participantsList", _("Participants"), urlHandlers.UHConfModifParticipants.getURL(self._conf))
        self._tabStatistics = self._tabCtrl.newTab("statistics", _("Statistics"), urlHandlers.UHConfModifParticipantsStatistics.getURL(self._conf))
        if self._conf.getParticipation().getPendingParticipantList() and nowutc() < self._conf.getStartDate():
            self._tabParticipantsPendingList = self._tabCtrl.newTab("pendingList", _("Pending"), urlHandlers.UHConfModifParticipantsPending.getURL(self._conf), className="pendingTab")
        if self._conf.getParticipation().getDeclinedParticipantList():
            self._tabParticipantsDeclinedList = self._tabCtrl.newTab("declinedList", _("Declined"), urlHandlers.UHConfModifParticipantsDeclined.getURL(self._conf))

        self._setActiveTab()

    def _getPageContent(self, params):
        self._createTabCtrl()

        return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + \
               self._includeJSPackage('Display')

    def _getTabContent(self, params):
        return "nothing"

    def _setActiveTab(self):
        pass


class WConferenceParticipant(wcomponents.WTemplated):

    def __init__(self, conference, participant):
        self._conf = conference
        self._participant = participant

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["conference"] = self._conf
        vars["participant"] = self._participant
        return vars


class WConferenceParticipantPending(wcomponents.WTemplated):

    def __init__(self, conference, id, pending):
        self._conf = conference
        self._id = id
        self._pending = pending

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["conference"] = self._conf
        vars["id"] = self._id
        vars["pending"] = self._pending
        return vars


class WConferenceParticipantsSetup(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["confId"] = self._conf.getId()
        vars["isObligatory"] = self._conf.getParticipation().isObligatory()
        vars["allowDisplay"] = self._conf.getParticipation().displayParticipantList()
        vars["addedInfo"] = self._conf.getParticipation().isAddedInfo()
        vars["allowForApply"] = self._conf.getParticipation().isAllowedForApplying()
        vars["autoAccept"] = self._conf.getParticipation().isAutoAccept()
        vars["numMaxParticipants"] = self._conf.getParticipation().getNumMaxParticipants()
        vars["notifyMgrNewParticipant"] = self._conf.getParticipation().isNotifyMgrNewParticipant()
        return vars


class WPConfModifParticipantsSetup(WPConferenceModifParticipantBase):

    def _setActiveTab(self):
        self._tabParticipantsSetup.setActive()

    def _getTabContent(self, params):
        p = WConferenceParticipantsSetup(self._conf)
        return p.getHTML(params)


class WConferenceParticipants(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["selectAll"] = Config.getInstance().getSystemIconURL("checkAll")
        vars["deselectAll"] = Config.getInstance().getSystemIconURL("uncheckAll")

        vars["participantsAction"] = str(urlHandlers.UHConfModifParticipantsAction.getURL(self._conf))
        vars["hasStarted"] = nowutc() < self._conf.getStartDate()
        vars["currentUser"] = self._rh._aw.getUser()
        vars["numberParticipants"] = len(self._conf.getParticipation().getParticipantList())
        vars["conf"] = self._conf
        vars["excelIconURL"] = quoteattr(str(Config.getInstance().getSystemIconURL("excel")))

        return vars


class WPConfModifParticipants(WPConferenceModifParticipantBase):

    def _setActiveTab(self):
        self._tabParticipantsList.setActive()

    def _getTabContent(self, params):
        p = WConferenceParticipants(self._conf)
        return p.getHTML(params)


class WConferenceParticipantsPending(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["selectAll"] = Config.getInstance().getSystemIconURL("checkAll")
        vars["deselectAll"] = Config.getInstance().getSystemIconURL("uncheckAll")
        vars["pending"] = self._getPendingParticipantsList()
        vars["numberPending"] = self._conf.getParticipation().getPendingNumber()
        vars["conf"] = self._conf
        vars["conferenceStarted"] = nowutc() > self._conf.getStartDate()
        vars["currentUser"] = self._rh._aw.getUser()

        return vars

    def _getPendingParticipantsList(self):
        l = []

        for k in self._conf.getParticipation().getPendingParticipantList().keys():
            p = self._conf.getParticipation().getPendingParticipantByKey(k)
            l.append((k, p))
        return l


class WPConfModifParticipantsPending(WPConferenceModifParticipantBase):

    def _setActiveTab(self):
        self._tabParticipantsPendingList.setActive()

    def _getTabContent(self, params):
        p = WConferenceParticipantsPending(self._conf)
        return p.getHTML()


class WConferenceParticipantsDeclined(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):

        vars = wcomponents.WTemplated.getVars(self)
        vars["declined"] = self._getDeclinedParticipantsList()
        vars["numberDeclined"] = self._conf.getParticipation().getDeclinedNumber()
        return vars

    def _getDeclinedParticipantsList(self):
        l = []

        for k in self._conf.getParticipation().getDeclinedParticipantList().keys():
            p = self._conf.getParticipation().getDeclinedParticipantByKey(k)
            l.append((k, p))
        return l


class WPConfModifParticipantsDeclined(WPConferenceModifParticipantBase):

    def _setActiveTab(self):
        self._tabParticipantsDeclinedList.setActive()

    def _getTabContent(self, params):
        p = WConferenceParticipantsDeclined(self._conf)
        return p.getHTML()


class WConferenceParticipantsStatistics(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):

        vars = wcomponents.WTemplated.getVars(self)
        vars["invited"] = self._conf.getParticipation().getInvitedNumber()
        vars["rejected"] = self._conf.getParticipation().getRejectedNumber()
        vars["added"] = self._conf.getParticipation().getAddedNumber()
        vars["refused"] = self._conf.getParticipation().getRefusedNumber()
        vars["pending"] = self._conf.getParticipation().getPendingNumber()
        vars["declined"] = self._conf.getParticipation().getDeclinedNumber()
        vars["conferenceStarted"] = nowutc() > self._conf.getStartDate()
        vars["present"] = self._conf.getParticipation().getPresentNumber()
        vars["absent"] = self._conf.getParticipation().getAbsentNumber()
        vars["excused"] = self._conf.getParticipation().getExcusedNumber()
        return vars


class WPConfModifParticipantsStatistics(WPConferenceModifParticipantBase):

    def _setActiveTab(self):
        self._tabStatistics.setActive()

    def _getTabContent(self, params):
        p = WConferenceParticipantsStatistics(self._conf)
        return p.getHTML(params)


class WPConfModifParticipantsInvitationBase(WPConferenceDisplayBase):

    def _getHeader(self):
        """
        """
        wc = wcomponents.WMenuSimpleEventHeader(self._getAW(), self._conf)
        return wc.getHTML({"loginURL": self.getLoginURL(),\
                            "logoutURL": self.getLogoutURL(),\
                            "confId": self._conf.getId(),\
                            "currentView": "static",\
                            "type": WebFactory.getId(),\
                            "dark": True})

    def _getBody(self, params):
        return '<div style="margin:10px">{0}</div>'.format(self._getContent(params))


class WPConfModifParticipantsInvite(WPConfModifParticipantsInvitationBase):

    def _getContent(self, params):
        msg = _("Please indicate whether you want to accept or reject the invitation to '{0}'").format(self._conf.getTitle())
        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHConfParticipantsInvitation.getURL(self._conf)
        url.addParam("participantId",params["participantId"])
        return wc.getHTML(msg,
                          url,
                          {},
                          confirmButtonCaption=_("Accept"),
                          cancelButtonCaption=_("Reject"),
                          severity="accept")

#---------------------------------------------------------------------------

class WPConfModifParticipantsRefuse(WPConfModifParticipantsInvitationBase):

    def _getContent( self, params ):
        msg = i18nformat("""
        <font size="+2"> _("Are you sure you want to refuse to attend the '%s'")?</font>
              """)%(self._conf.getTitle())
        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHConfParticipantsRefusal.getURL( self._conf )
        url.addParam("participantId",params["participantId"])
        return wc.getHTML( msg, url, {}, \
                        confirmButtonCaption= _("Refuse"), cancelButtonCaption= _("Cancel") )

#---------------------------------------------------------------------------

class WConfModifListings( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self.__conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["pendingQueuesIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("listing")))
        vars["pendingQueuesURL"]=quoteattr(str(urlHandlers.UHConfModifPendingQueues.getURL( self.__conf )))
        vars["allSessionsConvenersIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("listing")))
        vars["allSessionsConvenersURL"]=quoteattr(str(urlHandlers.UHConfAllSessionsConveners.getURL( self.__conf )))
        vars["allSpeakersIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("listing")))
        vars["allSpeakersURL"]=quoteattr(str(urlHandlers.UHConfAllSpeakers.getURL( self.__conf )))
        return vars


class WPConfModifListings(WPConferenceModifBase):

    sidemenu_option = 'lists'

    def __init__(self, rh, conference):
        WPConferenceModifBase.__init__(self, rh, conference)
        self._createTabCtrl()

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()
        self._subTabSpeakers = self._tabCtrl.newTab('speakers',
            _('All Contribution Speakers'),
            urlHandlers.UHConfAllSpeakers.getURL(self._conf))
        self._subTabConveners = self._tabCtrl.newTab('conveners',
            _('All Session Conveners'),
            urlHandlers.UHConfAllSessionsConveners.getURL(self._conf))
        self._subTabUsers = self._tabCtrl.newTab('users',
            _('People Pending'),
            urlHandlers.UHConfModifPendingQueues.getURL(self._conf))

    def _getPageContent(self, params):
        self._setActiveTab()
        return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))

    def _setActiveTab(self):
        self._subTabUsers.setActive()

#---------------------------------------------------------------------------
#---------------------------------------------------------------------------

class WConferenceClone(wcomponents.WTemplated):

    def __init__(self, conference):
        self.__conf = conference

    def _getSelectDay(self):
        sd = ""
        for i in range(31) :
            selected = ""
            if datetime.today().day == (i+1) :
                selected = "selected=\"selected\""
            sd += "<OPTION VALUE=\"%d\" %s>%d\n"%(i+1, selected, i+1)
        return sd

    def _getSelectMonth(self):
        sm = ""
        month = [ "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]
        for i in range(12) :
            selected = ""
            if datetime.today().month == (i+1) :
                selected = "selected=\"selected\""
            sm += "\t<OPTION VALUE=\"%d\" %s>%s\n"%(i+1, selected, _(month[i]))
        return sm

    def _getSelectYear(self):
        sy = ""
        i = 1995
        while i < 2015 :
            selected = ""
            if datetime.today().year == i :
                selected = "selected=\"selected\""
            sy += "\t<OPTION VALUE=\"%d\" %s>%d\n"%(i, selected, i)
            i += 1
        return sy


    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["confTitle"] = self.__conf.getTitle()
        vars["confId"] = self.__conf.getId()
        vars["selectDay"] = self._getSelectDay()
        vars["selectMonth"] = self._getSelectMonth()
        vars["selectYear"] = self._getSelectYear()
        return vars


class WPConfClone(WPConfModifToolsBase):

    def _setActiveTab( self ):
        self._tabCloneEvent.setActive()

    def _getTabContent( self, params ):
        p = WConferenceClone( self._conf )
        pars = {"cancelURL": urlHandlers.UHConfModifTools.getURL(self._conf),
                "cloning": urlHandlers.UHConfPerformCloning.getURL(self._conf),
                "cloneOptions": i18nformat("""<li><input type="checkbox" name="cloneTracks" id="cloneTracks" value="1" />_("Tracks")</li>
                                     <li><input type="checkbox" name="cloneTimetable" id="cloneTimetable" value="1" />_("Full timetable")</li>
                                     <li><ul style="list-style-type: none;"><li><input type="checkbox" name="cloneSessions" id="cloneSessions" value="1" />_("Sessions")</li></ul></li>
                                     <li><input type="checkbox" name="cloneRegistration" id="cloneRegistration" value="1" >_("Registration")</li>""") }
        pars['cloneOptions'] += EventCloner.get_plugin_items(self._conf)
        return p.getHTML(pars)


class WConferenceAllSessionsConveners(wcomponents.WTemplated):

    def __init__(self, conference):
        self.__conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["confTitle"] = self.__conf.getTitle()
        vars["confId"] = self.__conf.getId()
        vars["convenerSelectionAction"] = quoteattr(str(urlHandlers.UHConfAllSessionsConvenersAction.getURL(self.__conf)))
        vars["contribSetIndex"] = 'index'
        vars["convenerNumber"] = str(len(self.__conf.getAllSessionsConvenerList()))
        vars["conveners"] = self._getAllConveners()
        return vars

    def _getTimetableURL(self, convener):
        url = urlHandlers.UHSessionModifSchedule.getURL(self.__conf)
        url.addParam("sessionId", convener.getSession().getId())
        if hasattr(convener, "getSlot"):
            timetable = "#" + str(convener.getSlot().getStartDate().strftime("%Y%m%d")) + ".s%sl%s" % (convener.getSession().getId(), convener.getSlot().getId())
        else:
            timetable = "#" + str(convener.getSession().getStartDate().strftime("%Y%m%d"))

        return "%s%s" % (url, timetable)

    def _getAllConveners(self):
        convenersFormatted = []
        convenersDict = self.__conf.getAllSessionsConvenerList()

        for key, conveners in convenersDict.iteritems():
            data = None

            for convener in convenersDict[key]:

                if not data:
                    data = {
                        'email': convener.getEmail(),
                        'name': convener.getFullName() or '',
                        'sessions': []
                    }

                sessionData = {
                    'title': '',
                    'urlTimetable': self._getTimetableURL(convener),
                    'urlSessionModif': None
                }

                if isinstance(convener, conference.SlotChair):
                    title = convener.getSlot().getTitle() or "Block %s" % convener.getSlot().getId()
                    sessionData['title'] = convener.getSession().getTitle() + ': ' + title
                else:
                    url = urlHandlers.UHSessionModification.getURL(self.__conf)
                    url.addParam('sessionId', convener.getSession().getId())

                    sessionData['urlSessionModif'] = str(url)
                    sessionData['title'] = convener.getSession().getTitle() or ''

                data['sessions'].append(sessionData)

            convenersFormatted.append(data)

        return convenersFormatted


class WPConfAllSessionsConveners(WPConfModifListings):

    def _setActiveTab(self):
        self._subTabConveners.setActive()

    def _getTabContent(self, params):
        p = WConferenceAllSessionsConveners(self._conf)
        return p.getHTML()

#---------------------------------------------------------------------------------------


class WConfModifAllContribParticipants(wcomponents.WTemplated):

    def __init__(self, conference, partIndex):
        self._title = _("All participants list")
        self._conf = conference
        self._order = ""
        self._dispopts = ["Email", "Contributions"]
        self._partIndex = partIndex

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        self._url = vars["participantMainPageURL"]
        vars["speakers"] = self._getAllParticipants()
        vars["participantNumber"] = str(len(self._partIndex.getParticipationKeys()))

        return vars

    def _getAllParticipants(self):
        speakers = []

        for key in self._partIndex.getParticipationKeys():
            participationList = self._partIndex.getById(key)

            if participationList:
                participant = participationList[0]

                pData = {
                    'name': participant.getFullName(),
                    'email': participant.getEmail(),
                    'contributions': []
                }

                for participation in participationList:
                    contribution = participation.getContribution()

                    if contribution:
                        pData['contributions'].append({
                            'title': contribution.getTitle(),
                            'url': str(urlHandlers.UHContributionModification.getURL(contribution))
                        })

                speakers.append(pData)

        return speakers

    def _getURL(self):
        return self._url


class WPConfAllSpeakers(WPConfModifListings):

    def _setActiveTab(self):
        self._subTabSpeakers.setActive()

    def _getTabContent(self, params):
        p = WConfModifAllContribParticipants( self._conf, self._conf.getSpeakerIndex() )
        return p.getHTML({"title": _("All speakers list"), \
                          "participantMainPageURL":urlHandlers.UHConfAllSpeakers.getURL(self._conf), \
                          "participantSelectionAction":quoteattr(str(urlHandlers.UHConfAllSpeakersAction.getURL(self._conf)))})


class WPEMailContribParticipants ( WPConfModifListings):
    def __init__(self, rh, conf, participantList):
        WPConfModifListings.__init__(self, rh, conf)
        self._participantList = participantList

    def _getPageContent(self,params):
        wc = WEmailToContribParticipants(self._conf, self._getAW().getUser(), self._participantList)
        return wc.getHTML()

class WEmailToContribParticipants(wcomponents.WTemplated):
    def __init__(self,conf,user,contribParticipantList):
        self._conf = conf
        try:
            self._fromemail = user.getEmail()
        except:
            self._fromemail = ""
        self._contribParticipantList = contribParticipantList

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        toEmails=[]
        toIds=[]
        for email in self._contribParticipantList:
            if len(email) > 0 :
                toEmails.append(email)
        vars["From"] = self._fromemail
        vars["toEmails"]= ", ".join(toEmails)
        vars["emails"]= ",".join(toEmails)
        vars["postURL"]=urlHandlers.UHContribParticipantsSendEmail.getURL(self._conf)
        vars["subject"]=""
        vars["body"]=""
        return vars
#---------------------------------------------------------------------------------------

class WPEMailConveners ( WPConfModifListings):
    def __init__(self, rh, conf, convenerList):
        WPConfModifListings.__init__(self, rh, conf)
        self._convenerList = convenerList

    def _getPageContent(self,params):
        wc = WEmailToConveners(self._conf, self._getAW().getUser(), self._convenerList)
        return wc.getHTML()

class WEmailToConveners(wcomponents.WTemplated):
    def __init__(self,conf,user,convenerList):
        self._conf = conf
        try:
            self._fromemail = user.getEmail()
        except:
            self._fromemail = ""
        self._convenerList = convenerList

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        toEmails=[]
        toIds=[]
        for email in self._convenerList:
            if len(email) > 0 :
                toEmails.append(email)
        vars["From"] = self._fromemail
        vars["toEmails"]= ", ".join(toEmails)
        vars["emails"]= ",".join(toEmails)
        vars["postURL"]=urlHandlers.UHConvenersSendEmail.getURL(self._conf)
        vars["subject"]=""
        vars["body"]=""
        return vars


#---------------------------------------------------------------------------------------


class WConvenerSentMail  (wcomponents.WTemplated):
    def __init__(self,conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["BackURL"]=quoteattr(str(urlHandlers.UHConfAllSessionsConveners.getURL(self._conf)))
        return vars

class WPConvenerSentEmail( WPConfModifListings ):
    def _getTabContent(self,params):
        wc = WConvenerSentMail(self._conf)
        return wc.getHTML()


class WContribParticipationSentMail(wcomponents.WTemplated):
    def __init__(self,conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["BackURL"]=quoteattr(str(urlHandlers.UHConfAllSpeakers.getURL(self._conf)))
        return vars


class WPContribParticipationSentEmail( WPConfModifListings ):
    def _getTabContent(self,params):
        wc = WContribParticipationSentMail(self._conf)
        return wc.getHTML()


class WConfModifCFA(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def _getAbstractFieldsHTML(self, vars):
        abMgr = self._conf.getAbstractMgr()
        enabledText = _("Click to disable")
        disabledText = _("Click to enable")
        laf = []
        urlRemove = str(urlHandlers.UHConfModifCFARemoveOptFld.getURL(self._conf))
        laf.append("""<form action="" method="POST">""")
        for af in abMgr.getAbstractFieldsMgr().getFields():
            urlUp = urlHandlers.UHConfModifCFAAbsFieldUp.getURL(self._conf)
            urlUp.addParam("fieldId", af.getId())
            urlDown = urlHandlers.UHConfModifCFAAbsFieldDown.getURL(self._conf)
            urlDown.addParam("fieldId", af.getId())
            if af.isMandatory():
                mandatoryText = _("mandatory")
            else:
                mandatoryText = _("optional")
            maxCharText = ""
            if isinstance(af, AbstractTextField):
                maxCharText = " - "
                if int(af.getMaxLength()) != 0:
                    maxCharText += _("max: %s %s.") % (af.getMaxLength(), af.getLimitation())
                else:
                    maxCharText += _("not limited")
            addInfo = "(%s%s)" % (mandatoryText, maxCharText)
            url = urlHandlers.UHConfModifCFAOptFld.getURL(self._conf)
            url.addParam("fieldId", af.getId())
            url = quoteattr("%s#optional" % str(url))
            if self._conf.getAbstractMgr().hasEnabledAbstractField(af.getId()):
                icon = vars["enablePic"]
                textIcon = enabledText
            else:
                icon = vars["disablePic"]
                textIcon = disabledText
            if af.getId() == "content":
                removeButton = ""
            else:
                removeButton = "<input type=\"checkbox\" name=\"fieldId\" value=\"%s\">" % af.getId()
            laf.append("""
                            <tr>
                                <td>
                                  <a href=%s><img src=%s alt="%s" class="imglink"></a>&nbsp;<a href=%s><img src=%s border="0" alt=""></a><a href=%s><img src=%s border="0" alt=""></a>
                                </td>
                                <td width="1%%">%s</td>
                                <td>
                                  &nbsp;<a class="edit-field" href="#" data-id=%s data-fieldType=%s>%s</a> %s
                                </td>
                            </tr>
                            """ % (
                                url,
                                icon,
                                textIcon,
                                quoteattr(str(urlUp)),
                                quoteattr(str(Config.getInstance().getSystemIconURL("upArrow"))),
                                quoteattr(str(urlDown)),
                                quoteattr(str(Config.getInstance().getSystemIconURL("downArrow"))),
                                removeButton,
                                af.getId(),
                                af.getType(),
                                af.getCaption(),
                                addInfo))
        laf.append(i18nformat("""
    <tr>
      <td align="right" colspan="3">
        <input type="submit" value="_("remove")" onClick="this.form.action='%s';" class="btn">
        <input id="add-field-button" type="submit" value="_("add")" class="btn">
      </td>
    </tr>
    </form>""") % urlRemove)
        laf.append("</form>")
        return "".join(laf)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        abMgr = self._conf.getAbstractMgr()

        vars["iconDisabled"] = str(Config.getInstance().getSystemIconURL("disabledSection"))
        vars["iconEnabled"] = str(Config.getInstance().getSystemIconURL("enabledSection"))

        vars["multipleTracks"] = abMgr.getMultipleTracks()
        vars["areTracksMandatory"] = abMgr.areTracksMandatory()
        vars["canAttachFiles"] = abMgr.canAttachFiles()
        vars["showSelectAsSpeaker"] = abMgr.showSelectAsSpeaker()
        vars["isSelectSpeakerMandatory"] = abMgr.isSelectSpeakerMandatory()
        vars["showAttachedFilesContribList"] = abMgr.showAttachedFilesContribList()

        vars["multipleUrl"] = urlHandlers.UHConfCFASwitchMultipleTracks.getURL(self._conf)
        vars["mandatoryUrl"] = urlHandlers.UHConfCFAMakeTracksMandatory.getURL(self._conf)
        vars["attachUrl"] = urlHandlers.UHConfCFAAllowAttachFiles.getURL(self._conf)
        vars["showSpeakerUrl"] = urlHandlers.UHConfCFAShowSelectAsSpeaker.getURL(self._conf)
        vars["speakerMandatoryUrl"] = urlHandlers.UHConfCFASelectSpeakerMandatory.getURL(self._conf)
        vars["showAttachedFilesUrl"] = urlHandlers.UHConfCFAAttachedFilesContribList.getURL(self._conf)

        vars["setStatusURL"] = urlHandlers.UHConfCFAChangeStatus.getURL(self._conf)
        vars["dataModificationURL"] = urlHandlers.UHCFADataModification.getURL(self._conf)
        if abMgr.getCFAStatus():
            vars["changeTo"] = "False"
            vars["status"] = _("ENABLED")
            vars["changeStatus"] = _("DISABLE")
            vars["startDate"] = format_date(abMgr.getStartSubmissionDate(), format='full')
            vars["endDate"] = format_date(abMgr.getEndSubmissionDate(), format='full')
            vars["announcement"] = abMgr.getAnnouncement()
            vars["disabled"] = ""
            modifDL = abMgr.getModificationDeadline()
            vars["modifDL"] = i18nformat("""--_("not specified")--""")
            if modifDL:
                vars["modifDL"] = format_date(modifDL, format='full')
            vars["notification"] = i18nformat("""
                        <table align="left">
                            <tr>
                                <td align="right"><b> _("To List"):</b></td>
                                <td align="left">%s</td>
                            </tr>
                            <tr>
                                <td align="right"><b> _("Cc List"):</b></td>
                                <td align="left">%s</td>
                            </tr>
                        </table>
                        """) % (", ".join(abMgr.getSubmissionNotification().getToList()) or i18nformat("""--_("no TO list")--"""), ", ".join(abMgr.getSubmissionNotification().getCCList()) or i18nformat("""--_("no CC list")--"""))
        else:
            vars["changeTo"] = "True"
            vars["status"] = _("DISABLED")
            vars["changeStatus"] = _("ENABLE")
            vars["startDate"] = ""
            vars["endDate"] = ""
            vars["announcement"] = ""
            vars["manage"] = ""
            vars["type"] = ""
            vars["disabled"] = "disabled"
            vars["modifDL"] = ""
            vars["submitters"] = ""
            vars["notification"] = ""
        vars["enablePic"] = quoteattr(str(Config.getInstance().getSystemIconURL("enabledSection")))
        vars["disablePic"] = quoteattr(str(Config.getInstance().getSystemIconURL("disabledSection")))
        vars["abstractFields"] = self._getAbstractFieldsHTML(vars)
        vars["addNotifTplURL"] = urlHandlers.UHAbstractModNotifTplNew.getURL(self._conf)
        vars["remNotifTplURL"] = urlHandlers.UHAbstractModNotifTplRem.getURL(self._conf)
        vars["confId"] = self._conf.getId()
        vars["lateAuthUsers"] = fossilize(self._conf.getAbstractMgr().getAuthorizedSubmitterList())
        return vars


class WPConfModifCFAPreview(WPConferenceModifAbstractBase):

    def _setActiveTab(self):
        self._tabCFAPreview.setActive()

    def _getHeadContent(self):
        return WPConferenceModifAbstractBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])

    def getCSSFiles(self):
        return WPConferenceModifAbstractBase.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def getJSFiles(self):
        return WPConferenceModifAbstractBase.getJSFiles(self) + \
            self._asset_env['abstracts_js'].urls()

    def _getTabContent(self, params):
        import MaKaC.webinterface.pages.abstracts as abstracts
        wc = abstracts.WAbstractDataModification(self._conf)
        # Simulate fake abstract
        from MaKaC.webinterface.common.abstractDataWrapper import AbstractData
        ad = AbstractData(self._conf.getAbstractMgr(), {}, 9999)
        params = ad.toDict()
        params["postURL"] = ""
        params["origin"] = "management"
        return wc.getHTML(params)


class WPConfModifCFA(WPConferenceModifAbstractBase):

    def _setActiveTab(self):
        self._tabCFA.setActive()

    def _getTabContent(self, params):
        wc = WConfModifCFA(self._conf)
        return wc.getHTML()


class WCFADataModification(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        abMgr = self._conf.getAbstractMgr()
        vars["sDay"] = abMgr.getStartSubmissionDate().day
        vars["sMonth"] = abMgr.getStartSubmissionDate().month
        vars["sYear"] = abMgr.getStartSubmissionDate().year

        vars["eDay"] = abMgr.getEndSubmissionDate().day
        vars["eMonth"] = abMgr.getEndSubmissionDate().month
        vars["eYear"] = abMgr.getEndSubmissionDate().year

        vars["mDay"] = ""
        vars["mMonth"] = ""
        vars["mYear"] = ""
        if abMgr.getModificationDeadline():
            vars["mDay"] = str(abMgr.getModificationDeadline().day)
            vars["mMonth"] = str(abMgr.getModificationDeadline().month)
            vars["mYear"] = str(abMgr.getModificationDeadline().year)

        vars["announcement"] = abMgr.getAnnouncement()
        vars["toList"] = ", ".join(abMgr.getSubmissionNotification().getToList())
        vars["ccList"] = ", ".join(abMgr.getSubmissionNotification().getCCList())
        vars["postURL"] = urlHandlers.UHCFAPerformDataModification.getURL(self._conf)
        return vars


class WPCFADataModification(WPConferenceModifAbstractBase):

    def _setActiveTab(self):
        self._tabCFA.setActive()

    def _getTabContent(self, params):
        p = WCFADataModification(self._conf)
        return p.getHTML()


class WConfModifProgram(wcomponents.WTemplated):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["deleteItemsURL"]=urlHandlers.UHConfDelTracks.getURL(self._conf)
        vars["addTrackURL"]=urlHandlers.UHConfAddTrack.getURL( self._conf )
        vars["conf"] = self._conf
        return vars


class WPConfModifProgram( WPConferenceModifBase ):

    sidemenu_option = 'program'

    def _getPageContent( self, params ):
        wc = WConfModifProgram( self._conf )
        return wc.getHTML()


class WTrackCreation( wcomponents.WTemplated ):

    def __init__( self, targetConf ):
        self.__conf = targetConf

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars['title'] = ''
        vars['description'] = ''
        return vars



class WPConfAddTrack( WPConfModifProgram ):

    def _getPageContent( self, params ):
        p = WTrackCreation( self._conf )
        pars = {"postURL": urlHandlers.UHConfPerformAddTrack.getURL(self._conf)}
        return p.getHTML( pars )

class WFilterCriteriaAbstracts(wcomponents.WFilterCriteria):
    """
    Draws the options for a filter criteria object
    This means rendering the actual table that contains
    all the HTML for the several criteria
    """

    def __init__(self, options, filterCrit, extraInfo=""):
        wcomponents.WFilterCriteria.__init__(self, options, filterCrit, extraInfo)

    def _drawFieldOptions(self, id, data):
        page = WFilterCriterionOptionsAbstracts(id, data)

        # TODO: remove when we have a better template system
        return page.getHTML()

class WFilterCriterionOptionsAbstracts(wcomponents.WTemplated):

    def __init__(self, id, data):
        self._id = id
        self._data = data

    def getVars(self):

        vars = wcomponents.WTemplated.getVars( self )

        vars["id"] = self._id
        vars["title"] = self._data["title"]
        vars["options"] = self._data["options"]
        vars["selectFunc"] = self._data.get("selectFunc", True)

        return vars

class WAbstracts( wcomponents.WTemplated ):

    # available columns
    COLUMNS = ["ID", "Title", "PrimaryAuthor", "Tracks", "Type", "Status", "Rating", "AccTrack", "AccType", "SubmissionDate", "ModificationDate"]

    def __init__( self, conference, filterCrit, sortingCrit, order, display, filterUsed):
        self._conf = conference
        self._filterCrit = filterCrit
        self._sortingCrit = sortingCrit
        self._order = order
        self._display = display
        self._filterUsed = filterUsed

    def _getURL( self, sortingField, column ):
        url = urlHandlers.UHConfAbstractManagment.getURL(self._conf)
        url.addParam("sortBy", column)
        if sortingField and sortingField.getId() == column:
            if self._order == "down":
                url.addParam("order","up")
            elif self._order == "up":
                url.addParam("order","down")
        return url


    def _getTrackFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("track")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ i18nformat("""<input type="checkbox" name="trackShowNoValue"%s> --_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked = ""
            if field is not None and t.getId() in field.getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="track" value=%s%s> (%s) %s\n"""%(quoteattr(t.getId()),checked,self.htmlText(t.getCode()),self.htmlText(t.getTitle())))
        return l

    def _getContribTypeFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("type")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ i18nformat("""<input type="checkbox" name="typeShowNoValue"%s> --_("not specified")--""")%checked]
        for contribType in self._conf.getContribTypeList():
            checked = ""
            if field is not None and contribType.getId() in field.getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="type" value=%s%s> %s"""%(quoteattr(contribType.getId()), checked, self.htmlText(contribType.getName())) )
        return l

    def _getAccTrackFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("acc_track")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ i18nformat("""<input type="checkbox" name="accTrackShowNoValue"%s> --_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked = ""
            if field is not None and t.getId() in field.getValues():
                checked=" checked"
            l.append("""<input type="checkbox" name="acc_track" value=%s%s> (%s) %s"""%(quoteattr(t.getId()),checked,self.htmlText(t.getCode()),self.htmlText(t.getTitle())))
        return l

    def _getAccContribTypeFilterItemList( self ):
        checked = ""
        field=self._filterCrit.getField("acc_type")
        if field is not None and field.getShowNoValue():
            checked = " checked"
        l = [ i18nformat("""<input type="checkbox" name="accTypeShowNoValue"%s> --_("not specified")--""")%checked]
        for contribType in self._conf.getContribTypeList():
            checked = ""
            if field is not None and contribType.getId() in field.getValues():
                checked = " checked"
            l.append( """<input type="checkbox" name="acc_type" value=%s%s> %s"""%(quoteattr(contribType.getId()),checked,self.htmlText(contribType.getName())))
        return l

    def _getStatusFilterItemList( self ):
        l = []
        for status in AbstractStatusList.getInstance().getStatusList():
            checked = ""
            statusId = AbstractStatusList.getInstance().getId( status )
            statusCaption = AbstractStatusList.getInstance().getCaption( status )
            statusCode=AbstractStatusList.getInstance().getCode(status)
            statusIconURL= AbstractStatusList.getInstance().getIconURL( status )
            field=self._filterCrit.getField("status")
            if field is not None and statusId in field.getValues():
                checked = "checked"
            imgHTML = """<img src=%s border="0" alt="">"""%(quoteattr(str(statusIconURL)))
            l.append( """<input type="checkbox" name="status" value=%s%s>%s (%s) %s"""%(quoteattr(statusId),checked,imgHTML,self.htmlText(statusCode),self.htmlText(statusCaption)))
        return l

    def _getOthersFilterItemList( self ):
        checkedShowMultiple, checkedShowComments = "", ""
        track_field=self._filterCrit.getField("track")
        if track_field is not None and track_field.onlyMultiple():
            checkedShowMultiple = " checked"
        if self._filterCrit.getField("comment") is not None:
            checkedShowComments = " checked"
        l = [ i18nformat("""<input type="checkbox" name="trackShowMultiple"%s> _("only multiple tracks")""")%checkedShowMultiple,
                i18nformat("""<input type="checkbox" name="comment"%s> _("only with comments")""")%checkedShowComments]
        return l

    def _getFilterMenu(self):

        options = [
            ('Tracks', {"title": _("tracks"),
                        "options": self._getTrackFilterItemList()}),
            ('Types', {"title": _("types"),
                       "options": self._getContribTypeFilterItemList()}),
            ('Status', {"title": _("status"),
                       "options": self._getStatusFilterItemList()}),
            ('AccTracks', {"title": _("(proposed to be) accepted for tracks"),
                       "options": self._getAccTrackFilterItemList()}),
            ('AccTypes', {"title": _("(proposed to be) accepted for types"),
                       "options": self._getAccContribTypeFilterItemList()}),
            ('Others', {"title": _("others"),
                       "selectFunc": False,
                       "options": self._getOthersFilterItemList()})
            ]

        extraInfo = ""
        if self._conf.getRegistrationForm().getStatusesList():
            extraInfo = i18nformat("""<table align="center" cellspacing="10" width="100%%">
                                <tr>
                                    <td colspan="5" class="titleCellFormat"> _("Author search") <input type="text" name="authSearch" value=%s></td>
                                </tr>
                            </table>
                        """)%(quoteattr(str(self._authSearch)))

        p = WFilterCriteriaAbstracts(options, None, extraInfo)

        return p.getHTML()


    def _getColumnTitlesDict(self):
        """
            Dictionary with the translation from "ids" to "name to display" for each of the options you can choose for the display.
            This method complements the method "_setDispOpts" in which we get a dictonary with "ids".
        """
        if not hasattr(self, "_columns"):
            self._columns = {"ID": "ID","Title": "Title", "PrimaryAuthor": "Primary Author", "Tracks": "Tracks", "Type": "Type", "Status":"Status", \
                      "Rating":" Rating", "AccTrack": "Acc. Track", "AccType": "Acc. Type", "SubmissionDate": "Submission Date", "ModificationDate": "Modification Date"}
        return self._columns

    def _getDisplay(self):
        """
            These are the 'display' options selected by the user. In case no options were selected we add some of them by default.
        """
        display = self._display[:]

        if display == []:
            display = self.COLUMNS
        return display

    def _getAccType(self, abstract):
        status = abstract.getCurrentStatus()
        if isinstance(status,(review.AbstractStatusAccepted, review.AbstractStatusProposedToAccept)) and status.getType() is not None:
            return self.htmlText(status.getType().getName())
        return ""

    def _getAccTrack(self, abstract):
        acc_track = abstract.getAcceptedTrack()
        if not acc_track:
            return ""
        return self.htmlText(acc_track.getCode())

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["abstractSelectionAction"]=quoteattr(str(urlHandlers.UHAbstractConfSelectionAction.getURL(self._conf)))
        vars["confId"] = self._conf.getId()
        self._authSearch=vars.get("authSearch","")

        vars["filterMenu"] = self._getFilterMenu()

        sortingField=None
        if self._sortingCrit is not None:
            sortingField=self._sortingCrit.getField()

        vars["sortingField"] = sortingField.getId()
        vars["order"] = self._order
        vars["downArrow"] = Config.getInstance().getSystemIconURL("downArrow")
        vars["upArrow"] = Config.getInstance().getSystemIconURL("upArrow")
        vars["getSortingURL"] = lambda column: self._getURL(sortingField, column)
        vars["getAccType"] = lambda abstract: self._getAccType(abstract)
        vars["getAccTrack"] = lambda abstract: self._getAccTrack(abstract)

        f = filters.SimpleFilter( self._filterCrit, self._sortingCrit )
        abstractList=f.apply(self._conf.getAbstractMgr().getAbstractsMatchingAuth(self._authSearch))
        if self._order =="up":
            abstractList.reverse()
        vars["abstracts"] = abstractList

        vars["totalNumberAbstracts"] = str(len(self._conf.getAbstractMgr().getAbstractList()))
        vars["filteredNumberAbstracts"] = str(len(abstractList))
        vars["filterUsed"] = self._filterUsed
        vars["accessAbstract"] = quoteattr(str(urlHandlers.UHAbstractDirectAccess.getURL(self._conf)))

        url = urlHandlers.UHConfAbstractManagment.getURL(self._conf)
        url.setSegment( "results" )
        vars["filterPostURL"] = quoteattr(str(url))
        vars["excelIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("excel")))
        vars["pdfIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("pdf")))
        vars["xmlIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("xml")))
        vars["displayColumns"] = self._getDisplay()
        vars["columnsDict"] = self._getColumnTitlesDict()
        vars["columns"] = self.COLUMNS

        return vars

class WPConfAbstractList( WPConferenceModifAbstractBase ):

    def __init__(self, rh, conf, msg, filterUsed = False ):
        self._msg = msg
        self._filterUsed = filterUsed
        WPConferenceModifAbstractBase.__init__(self, rh, conf)

    def _getTabContent( self, params ):
        order = params.get("order","down")
        wc = WAbstracts( self._conf, params.get("filterCrit", None ),
                            params.get("sortingCrit", None),
                            order,
                            params.get("display",None),
                            self._filterUsed )
        p = {"authSearch":params.get("authSearch","")}
        return wc.getHTML( p )

    def _setActiveTab(self):
        self._tabAbstractList.setActive()


class WPModNewAbstract(WPConfAbstractList):

    def __init__(self, rh, conf, abstractData):
        WPConfAbstractList.__init__(self, rh, conf, "")

    def _getTabContent(self, params):
        from MaKaC.webinterface.pages.abstracts import WAbstractDataModification
        params["postURL"] = urlHandlers.UHConfModNewAbstract.getURL(self._conf)
        params["origin"] = "management"
        wc = WAbstractDataModification(self._conf)
        return wc.getHTML(params)

    def getCSSFiles(self):
        return WPConfAbstractList.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def getJSFiles(self):
        return WPConfAbstractList.getJSFiles(self) + \
            self._includeJSPackage('Management') + \
            self._asset_env['abstracts_js'].urls()

    def _getHeadContent(self):
        return WPConfAbstractList._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])


class WConfModAbstractsMerge(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf=conf

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfModAbstractsMerge.getURL(self._conf)))
        vars["selAbstracts"]=",".join(vars.get("absIdList",[]))
        vars["targetAbs"]=quoteattr(str(vars.get("targetAbsId","")))
        vars["inclAuthChecked"]=""
        if vars.get("inclAuth",False):
            vars["inclAuthChecked"]=" checked"
        vars["comments"]=self.htmlText(vars.get("comments",""))
        vars["notifyChecked"]=""
        if vars.get("notify",False):
            vars["notifyChecked"]=" checked"
        return vars


class WPModMergeAbstracts(WPConfAbstractList):

    def __init__(self, rh, conf):
        WPConfAbstractList.__init__(self, rh, conf, "")

    def _getTabContent(self, params):
        wc = WConfModAbstractsMerge(self._conf)
        p = {"absIdList": params.get("absIdList", []),
             "targetAbsId": params.get("targetAbsId", ""),
             "inclAuth": params.get("inclAuth", False),
             "comments": params.get("comments", ""),
             "notify": params.get("notify", True),
             }
        return wc.getHTML(p)


class WPConfParticipantList( WPConfAbstractList ):

    def __init__(self, rh, conf, emailList, displayedGroups, abstracts):
        WPConfAbstractList.__init__(self, rh, conf, None)
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._abstracts = abstracts

    def _getTabContent( self, params ):
        wc = WAbstractsParticipantList(self._conf, self._emailList, self._displayedGroups, self._abstracts)
        return wc.getHTML()

class WPConfModifParticipantList( WPConferenceBase ):

    def __init__(self, rh, conf, emailList, displayedGroups, contribs):
        WPConferenceBase.__init__(self, rh, conf)
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._contribs = contribs

    def _getBody( self, params ):
        WPConferenceBase._getBody(self, params)
        wc = WContribParticipantList(self._conf, self._emailList, self._displayedGroups, self._contribs)
        params = {"urlDisplayGroup":urlHandlers.UHContribsConfManagerDisplayParticipantList.getURL(self._conf)}
        return wc.getHTML(params)


class WConfModifContribList(wcomponents.WTemplated):

    def __init__(self,conf,filterCrit, sortingCrit, order, filterUsed=False, filterUrl=None):
        self._conf=conf
        self._filterCrit=filterCrit
        self._sortingCrit=sortingCrit
        self._order = order
        self._totaldur =timedelta(0)
        self._filterUsed = filterUsed
        self._filterUrl = filterUrl


    def _getURL( self ):
        #builds the URL to the contribution list page
        #   preserving the current filter and sorting status
        url = urlHandlers.UHConfModifContribList.getURL(self._conf)

        #save params in websession
        dict = session.setdefault('ContributionFilterConf%s' % self._conf.getId(), {})
        if self._filterCrit.getField("type"):
            l=[]
            for t in self._filterCrit.getField("type").getValues():
                if t!="":
                    l.append(t)
            dict["types"] = l
            if self._filterCrit.getField("type").getShowNoValue():
                dict["typeShowNoValue"] = "1"

        if self._filterCrit.getField("track"):
            dict["tracks"] = self._filterCrit.getField("track").getValues()
            if self._filterCrit.getField("track").getShowNoValue():
                dict["trackShowNoValue"] = "1"

        if self._filterCrit.getField("session"):
            dict["sessions"] = self._filterCrit.getField("session").getValues()
            if self._filterCrit.getField("session").getShowNoValue():
                dict["sessionShowNoValue"] = "1"

        if self._filterCrit.getField("status"):
            dict["status"] = self._filterCrit.getField("status").getValues()

        if self._sortingCrit.getField():
            dict["sortBy"] = self._sortingCrit.getField().getId()
            dict["order"] = "down"
        dict["OK"] = "1"
        session.modified = True

        return url

    def _getMaterialsHTML(self, contrib):
        attached_items = contrib.attached_items
        if attached_items:
            num_files = len(attached_items['files']) + sum(len(f.attachments) for f in attached_items['folders'])
            return '<a href="{}">{}</a>'.format(
                url_for('attachments.management', contrib),
                ngettext('1 file', '{num} files', num_files).format(num=num_files)
            )

    def _getContribHTML( self, contrib ):
        try:
            sdate=contrib.getAdjustedStartDate().strftime("%d-%b-%Y %H:%M" )
        except AttributeError:
            sdate = ""
        title = """<a href=%s>%s</a>"""%( quoteattr( str( urlHandlers.UHContributionModification.getURL( contrib ) ) ), self.htmlText( contrib.getTitle() ))
        strdur = ""
        if contrib.getDuration() is not None and contrib.getDuration().seconds != 0:
            strdur = (datetime(1900,1,1)+ contrib.getDuration()).strftime("%Hh%M'")
            dur = contrib.getDuration()
            self._totaldur = self._totaldur + dur

        l = [self.htmlText( spk.getFullName() ) for spk in contrib.getSpeakerList()]
        speaker = "<br>".join( l )
        session = ""
        if contrib.getSession() is not None:
            if contrib.getSession().getCode() != "no code":
                session=self.htmlText(contrib.getSession().getCode())
            else:
                session=self.htmlText(contrib.getSession().getId())
        track = ""
        if contrib.getTrack() is not None:
            if contrib.getTrack().getCode() is not None:
                track = self.htmlText( contrib.getTrack().getCode() )
            else:
                track = self.htmlText( contrib.getTrack().getId() )
        cType=""
        if contrib.getType() is not None:
            cType=self.htmlText(contrib.getType().getName())
        status=contrib.getCurrentStatus()
        statusCaption=ContribStatusList().getCode(status.__class__)
        html = """
            <tr id="contributions%s" style="background-color: transparent;" onmouseout="javascript:onMouseOut('contributions%s')" onmouseover="javascript:onMouseOver('contributions%s')">
                <td valign="top" align="right" nowrap><input onchange="javascript:isSelected('contributions%s')" type="checkbox" name="contributions" value=%s></td>
                <td valign="top" nowrap class="CRLabstractDataCell">%s</td>
                <td valign="top" nowrap class="CRLabstractDataCell">%s</td>
                <td valign="top" nowrap class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell">%s</td>
                <td valign="top" class="CRLabstractDataCell" nowrap>%s</td>
            </tr>
                """%(contrib.getId(), contrib.getId(), contrib.getId(),
                    contrib.getId(), contrib.getId(),
                    self.htmlText(contrib.getId()),
                    sdate or "&nbsp;",strdur or "&nbsp;",cType or "&nbsp;",
                    title or "&nbsp;",
                    speaker or "&nbsp;",session or "&nbsp;",
                    track or "&nbsp;",statusCaption or "&nbsp;",
                    self._getMaterialsHTML(contrib) or "&nbsp;")
        return html

    def _getTypeItemsHTML(self):
        checked=""
        if self._filterCrit.getField("type").getShowNoValue():
            checked=" checked"
        res=[ i18nformat("""<input type="checkbox" name="typeShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for t in self._conf.getContribTypeList():
            checked=""
            if t.getId() in self._filterCrit.getField("type").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="types" value=%s%s> %s"""%(quoteattr(str(t.getId())),checked,self.htmlText(t.getName())))
        return res

    def _getSessionItemsHTML(self):
        checked=""
        if self._filterCrit.getField("session").getShowNoValue():
            checked=" checked"
        res=[ i18nformat("""<input type="checkbox" name="sessionShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for s in self._conf.getSessionListSorted():
            checked=""
            l = self._filterCrit.getField("session").getValues()
            if not isinstance(l, list):
                l = [l]
            if s.getId() in l:
                checked=" checked"
            res.append("""<input type="checkbox" name="sessions" value=%s%s> (%s) %s"""%(quoteattr(str(s.getId())),checked,self.htmlText(s.getCode()),self.htmlText(s.getTitle())))
        return res

    def _getTrackItemsHTML(self):
        checked=""
        if self._filterCrit.getField("track").getShowNoValue():
            checked=" checked"
        res=[ i18nformat("""<input type="checkbox" name="trackShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked=""
            if t.getId() in self._filterCrit.getField("track").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="tracks" value=%s%s> (%s) %s"""%(quoteattr(str(t.getId())),checked,self.htmlText(t.getCode()),self.htmlText(t.getTitle())))
        return res

    def _getStatusItemsHTML(self):
        res=[]
        for st in ContribStatusList().getList():
            id=ContribStatusList().getId(st)
            checked=""
            if id in self._filterCrit.getField("status").getValues():
                checked=" checked"
            code=ContribStatusList().getCode(st)
            caption=ContribStatusList().getCaption(st)
            res.append("""<input type="checkbox" name="status" value=%s%s> (%s) %s"""%(quoteattr(str(id)),checked,self.htmlText(code),self.htmlText(caption)))
        return res

    def _getFilterMenu(self):

        options = [
            ('Types', {"title": _("Types"),
                       "options": self._getTypeItemsHTML()}),
            ('Sessions', {"title": _("Sessions"),
                        "options": self._getSessionItemsHTML()}),
            ('Tracks', {"title": _("Tracks"),
                        "options": self._getTrackItemsHTML()}),
            ('Status', {"title": _("Status"),
                       "options": self._getStatusItemsHTML()})
        ]

        extraInfo = i18nformat("""<table align="center" cellspacing="10" width="100%%">
                            <tr>
                                <td colspan="5" class="titleCellFormat"> _("Author search") <input type="text" name="authSearch" value=%s></td>
                            </tr>
                        </table>
                    """)%(quoteattr(str(self._authSearch)))

        p = WFilterCriteriaContribs(options, None, extraInfo)

        return p.getHTML()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["filterUrl"] = str(self._filterUrl).replace('%', '%%')
        vars["quickSearchURL"]=quoteattr(str(urlHandlers.UHConfModContribQuickAccess.getURL(self._conf)))
        vars["filterPostURL"]=quoteattr(str(urlHandlers.UHConfModifContribList.getURL(self._conf)))
        self._authSearch=vars.get("authSearch","").strip()
        cl=self._conf.getContribsMatchingAuth(self._authSearch)

        sortingField = self._sortingCrit.getField()
        self._currentSorting=""

        if sortingField is not None:
            self._currentSorting=sortingField.getId()
        vars["currentSorting"]=""

        url=self._getURL()
        url.addParam("sortBy","number")
        vars["numberImg"]=""
        if self._currentSorting == "number":
                vars["currentSorting"] = i18nformat("""<input type="hidden" name="sortBy" value="_("number")">""")
                if self._order == "down":
                    vars["numberImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                    url.addParam("order","up")
                elif self._order == "up":
                    vars["numberImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                    url.addParam("order","down")
        vars["numberSortingURL"]=quoteattr(str(url))

        url = self._getURL()
        url.addParam("sortBy", "date")
        vars["dateImg"] = ""
        if self._currentSorting == "date":
            vars["currentSorting"]= i18nformat("""<input type="hidden" name="sortBy" value="_("date")">""")
            if self._order == "down":
                vars["dateImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["dateImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["dateSortingURL"]=quoteattr(str(url))


        url = self._getURL()
        url.addParam("sortBy", "name")
        vars["titleImg"] = ""
        if self._currentSorting == "name":
            vars["currentSorting"]= i18nformat("""<input type="hidden" name="sortBy" value="_("name")">""")
            if self._order == "down":
                vars["titleImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["titleImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["titleSortingURL"]=quoteattr(str(url))


        url = self._getURL()
        url.addParam("sortBy", "type")
        vars["typeImg"] = ""
        if self._currentSorting == "type":
            vars["currentSorting"]= i18nformat("""<input type="hidden" name="sortBy" value="_("type")">""")
            if self._order == "down":
                vars["typeImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["typeImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["typeSortingURL"] = quoteattr( str( url ) )
        url = self._getURL()
        url.addParam("sortBy", "session")
        vars["sessionImg"] = ""
        if self._currentSorting == "session":
            vars["currentSorting"] = i18nformat("""<input type="hidden" name="sortBy" value='_("session")'>""")
            if self._order == "down":
                vars["sessionImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["sessionImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["sessionSortingURL"] = quoteattr( str( url ) )
        url = self._getURL()
        url.addParam("sortBy", "speaker")
        vars["speakerImg"]=""
        if self._currentSorting=="speaker":
            vars["currentSorting"] = i18nformat("""<input type="hidden" name="sortBy" value="_("speaker")">""")
            if self._order == "down":
                vars["speakerImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["speakerImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["speakerSortingURL"]=quoteattr( str( url ) )

        url = self._getURL()
        url.addParam("sortBy","track")
        vars["trackImg"] = ""
        if self._currentSorting == "track":
            vars["currentSorting"] = i18nformat("""<input type="hidden" name="sortBy" value="_("track")">""")
            if self._order == "down":
                vars["trackImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["trackImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["trackSortingURL"] = quoteattr( str( url ) )

        f=filters.SimpleFilter(self._filterCrit,self._sortingCrit)
        filteredContribs = f.apply(cl)
        l = [self._getContribHTML(contrib) for contrib in filteredContribs]
        contribsToPrint = ["""<input type="hidden" name="contributions" value="%s">"""%contrib.getId() for contrib in filteredContribs]
        numContribs = len(filteredContribs)

        if self._order =="up":
            l.reverse()
        vars["contribsToPrint"] = "\n".join(contribsToPrint)
        vars["contributions"] = "".join(l)
        orginURL = urlHandlers.UHConfModifContribList.getURL(self._conf)
        vars["numContribs"]=str(numContribs)

        vars["totalNumContribs"] = str(len(self._conf.getContributionList()))
        vars["filterUsed"] = self._filterUsed

        vars["contributionsPDFURL"]=quoteattr(str(urlHandlers.UHContribsConfManagerDisplayMenuPDF.getURL(self._conf)))
        vars["contribSelectionAction"]=quoteattr(str(urlHandlers.UHContribConfSelectionAction.getURL(self._conf)))

        totaldur = self._totaldur
        days = totaldur.days
        hours = (totaldur.seconds)/3600
        dayhours = (days * 24)+hours
        mins = ((totaldur.seconds)/60)-(hours*60)
        vars["totaldur"] = """%sh%sm""" % (dayhours, mins)
        vars['rbActive'] = Config.getInstance().getIsRoomBookingActive()
        vars["bookings"] = Conversion.reservationsList(self._conf.getRoomBookingList())
        vars["filterMenu"] = self._getFilterMenu()
        vars["sortingOptions"]="""<input type="hidden" name="sortBy" value="%s">
                                  <input type="hidden" name="order" value="%s">"""%(self._sortingCrit.getField().getId(), self._order)
        vars["pdfIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("pdf")))
        vars["excelIconURL"] = quoteattr(str(Config.getInstance().getSystemIconURL("excel")))
        vars["xmlIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("xml")))
        return vars

class WFilterCriteriaContribs(wcomponents.WFilterCriteria):
    """
    Draws the options for a filter criteria object
    This means rendering the actual table that contains
    all the HTML for the several criteria
    """

    def __init__(self, options, filterCrit, extraInfo=""):
        wcomponents.WFilterCriteria.__init__(self, options, filterCrit, extraInfo)

    def _drawFieldOptions(self, id, data):

        page = WFilterCriterionOptionsContribs(id, data)

        # TODO: remove when we have a better template system
        return page.getHTML().replace('%','%%')

class WFilterCriterionOptionsContribs(wcomponents.WTemplated):

    def __init__(self, id, data):
        self._id = id
        self._data = data

    def getVars(self):

        vars = wcomponents.WTemplated.getVars( self )

        vars["id"] = self._id
        vars["title"] = self._data["title"]
        vars["options"] = self._data["options"]
        vars["selectFunc"] = self._data.get("selectFunc", True)

        return vars

class WPModifContribList( WPConferenceModifBase ):

    sidemenu_option = 'contributions'
    _userData = ['favorite-user-list', 'favorite-user-ids']

    def __init__(self, rh, conference, filterUsed=False):
        WPConferenceModifBase.__init__(self, rh, conference)
        self._filterUsed = filterUsed

    def _getPageContent( self, params ):
        filterCrit=params.get("filterCrit",None)
        sortingCrit=params.get("sortingCrit",None)
        order = params.get("order","down")

        filterParams = {}
        fields = getattr(filterCrit, '_fields')
        for field in fields.values():
            id = field.getId()
            showNoValue = field.getShowNoValue()
            values = field.getValues()
            if showNoValue:
                filterParams['%sShowNoValue' % id] = '--none--'
            filterParams[id] = values

        requestParams = self._rh.getRequestParams()

        operationType = requestParams.get('operationType')
        if operationType != 'resetFilters':
            operationType = 'filter'
        urlParams = dict(isBookmark='y', operationType=operationType)

        urlParams.update(self._rh.getRequestParams())
        urlParams.update(filterParams)
        filterUrl = self._rh._uh.getURL(None, **urlParams)

        wc = WConfModifContribList(self._conf,filterCrit, sortingCrit, order, self._filterUsed, filterUrl)
        p={"authSearch":params.get("authSearch","")}

        return wc.getHTML(p)

class WPConfModifContribToPDFMenu( WPModifContribList ):

    def __init__(self, rh, conf, contribIds):
        WPModifContribList.__init__(self, rh, conf)
        self._contribIds = contribIds

    def _getPageContent(self, params):

        wc = WConfModifContribToPDFMenu(self._conf, self._contribIds)
        return wc.getHTML(params)

class WConfModifContribToPDFMenu(wcomponents.WTemplated):
    def __init__(self, conf, contribIds):
        self._conf = conf
        self.contribIds = contribIds

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["createPDFURL"] = urlHandlers.UHContribsConfManagerDisplayMenuPDF.getURL(self._conf)
        l = []
        for id in self.contribIds:
            l.append("""<input type="hidden" name="contributions" value="%s">"""%id)
        vars["contribIdsList"] = "\n".join(l)
        return vars


class WConfModMoveContribsToSession(wcomponents.WTemplated):

    def __init__(self,conf,contribIdList=[]):
        self._conf=conf
        self._contribIdList=contribIdList

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfModMoveContribsToSession.getURL(self._conf)))
        vars["contribs"]=",".join(self._contribIdList)
        s=["""<option value="--none--">--none--</option>"""]
        for session in self._conf.getSessionListSorted():
            if not session.isClosed():
                s.append("""<option value=%s>%s</option>"""%(
                quoteattr(str(session.getId())),
                self.htmlText(session.getTitle())))
        vars["sessions"]="".join(s)
        return vars


class WPModMoveContribsToSession(WPModifContribList):

    def _getPageContent(self,params):
        wc=WConfModMoveContribsToSession(self._conf,params.get("contribIds",[]))
        return wc.getHTML()


class WPModMoveContribsToSessionConfirmation(WPModifContribList):

    def _getPageContent(self,params):
        wc=wcomponents.WConfModMoveContribsToSessionConfirmation(self._conf,params.get("contribIds",[]),params.get("targetSession",None))
        p={"postURL":urlHandlers.UHConfModMoveContribsToSession.getURL(self._conf),}
        return wc.getHTML(p)


class WPConfEditContribType(WPConferenceModifBase):

    sidemenu_option = 'general'

    def __init__(self, rh, ct):
        self._conf = ct.getConference()
        self._contribType = ct
        WPConferenceModifBase.__init__(self, rh, self._conf)

    def _getPageContent( self, params ):
        wc = WConfEditContribType(self._contribType)
        params["saveURL"] = quoteattr(str(urlHandlers.UHConfEditContribType.getURL(self._contribType)))
        return wc.getHTML(params)


class WConfEditContribType(wcomponents.WTemplated):

    def __init__(self, contribType):
        self._contribType = contribType

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["ctName"] = self._contribType.getName()
        vars["ctDescription"] = self._contribType.getDescription()

        return vars

class WPConfAddContribType(WPConferenceModifBase):

    sidemenu_option = 'general'

    def _getPageContent( self, params ):
        wc = WConfAddContribType()
        params["saveURL"] = quoteattr(str(urlHandlers.UHConfAddContribType.getURL(self._conf)))
        return wc.getHTML(params)


class WConfAddContribType(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        return vars

class WAbstractsParticipantList(wcomponents.WTemplated):

    def __init__(self, conf, emailList, displayedGroups, abstracts):
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._conf = conf
        self._abstracts = abstracts

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["submitterEmails"] = ",".join(self._emailList["submitters"]["emails"])
        vars["primaryAuthorEmails"] = ",".join(self._emailList["primaryAuthors"]["emails"])
        vars["coAuthorEmails"] = ",".join(self._emailList["coAuthors"]["emails"])

        urlDisplayGroup = urlHandlers.UHAbstractsConfManagerDisplayParticipantList.getURL(self._conf)
        abstractsToPrint = []
        for abst in self._abstracts:
            abstractsToPrint.append("""<input type="hidden" name="abstracts" value="%s">"""%abst)
        abstractsList = "".join(abstractsToPrint)
        displayedGroups = []
        for dg in self._displayedGroups:
            displayedGroups.append("""<input type="hidden" name="displayedGroups" value="%s">"""%dg)
        groupsList = "".join(displayedGroups)

        # Submitters
        text = _("show list")
        vars["submitters"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "submitters" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for subm in self._emailList["submitters"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                participant = "%s %s %s <%s>"%(subm.getTitle(), subm.getFirstName(), safe_upper(subm.getFamilyName()), subm.getEmail())
                l.append("<tr>\
                        <td colspan=\"2\" nowrap bgcolor=\"%s\" class=\"blacktext\">\
                        &nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["submitters"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "submitters")
        vars["showSubmitters"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), abstractsList,groupsList, text)

        # Primary authors
        text = _("show list")
        vars["primaryAuthors"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "primaryAuthors" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for pAuth in self._emailList["primaryAuthors"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                participant = "%s <%s>"%(pAuth.getFullName(), pAuth.getEmail())
                l.append("<tr><td colspan=\"2\" nowrap bgcolor=\"%s\" \
                        class=\"blacktext\">&nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["primaryAuthors"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "primaryAuthors")
        vars["showPrimaryAuthors"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), abstractsList,groupsList, text)

        # Co-Authors
        text = _("show list")
        vars["coAuthors"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "coAuthors" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for cAuth in self._emailList["coAuthors"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                cAuthEmail = cAuth.getEmail()
                if cAuthEmail.strip() == "":
                    participant = "%s"%cAuth.getFullName()
                else:
                    participant = "%s <%s>"%(cAuth.getFullName(), cAuthEmail)
                l.append("<tr><td colspan=\"2\" nowrap bgcolor=\"%s\" class=\"blacktext\">\
                        &nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["coAuthors"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "coAuthors")
        vars["showCoAuthors"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), abstractsList,groupsList, text)
        return vars

class WContribParticipantList(wcomponents.WTemplated):

    def __init__(self, conf, emailList, displayedGroups, contribs):
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._conf = conf
        self._contribs = contribs

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["speakerEmails"] = ", ".join(self._emailList["speakers"]["emails"])
        vars["primaryAuthorEmails"] = ", ".join(self._emailList["primaryAuthors"]["emails"])
        vars["coAuthorEmails"] = ", ".join(self._emailList["coAuthors"]["emails"])

        urlDisplayGroup = vars["urlDisplayGroup"]
        contribsToPrint = []
        for contrib in self._contribs:
            contribsToPrint.append("""<input type="hidden" name="contributions" value="%s">"""%contrib)
        contribsList = "".join(contribsToPrint)
        displayedGroups = []
        for dg in self._displayedGroups:
            displayedGroups.append("""<input type="hidden" name="displayedGroups" value="%s">"""%dg)
        groupsList = "".join(displayedGroups)

        # Speakers
        text = _("show list")
        vars["speakers"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "speakers" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for speaker in self._emailList["speakers"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                participant = "%s <%s>"%(speaker.getFullName(), speaker.getEmail())
                l.append("<tr>\
                        <td colspan=\"2\" nowrap bgcolor=\"%s\" class=\"blacktext\">\
                        &nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["speakers"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "speakers")
        vars["showSpeakers"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), contribsList,groupsList, text)

        # Primary authors
        text = _("show list")
        vars["primaryAuthors"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "primaryAuthors" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for pAuth in self._emailList["primaryAuthors"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                participant = "%s %s %s <%s>"%(pAuth.getTitle(), pAuth.getFirstName(), safe_upper(pAuth.getFamilyName()), pAuth.getEmail())
                l.append("<tr><td colspan=\"2\" nowrap bgcolor=\"%s\" \
                        class=\"blacktext\">&nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["primaryAuthors"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "primaryAuthors")
        vars["showPrimaryAuthors"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), contribsList,groupsList, text)

        # Co-Authors
        text = _("show list")
        vars["coAuthors"] = "<tr colspan=\"2\"><td>&nbsp;</td></tr>"
        if "coAuthors" in self._displayedGroups:
            l = []
            color = "white"
            text = _("close list")
            for cAuth in self._emailList["coAuthors"]["tree"].values():
                if color=="white":
                    color="#F6F6F6"
                else:
                    color="white"
                cAuthEmail = cAuth.getEmail()
                if cAuthEmail.strip() == "":
                    participant = "%s %s %s"%(cAuth.getTitle(), cAuth.getFirstName(), safe_upper(cAuth.getFamilyName()))
                else:
                    participant = "%s %s %s <%s>"%(cAuth.getTitle(), cAuth.getFirstName(), safe_upper(cAuth.getFamilyName()), cAuthEmail)
                l.append("<tr><td colspan=\"2\" nowrap bgcolor=\"%s\" class=\"blacktext\">\
                        &nbsp;&nbsp;&nbsp;%s</td></tr>"%(color, self.htmlText(participant)))
            vars["coAuthors"] = "".join(l)
        urlDisplayGroup.addParam("clickedGroup", "coAuthors")
        vars["showCoAuthors"] = """<form action="%s" method="post">\
                                     %s
                                     %s
                                    <input type="submit" class="btn" value="%s">
                                    </form>"""%(str(urlDisplayGroup), contribsList,groupsList, text)
        return vars


class WPAbstractSendNotificationMail(WPConferenceBase):

    def __init__(self, rh, conf, count):
        WPConferenceBase.__init__(self, rh, conf)
        self._count = count

    def _getBody( self, params ):
        return i18nformat("""
<table align="center"><tr><td align="center">
<b> _("The submitters of the selected abstracts will nearly recieve the notification mail").<br>
<br>
_("You can now close this window.")</b>
</td></tr></table>

""")


class WPContributionList( WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NEContributionList
    menu_entry_name = 'contributions'

    def _getBody( self, params ):
        wc = WConfContributionList( self._getAW(), self._conf, params["filterCrit"], params.get("filterText",""))
        return wc.getHTML()


class WConfContributionList (WConfDisplayBodyBase):

    _linkname = 'contributions'

    def __init__(self, aw, conf, filterCrit, filterText):
        self._aw = aw
        self._conf = conf
        self._filterCrit = filterCrit
        self._filterText = filterText

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)

        wvars["body_title"] = self._getTitle()
        wvars["contributions"] = self._conf.getContributionListSorted(includeWithdrawn=False, key="title")
        wvars["showAttachedFiles"] = self._conf.getAbstractMgr().showAttachedFilesContribList()
        wvars["conf"] = self._conf
        wvars["accessWrapper"] = self._aw
        wvars["filterCriteria"] = self._filterCrit
        wvars["filterText"] = self._filterText
        wvars["formatDate"] = lambda date: format_date(date, "d MMM yyyy")
        wvars["formatTime"] = lambda time: format_time(time, format="short", timezone=timezone(DisplayTZ(self._aw, self._conf).getDisplayTZ()))
        return wvars


class WConfAuthorIndex(WConfDisplayBodyBase):

    _linkname = 'author_index'

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["items"] = dict(enumerate(self._getItems()))
        return wvars

    def _getItems(self):
        res = []

        for key, authors in self._conf.getAuthorIndex().iteritems():
            # get the first identity that matches the author
            if len(authors) == 0:
                continue
            else:
                auth = next((x for x in authors if x.getContribution() and x.getContribution().getConference()), None)
                if auth is None:
                    continue

            authorURL = urlHandlers.UHContribAuthorDisplay.getURL(auth.getContribution(), authorId=auth.getId())
            contribs = []
            res.append({'fullName': auth.getFullNameNoTitle(),
                        'affiliation': auth.getAffiliation(),
                        'authorURL': authorURL,
                        'contributions': contribs})

            for auth in authors:
                contrib = auth.getContribution()
                if contrib is not None and contrib.getConference() is not None:
                    contribs.append({
                        'title': contrib.getTitle(),
                        'url': str(urlHandlers.UHContributionDisplay.getURL(auth.getContribution())),
                        'attached_items': contrib.attached_items
                    })
        return res


class WPAuthorIndex(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEAuthorIndex
    menu_entry_name = 'author_index'

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._asset_env['indico_authors'].urls()

    def _getBody(self, params):
        wc = WConfAuthorIndex(self._conf)
        return wc.getHTML()


class WConfSpeakerIndex(WConfDisplayBodyBase):

    _linkname = 'speaker_index'

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        res = collections.defaultdict(list)
        for index, key in enumerate(self._conf.getSpeakerIndex().getParticipationKeys()):
            pl = self._conf.getSpeakerIndex().getById(key)
            try:
                speaker = pl[0]
            except IndexError:
                continue
            res[index].append({'fullName': speaker.getFullNameNoTitle(), 'affiliation': speaker.getAffiliation()})
            for speaker in pl:
                if isinstance(speaker, conference.SubContribParticipation):
                    participation = speaker.getSubContrib()
                    if participation is None:
                        continue
                    url = urlHandlers.UHSubContributionDisplay.getURL(participation)
                else:
                    participation = speaker.getContribution()
                    if participation is None:
                        continue
                    url = urlHandlers.UHContributionDisplay.getURL(participation)
                if participation.getConference() is not None:
                    res[index].append({'title': participation.getTitle(),
                                       'url': str(url),
                                       'attached_items': participation.getContribution().attached_items})
        wvars["body_title"] = self._getTitle()
        wvars["items"] = res
        return wvars


class WPSpeakerIndex(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NESpeakerIndex
    menu_entry_name = 'speaker_index'

    def _getBody(self, params):
        wc=WConfSpeakerIndex(self._conf)
        return wc.getHTML()

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._asset_env['indico_authors'].urls()


class WConfMyContributions(wcomponents.WTemplated):

    def __init__(self, aw, conf):
        self._aw=aw
        self._conf=conf

    def getHTML(self, params):
        return wcomponents.WTemplated.getHTML(self, params)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["User"] = self._aw.getUser()
        vars["Conference"] = self._conf
        vars["ConfReviewingChoice"] = self._conf.getConfPaperReview().getChoice()
        return vars


class WConfMyStuffMySessions(WConfDisplayBodyBase):

    _linkname = 'my_sessions'

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def _getSessionsHTML(self):
        if self._aw.getUser() is None:
            return ""
        #ls=self._conf.getCoordinatedSessions(self._aw.getUser())+self._conf.getManagedSession(self._aw.getUser())
        ls = set(self._conf.getCoordinatedSessions(self._aw.getUser()))
        ls = list(ls | set(self._conf.getManagedSession(self._aw.getUser())))
        if len(ls) <= 0:
            return ""
        res = []
        iconURL = Config.getInstance().getSystemIconURL("conf_edit")
        for s in ls:
            modURL = urlHandlers.UHSessionModification.getURL(s)
            dispURL = urlHandlers.UHSessionDisplay.getURL(s)
            res.append("""
                <tr class="infoTR">
                    <td class="infoTD" width="100%%">%s</td>
                    <td nowrap class="infoTD"><a href=%s>%s</a><span class="horizontalSeparator">|</span><a href=%s>%s</a></td>
                </tr>""" % (self.htmlText(s.getTitle()),
                            quoteattr(str(modURL)),
                            _("Edit"),
                            quoteattr(str(dispURL)),
                            _("View")))
        return """
            <table class="infoTable" cellspacing="0" width="100%%">
                <tr>
                    <td nowrap class="tableHeader"> %s </td>
                    <td nowrap class="tableHeader" style="text-align:right;"> %s </td>
                </tr>
                <tr>
                    <td>%s</td>
                </tr>
            </table>
            """ % (_("Session"),
                   _("Actions"),
                   "".join(res))

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["items"] = self._getSessionsHTML()
        return wvars


class WPConfMyStuffMySessions(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEMyStuff
    menu_entry_name = 'my_conference'

    def _getBody(self,params):
        wc=WConfMyStuffMySessions(self._getAW(),self._conf)
        return wc.getHTML()


class WConfMyStuffMyContributions(WConfDisplayBodyBase):

    _linkname = 'my_contributions'

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def _getContribsHTML(self):
        return WConfMyContributions(self._aw, self._conf).getHTML({})

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["items"] = self._getContribsHTML()
        return wvars


class WPConfMyStuffMyContributions(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEMyStuff
    menu_entry_name = 'my_contributions'

    def _getBody(self,params):
        wc=WConfMyStuffMyContributions(self._getAW(),self._conf)
        return wc.getHTML()


class WConfMyStuffMyTracks(WConfDisplayBodyBase):

    _linkname = 'my_tracks'

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def _getTracksHTML(self):
        if self._aw.getUser() is None or not self._conf.getAbstractMgr().isActive() or not self._conf.hasEnabledSection("cfa"):
            return ""
        lt = self._conf.getCoordinatedTracks(self._aw.getUser())
        if len(lt) <= 0:
            return ""
        res = []
        iconURL = Config.getInstance().getSystemIconURL("conf_edit")
        for t in lt:
            modURL = urlHandlers.UHTrackModifAbstracts.getURL(t)
            res.append("""
                <tr class="infoTR">
                    <td class="infoTD" width="100%%">%s</td>
                    <td nowrap class="infoTD"><a href=%s>%s</a></td>
                </tr>""" % (self.htmlText(t.getTitle()),
                            quoteattr(str(modURL)),
                            _("Edit")))
        return """
            <table class="infoTable" cellspacing="0" width="100%%">
                <tr>
                    <td nowrap class="tableHeader"> %s </td>
                    <td nowrap class="tableHeader" style="text-align:right;"> %s </td>
                </tr>
                <tr>
                    <td>%s</td>
                </tr>
            </table>
            """ % (_("Track"),
                   _("Actions"),
                   "".join(res))

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["items"] = self._getTracksHTML()
        return wvars

class WPConfMyStuffMyTracks(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEMyStuff
    menu_entry_name = 'my_tracks'

    def _getBody(self,params):
        wc=WConfMyStuffMyTracks(self._getAW(),self._conf)
        return wc.getHTML()


class WConfMyStuff(WConfDisplayBodyBase):

    _linkname = 'my_conference'

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        return wvars


class WPMyStuff(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NEMyStuff
    menu_entry_name = 'my_conference'

    def _getBody(self,params):
        wc=WConfMyStuff(self._getAW(),self._conf)
        return wc.getHTML()


class WConfModAbstractBook(wcomponents.WTemplated):

    def __init__(self,conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        boaConfig = self._conf.getBOAConfig()
        vars["sortByList"] = boaConfig.getSortByTypes()
        vars["modURL"] = quoteattr(str(urlHandlers.UHConfModAbstractBook.getURL(self._conf)))
        vars["previewURL"] = quoteattr(str(urlHandlers.UHConfAbstractBook.getURL(self._conf)))
        vars["sortBy"] = boaConfig.getSortBy()
        vars["boaConfig"] = boaConfig
        vars["urlToogleShowIds"] = str(urlHandlers.UHConfModAbstractBookToogleShowIds.getURL(self._conf))
        vars["conf"] = self._conf
        vars["bookOfAbstractsActive"] = self._conf.getAbstractMgr().getCFAStatus()
        vars["bookOfAbstractsMenuActive"] = get_menu_entry_by_name('abstracts_book', self._conf).is_enabled
        vars["correspondingAuthorList"] = boaConfig.getCorrespondingAuthorTypes()
        vars["correspondingAuthor"] = boaConfig.getCorrespondingAuthor()
        return vars


class WPModAbstractBook(WPConferenceModifAbstractBase):

    def _setActiveTab(self):
        self._tabBOA.setActive()

    def _getTabContent(self, params):
        wc = WConfModAbstractBook(self._conf)
        return wc.getHTML()

    def getCSSFiles(self):
        return WPConferenceModifAbstractBase.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def getJSFiles(self):
        return WPConferenceModifAbstractBase.getJSFiles(self) + \
            self._includeJSPackage('Management') + \
            self._asset_env['abstracts_js'].urls()

    def _getHeadContent(self):
        return WPConferenceModifAbstractBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])


class WTimeTableCustomizePDF(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        url = urlHandlers.UHConfTimeTablePDF.getURL(self._conf)
        vars["getPDFURL"] = quoteattr(str(url))
        vars["showDays"] = vars.get("showDays", "all")
        vars["showSessions"] = vars.get("showSessions", "all")

        wc = WConfCommonPDFOptions(self._conf)
        vars["commonPDFOptions"] = wc.getHTML()

        return vars


class WPTimeTableCustomizePDF(WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NETimeTableCustomizePDF
    menu_entry_name = 'timetable'

    def _getBody(self, params):
        wc = WTimeTableCustomizePDF(self._conf)
        return wc.getHTML(params)


class WConfModifPendingQueuesList(wcomponents.WTemplated):

    def __init__(self, url, title, target, list, pType):
        self._postURL = url
        self._title = title
        self._target = target
        self._list = list
        self._pType = pType

    def _cmpByConfName(self, cp1, cp2):
        if cp1 is None and cp2 is not None:
            return -1
        elif cp1 is not None and cp2 is None:
            return 1
        elif cp1 is None and cp2 is None:
            return 0
        return cmp(cp1.getTitle(), cp2.getTitle())

    def _cmpByContribName(self, cp1, cp2):
        if cp1 is None and cp2 is not None:
            return -1
        elif cp1 is not None and cp2 is None:
            return 1
        elif cp1 is None and cp2 is None:
            return 0
        return cmp(cp1.getContribution().getTitle(), cp2.getContribution().getTitle())

    def _cmpBySessionName(self, cp1, cp2):
        if cp1 is None and cp2 is not None:
            return -1
        elif cp1 is not None and cp2 is None:
            return 1
        elif cp1 is None and cp2 is None:
            return 0
        return cmp(cp1.getSession().getTitle(), cp2.getSession().getTitle())

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["postURL"] = self._postURL
        vars["title"] = self._title
        vars["target"] = self._target
        vars["list"] = self._list
        vars["pType"] = self._pType

        return vars


class WConfModifPendingQueues(wcomponents.WTemplated):

    def __init__(self, conf, aw, activeTab="submitters"):
        self._conf = conf
        self._aw = aw
        self._activeTab = activeTab
        self._pendingSubmitters = self._conf.getPendingQueuesMgr().getPendingSubmitters()
        self._pendingManagers = self._conf.getPendingQueuesMgr().getPendingManagers()
        self._pendingCoordinators = self._conf.getPendingQueuesMgr().getPendingCoordinators()

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()
        url = urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab", "conf_submitters")
        self._tabConfSubmitters = self._tabCtrl.newTab("conf_submitters", _("Pending Conference Submitters"), str(url))
        url.addParam("tab", "conf_managers")
        self._tabConfManagers = self._tabCtrl.newTab("conf_managers", _("Pending Conference Managers"), str(url))
        url.addParam("tab", "submitters")
        self._tabSubmitters = self._tabCtrl.newTab("submitters", _("Pending Contribution Submitters"), str(url))
        url.addParam("tab", "managers")
        self._tabManagers = self._tabCtrl.newTab("managers", _("Pending Managers"), str(url))
        url.addParam("tab", "coordinators")
        self._tabCoordinators = self._tabCtrl.newTab("coordinators", _("Pending Coordinators"), str(url))
        self._tabSubmitters.setEnabled(True)
        tab = self._tabCtrl.getTabById(self._activeTab)
        if tab is None:
            tab = self._tabCtrl.getTabById("conf_submitters")
        tab.setActive()

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        self._createTabCtrl()
        list = []
        url = ""
        title = ""

        if self._tabConfSubmitters.isActive():
            # Pending conference submitters
            url = urlHandlers.UHConfModifPendingQueuesActionConfSubm.getURL(self._conf)
            url.addParam("tab","conf_submitters")
            title = _("Pending chairpersons/speakers to become submitters")
            target = _("Conference")
            pType = "ConfSubmitters"

            emails = [x.principal.email for x in self._conf.as_event.acl_entries
                      if x.type == PrincipalType.email and x.has_management_role('submit', explicit=True)]
            chairs = {c.getEmail().strip().lower(): c for c in self._conf.getChairList() if c.getEmail().strip()}
            for email in emails:
                # XXX: this will fail if we ever have a submitter without a corresponding chairperson.
                # i don't think this can happen unless you mess with the DB...
                # if it does simply ignore KeyErrors here.. it's legacy code anyway!
                list.append((email, [chairs[email]]))

        elif self._tabConfManagers.isActive():
            url = url_for('event_mgmt.confModifPendingQueues-actionConfManagers', self._conf)
            title = _("Pending chairpersons to become managers")
            target = _("Conference")
            pType = "ConfManagers"

            emails = [x.principal.email for x in self._conf.as_event.acl_entries
                      if x.type == PrincipalType.email and x.has_management_role()]
            chairs = {c.getEmail().strip().lower(): c for c in self._conf.getChairList() if c.getEmail().strip()}
            for email in emails:
                # XXX: this will fail if we ever have a pending manager without a corresponding chairperson.
                # i don't think this can happen unless you mess with the DB...
                # if it does simply ignore KeyErrors here.. it's legacy code anyway!
                list.append((email, [chairs[email]]))

        elif self._tabSubmitters.isActive():
            # Pending submitters
            keys = self._conf.getPendingQueuesMgr().getPendingSubmittersKeys(True)

            url = urlHandlers.UHConfModifPendingQueuesActionSubm.getURL(self._conf)
            url.addParam("tab", "submitters")
            title = _("Pending authors/speakers to become submitters")
            target = _("Contribution")
            pType = "Submitters"

            for key in keys:
                list.append((key, self._pendingSubmitters[key][:]))

        elif self._tabManagers.isActive():
            # Pending managers
            keys = self._conf.getPendingQueuesMgr().getPendingManagersKeys(True)

            url = urlHandlers.UHConfModifPendingQueuesActionMgr.getURL(self._conf)
            url.addParam("tab", "managers")
            title = _("Pending conveners to become managers")
            target = _("Session")
            pType = "Managers"

            for key in keys:
                list.append((key, self._pendingManagers[key][:]))
                #list.sort(conference.SessionChair._cmpFamilyName)

        elif self._tabCoordinators.isActive():
            # Pending coordinators
            keys = self._conf.getPendingQueuesMgr().getPendingCoordinatorsKeys(True)

            url = urlHandlers.UHConfModifPendingQueuesActionCoord.getURL(self._conf)
            url.addParam("tab", "coordinators")
            title = _("Pending conveners to become coordinators")
            target = _("Session")
            pType = "Coordinators"

            for key in keys:
                list.append((key, self._pendingCoordinators[key][:]))
                list.sort(conference.ConferenceParticipation._cmpFamilyName)

        html = WConfModifPendingQueuesList(str(url), title, target, list, pType).getHTML()
        vars["pendingQueue"] = wcomponents.WTabControl(self._tabCtrl, self._aw).getHTML(html)

        return vars


class WPConfModifPendingQueuesBase(WPConfModifListings):

    sidemenu_option = 'lists'

    def __init__(self, rh, conf, activeTab=""):
        WPConfModifListings.__init__(self, rh, conf)
        self._activeTab = activeTab


class WPConfModifPendingQueues(WPConfModifPendingQueuesBase):

    def _getTabContent(self, params):
        wc = WConfModifPendingQueues(self._conf, self._getAW(), self._activeTab)
        return wc.getHTML()


class WPConfModifPendingQueuesRemoveConfMgrConfirm(WPConfModifPendingQueuesBase):
    def __init__(self, rh, conf, pendingConfMgrs):
        WPConfModifPendingQueuesBase.__init__(self, rh, conf)
        self._pendingConfMgrs = pendingConfMgrs

    def _getTabContent(self, params):
        wc = wcomponents.WConfirmation()
        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingConfMgrs))

        msg = {'challenge': _("Are you sure you want to delete the following users pending to become conference "
                              "managers?"),
               'target': "<ul>{0}</ul>".format(psubs),
               'subtext': _("Please note that they will still remain as user")}

        url = url_for('event_mgmt.confModifPendingQueues-actionConfManagers', self._conf)
        return wc.getHTML(msg, url, {"pendingUsers": self._pendingConfMgrs, "remove": _("remove")})


class WPConfModifPendingQueuesReminderConfMgrConfirm(WPConfModifPendingQueuesBase):
    def __init__(self, rh, conf, pendingConfMgrs):
        WPConfModifPendingQueuesBase.__init__(self, rh, conf)
        self._pendingConfMgrs = pendingConfMgrs

    def _getTabContent(self, params):
        wc = wcomponents.WConfirmation()
        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingConfMgrs))

        msg = {'challenge': _("Are you sure that you want to send these users an email with a reminder to create an "
                              "account in Indico?"),
               'target': "<ul>{0}</ul>".format(psubs)}
        url = url_for('event_mgmt.confModifPendingQueues-actionConfManagers', self._conf)
        return wc.getHTML(msg, url, {"pendingUsers": self._pendingConfMgrs, "reminder": _("reminder")},
                          severity='accept')


class WPConfModifPendingQueuesRemoveConfSubmConfirm(WPConfModifPendingQueuesBase):

    def __init__(self, rh, conf, pendingConfSubms):
        WPConfModifPendingQueuesBase.__init__(self, rh, conf)
        self._pendingConfSubms = pendingConfSubms

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()
        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingConfSubms))

        msg = {'challenge': _("Are you sure you want to delete the following users pending to become submitters?"),
               'target': "<ul>{0}</ul>".format(psubs),
               'subtext': _("Please note that they will still remain as user"),
               }

        url = urlHandlers.UHConfModifPendingQueuesActionConfSubm.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingUsers":self._pendingConfSubms, "remove": _("remove")})

class WPConfModifPendingQueuesReminderConfSubmConfirm(WPConfModifPendingQueuesBase):

    def __init__(self, rh, conf, pendingConfSubms):
        WPConfModifPendingQueuesBase.__init__(self, rh, conf)
        self._pendingConfSubms = pendingConfSubms

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()
        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingConfSubms))

        msg = {'challenge': _("Are you sure that you want to send these users an email with a reminder to create an account in Indico?"),
               'target': "<ul>{0}</ul>".format(psubs)
               }
        url = urlHandlers.UHConfModifPendingQueuesActionConfSubm.getURL(self._conf)
        return wc.getHTML(
            msg,
            url, {
                "pendingUsers": self._pendingConfSubms,
                "reminder": _("reminder")
                },
            severity='accept')

class WPConfModifPendingQueuesRemoveSubmConfirm(WPConfModifPendingQueuesBase):

    def __init__(self, rh, conf, pendingSubms):
        WPConfModifPendingQueuesBase.__init__(self, rh, conf)
        self._pendingSubms = pendingSubms

    def _getTabContent(self, params):
        wc = wcomponents.WConfirmation()
        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingSubms))

        msg = {'challenge': _("Are you sure you want to delete the following participants pending to become submitters?"),
               'target': "<ul>{0}</ul>".format(psubs),
               'subtext': _("Please note that they will still remain as participants"),
               }

        url = urlHandlers.UHConfModifPendingQueuesActionSubm.getURL(self._conf)
        return wc.getHTML(msg, url, {"pendingUsers": self._pendingSubms, "remove": _("remove")})


class WPConfModifPendingQueuesReminderSubmConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingSubms):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingSubms = pendingSubms

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        psubs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingSubms))

        msg = {'challenge': _("Are you sure that you want to send these users an email with a reminder to create an account in Indico?"),
               'target': "<ul>{0}</ul>".format(psubs)
               }

        url = urlHandlers.UHConfModifPendingQueuesActionSubm.getURL(self._conf)
        return wc.getHTML(
            msg,
            url, {
                "pendingUsers": self._pendingSubms,
                "reminder": _("reminder")
                },
            severity='accept')

class WPConfModifPendingQueuesRemoveMgrConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingMgrs):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingMgrs = pendingMgrs

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        pmgrs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingMgrs))

        msg = {'challenge': _("Are you sure you want to delete the following conveners pending to become managers?"),
               'target': "<ul>{0}</ul>".format(pmgrs),
               'subtext': _("Please note that they will still remain as conveners")
               }

        url = urlHandlers.UHConfModifPendingQueuesActionMgr.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingUsers":self._pendingMgrs, "remove": _("remove")})

class WPConfModifPendingQueuesReminderMgrConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingMgrs):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingMgrs = pendingMgrs

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        pmgrs = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingMgrs))

        msg = {'challenge': _("Are you sure that you want to send these users an email with a reminder to create an account in Indico?"),
               'target': "<ul>{0}</ul>".format(pmgrs)
               }

        url = urlHandlers.UHConfModifPendingQueuesActionMgr.getURL(self._conf)
        return wc.getHTML(msg,url,{"pendingUsers":self._pendingMgrs, "reminder": _("reminder")})

class WPConfModifPendingQueuesRemoveCoordConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingCoords):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingCoords = pendingCoords

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        pcoords = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingMgrs))

        msg = {'challenge': _("Are you sure you want to delete the following conveners pending to become coordinators?"),
               'target': "<ul>{0}</ul>".format(pcoords),
               'subtext': _("Please note that they will still remain as conveners")
               }

        url = urlHandlers.UHConfModifPendingQueuesActionCoord.getURL(self._conf)
        return wc.getHTML(msg, url,{
                "pendingUsers": self._pendingCoords,
                "remove": _("remove")
                })

class WPConfModifPendingQueuesReminderCoordConfirm( WPConfModifPendingQueuesBase ):

    def __init__(self,rh, conf, pendingCoords):
        WPConfModifPendingQueuesBase.__init__(self,rh,conf)
        self._pendingCoords = pendingCoords

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        pcoords = ''.join(list("<li>{0}</li>".format(s) for s in self._pendingMgrs))

        msg = {'challenge': _("Are you sure that you want to send these users an email with a reminder to create an account in Indico?"),
               'target': "<ul>{0}</ul>".format(pcoords)
               }

        url = urlHandlers.UHConfModifPendingQueuesActionCoord.getURL(self._conf)
        return wc.getHTML(
            msg, url, {
                "pendingUsers": self._pendingCoords,
                "reminder": _("reminder")
                })


class WConfModifReschedule(wcomponents.WTemplated):

    def __init__(self, targetDay):
        self._targetDay = targetDay

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["targetDay"]=quoteattr(str(self._targetDay))
        return vars

class WPConfModifReschedule(WPConferenceModifBase):

    def __init__(self, rh, conf, targetDay):
        WPConferenceModifBase.__init__(self, rh, conf)
        self._targetDay=targetDay

    def _getPageContent( self, params):
        wc=WConfModifReschedule(self._targetDay)
        p={"postURL":quoteattr(str(urlHandlers.UHConfModifReschedule.getURL(self._conf)))}
        return wc.getHTML(p)


# ============================================================================
# === Badges related =========================================================
# ============================================================================

##------------------------------------------------------------------------------------------------------------
"""
Badge Printing classes
"""
class WConfModifBadgePrinting(wcomponents.WTemplated):
    """ This class corresponds to the screen where badge templates are
        listed and can be created, edited, deleted, and tried.
    """

    def __init__(self, conference, user=None):
        self.__conf = conference
        self._user = user

    def _getBaseTemplateOptions(self):
        dconf = conference.CategoryManager().getDefaultConference()
        templates = dconf.getBadgeTemplateManager().getTemplates()

        options = [{'value': 'blank', 'label': _('Blank Page')}]

        for id, template in templates.iteritems():
            options.append({'value': id, 'label': template.getName()})

        return options

    def getVars(self):
        uh = urlHandlers
        templates = []
        sortedTemplates = self.__conf.getBadgeTemplateManager().getTemplates().items()
        sortedTemplates.sort(lambda x, y: cmp(x[1].getName(), y[1].getName()))

        for templateId, template in sortedTemplates:

            data = {
                'id': templateId,
                'name': template.getName(),
                'urlEdit': str(uh.UHConfModifBadgeDesign.getURL(self.__conf, templateId)),
                'urlDelete': str(uh.UHConfModifBadgePrinting.getURL(self.__conf, deleteTemplateId=templateId)),
                'urlCopy': str(uh.UHConfModifBadgePrinting.getURL(self.__conf, copyTemplateId=templateId))
            }

            templates.append(data)

        wcPDFOptions = WConfModifBadgePDFOptions(self.__conf)
        vars = wcomponents.WTemplated.getVars(self)
        vars['NewTemplateURL'] = str(uh.UHConfModifBadgeDesign.getURL(self.__conf,
                                    self.__conf.getBadgeTemplateManager().getNewTemplateId(),new = True))
        vars['CreatePDFURL'] = str(uh.UHConfModifBadgePrintingPDF.getURL(self.__conf))
        vars['templateList'] = templates
        vars['PDFOptions'] = wcPDFOptions.getHTML()
        vars['baseTemplates'] = self._getBaseTemplateOptions()

        return vars


class WConfModifBadgePDFOptions(wcomponents.WTemplated):

    def __init__(self, conference, showKeepValues=True, showTip=True):
        self.__conf = conference
        self.__showKeepValues = showKeepValues
        self.__showTip = showTip

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        pagesizeNames = PDFSizes().PDFpagesizes.keys()
        pagesizeNames.sort()
        vars['PagesizeNames'] = pagesizeNames
        vars['PDFOptions'] = self.__conf.getBadgeTemplateManager().getPDFOptions()
        vars['ShowKeepValues'] = self.__showKeepValues
        vars['ShowTip'] = self.__showTip

        return vars


class WPBadgeBase(WPConfModifToolsBase):

    def getCSSFiles(self):
        return WPConfModifToolsBase.getCSSFiles(self) + self._asset_env['indico_badges_css'].urls()

    def getJSFiles(self):
        return WPConfModifToolsBase.getJSFiles(self) + self._includeJSPackage('badges_js')


class WPConfModifBadgePrinting(WPBadgeBase):

    def _setActiveTab(self):
        self._tabBadges.setActive()

    def _getTabContent(self, params):
        wc = WConfModifBadgePrinting(self._conf)
        return wc.getHTML()



##------------------------------------------------------------------------------------------------------------
"""
Badge Design classes
"""
class WConfModifBadgeDesign(wcomponents.WTemplated):
    """ This class corresponds to the screen where a template
        is designed inserting, dragging and editing items.
    """

    def __init__(self, conference, templateId, new=False, user=None):
        self.__conf = conference
        self.__templateId = templateId
        self.__new = new
        self._user = user

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["baseURL"] = Config.getInstance().getBaseURL() ##base url of the application, used for the ruler images
        vars["cancelURL"] = urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf, templateId = self.__templateId, cancel = True)
        vars["saveBackgroundURL"] = urlHandlers.UHConfModifBadgeSaveBackground.getURL(self.__conf, self.__templateId)
        vars["loadingIconURL"] = quoteattr(str(Config.getInstance().getSystemIconURL("loading")))
        vars["templateId"] = self.__templateId

        badgeDesignConfiguration = BadgeDesignConfiguration()
        from MaKaC.services.interface.rpc.json import encode as jsonEncode
        vars["translateName"]= jsonEncode(dict([(key, value[0]) for key, value in badgeDesignConfiguration.items_actions.iteritems()]))

        cases = []
        for itemKey in badgeDesignConfiguration.items_actions.keys():
            case = []
            case.append('case "')
            case.append(itemKey)
            case.append('":')
            case.append('\n')
            case.append('items[itemId] = new Item(itemId, "')
            case.append(itemKey)
            case.append('");')
            case.append('\n')
            case.append('newDiv.html(items[itemId].toHTML());')
            case.append('\n')
            case.append('break;')
            cases.append("".join(case))

        vars['switchCases'] = "\n".join(cases)

        optgroups = []
        for optgroupName, options in badgeDesignConfiguration.groups:
            optgroup = []
            optgroup.append('<optgroup label="')
            optgroup.append(optgroupName)
            optgroup.append('">')
            optgroup.append('\n')
            for optionName in options:
                optgroup.append('<option value="%s">'%optionName)
                optgroup.append(badgeDesignConfiguration.items_actions[optionName][0])
                optgroup.append('</option>')
                optgroup.append('\n')
            optgroup.append('</optgroup>')
            optgroups.append("".join(optgroup))

        vars['selectOptions'] = "\n".join(optgroups)
        vars["backgroundPos"] = "Stretch"

        if self.__new:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf, new=True)
            vars["titleMessage"]= _("Creating new badge template")
            vars["editingTemplate"]="false"
            vars["templateData"]="[]"
            vars["hasBackground"]="false"
            vars["backgroundURL"]="false"
            vars["backgroundId"]=-1

        elif self.__templateId is None:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf)
            vars["titleMessage"]= _("No template id given")
            vars["editingTemplate"]="false"
            vars["templateData"]="[]"
            vars["hasBackground"]="false"
            vars["backgroundURL"]="false"
            vars["backgroundId"]=-1

        else:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf)
            vars["titleMessage"]= _("Editing badge template")
            vars["editingTemplate"]="true"

            templateDataString = jsonEncode(self.__conf.getBadgeTemplateManager().getTemplateData(self.__templateId))
            vars["templateData"]= templateDataString

            usedBackgroundId = self.__conf.getBadgeTemplateManager().getTemplateById(self.__templateId).getUsedBackgroundId()
            vars["backgroundId"] = usedBackgroundId
            if usedBackgroundId != -1:
                vars["hasBackground"]="true"
                vars["backgroundURL"]=str(urlHandlers.UHConfModifBadgeGetBackground.getURL(self.__conf, self.__templateId, usedBackgroundId))
            else:
                vars["hasBackground"]="false"
                vars["backgroundURL"]="false"


        return vars


class WPConfModifBadgeDesign(WPBadgeBase):

    def __init__(self, rh, conf, templateId=None, new=False, baseTemplateId="blank"):
        WPBadgeBase.__init__(self, rh, conf)
        self.__templateId = templateId
        self.__new = new
        self.__baseTemplate = baseTemplateId

        if baseTemplateId != 'blank':
            dconf = conference.CategoryManager().getDefaultConference()
            templMan = conf.getBadgeTemplateManager()
            newId = templateId
            dconf.getBadgeTemplateManager().getTemplateById(baseTemplateId).clone(templMan, newId)
            # now, let's pretend nothing happened, and let the code
            # handle the template as if it existed before
            self.__new = False

    def _setActiveTab(self):
        self._tabBadges.setActive()

    def _getTabContent(self, params):
        wc = WConfModifBadgeDesign(self._conf, self.__templateId, self.__new)
        return wc.getHTML()

##------------------------------------------------------------------------------------------------------------
"""
Common PDF Options classes
"""
class WConfCommonPDFOptions( wcomponents.WTemplated ):
    """ This class corresponds to a section of options
        that are common to each PDF in Indico.
    """

    def __init__( self, conference, user=None ):
        self.__conf = conference
        self._user=user

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )

        pagesizeNames = PDFSizes().PDFpagesizes.keys()
        pagesizeNames.sort()
        pagesizeOptions = []
        for pagesizeName in pagesizeNames:
            pagesizeOptions.append('<option ')
            if pagesizeName == 'A4':
                pagesizeOptions.append('selected="selected"')
            pagesizeOptions.append('>')
            pagesizeOptions.append(pagesizeName)
            pagesizeOptions.append('</option>')

        vars['pagesizes'] = "".join(pagesizeOptions)

        fontsizeOptions = []
        for fontsizeName in PDFSizes().PDFfontsizes:
            fontsizeOptions.append('<option ')
            if fontsizeName == 'normal':
                fontsizeOptions.append('selected="selected"')
            fontsizeOptions.append('>')
            fontsizeOptions.append(fontsizeName)
            fontsizeOptions.append('</option>')

        vars['fontsizes'] = "".join(fontsizeOptions)

        return vars


# ============================================================================
# === Posters related ========================================================
# ============================================================================

##------------------------------------------------------------------------------------------------------------
"""
Poster Printing classes
"""
class WConfModifPosterPrinting(wcomponents.WTemplated):
    """ This class corresponds to the screen where poster templates are
        listed and can be created, edited, deleted, and tried.
    """

    def __init__(self, conference, user=None):
        self.__conf = conference
        self._user = user

    def _getFullTemplateListOptions(self):
        templates = {}
        templates['global'] = conference.CategoryManager().getDefaultConference().getPosterTemplateManager().getTemplates()
        templates['local'] = self.__conf.getPosterTemplateManager().getTemplates()
        options = []

        def _iterTemplatesToObjectList(key, templates):
            newList = []

            for id, template in templates.iteritems():
                pKey = ' (' + key + ')'
                # Only if the template is 'global' should it have the word prefixed.
                value = key + str(id) if key == 'global' else str(id)
                newList.append({'value': value,
                                'label': template.getName() + pKey})

            return newList

        for k, v in templates.iteritems():
            options.extend(_iterTemplatesToObjectList(k, v))

        return options

    def _getBaseTemplateListOptions(self):
        templates = conference.CategoryManager().getDefaultConference().getPosterTemplateManager().getTemplates()
        options = [{'value': 'blank', 'label': _('Blank Page')}]

        for id, template in templates.iteritems():
            options.append({'value': id, 'label': template.getName()})

        return options

    def getVars(self):
        uh = urlHandlers
        templates = []
        wcPDFOptions = WConfModifPosterPDFOptions(self.__conf)
        sortedTemplates = self.__conf.getPosterTemplateManager().getTemplates().items()
        sortedTemplates.sort(lambda item1, item2: cmp(item1[1].getName(), item2[1].getName()))

        for templateId, template in sortedTemplates:

            data = {
                'id': templateId,
                'name': template.getName(),
                'urlEdit': str(uh.UHConfModifPosterDesign.getURL(self.__conf, templateId)),
                'urlDelete': str(uh.UHConfModifPosterPrinting.getURL(self.__conf, deleteTemplateId=templateId)),
                'urlCopy': str(uh.UHConfModifPosterPrinting.getURL(self.__conf, copyTemplateId=templateId))
            }

            templates.append(data)

        vars = wcomponents.WTemplated.getVars(self)
        vars["NewTemplateURL"] = str(uh.UHConfModifPosterDesign.getURL(self.__conf, self.__conf.getPosterTemplateManager().getNewTemplateId(),new=True))
        vars["CreatePDFURL"]= str(uh.UHConfModifPosterPrintingPDF.getURL(self.__conf))
        vars["templateList"] = templates
        vars['PDFOptions'] = wcPDFOptions.getHTML()
        vars['baseTemplates'] = self._getBaseTemplateListOptions()
        vars['fullTemplateList'] = self._getFullTemplateListOptions()

        return vars

class WConfModifPosterPDFOptions(wcomponents.WTemplated):

    def __init__(self, conference, user=None):
        self.__conf = conference
        self._user= user

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        pagesizeNames = PDFSizes().PDFpagesizes.keys()
        pagesizeNames.sort()
        pagesizeOptions = []

        for pagesizeName in pagesizeNames:
            pagesizeOptions.append('<option ')

            if pagesizeName == 'A4':
                pagesizeOptions.append('selected="selected"')

            pagesizeOptions.append('>')
            pagesizeOptions.append(pagesizeName)
            pagesizeOptions.append('</option>')

        vars['pagesizes'] = "".join(pagesizeOptions)

        return vars

class WPConfModifPosterPrinting(WPBadgeBase):

    def _setActiveTab(self):
        self._tabPosters.setActive()

    def _getTabContent(self, params):
        wc = WConfModifPosterPrinting(self._conf)
        return wc.getHTML()

##------------------------------------------------------------------------------------------------------------
"""
Poster Design classes
"""
class WConfModifPosterDesign( wcomponents.WTemplated ):
    """ This class corresponds to the screen where a template
        is designed inserting, dragging and editing items.
    """

    def __init__(self, conference, templateId, new=False, user=None):
        self.__conf = conference
        self.__templateId = templateId
        self.__new = new
        self._user = user


    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["baseURL"] = Config.getInstance().getBaseURL()  # base url of the application, used for the ruler images
        vars["cancelURL"] = urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf, templateId = self.__templateId, cancel = True)
        vars["saveBackgroundURL"] = urlHandlers.UHConfModifPosterSaveBackground.getURL(self.__conf, self.__templateId)
        vars["loadingIconURL"] = quoteattr(str(Config.getInstance().getSystemIconURL("loading")))
        vars["templateId"] = self.__templateId

        posterDesignConfiguration = PosterDesignConfiguration()
        from MaKaC.services.interface.rpc.json import encode as jsonEncode
        vars["translateName"]= jsonEncode(dict([(key, value[0]) for key, value in posterDesignConfiguration.items_actions.iteritems()]))

        cases = []
        for itemKey in posterDesignConfiguration.items_actions.keys():
            case = []
            case.append('case "')
            case.append(itemKey)
            case.append('":')
            case.append('\n')
            case.append('items[itemId] = new Item(itemId, "')
            case.append(itemKey)
            case.append('");')
            case.append('\n')
            case.append('newDiv.html(items[itemId].toHTML());')
            case.append('\n')
            case.append('break;')
            cases.append("".join(case))

        vars['switchCases'] = "\n".join(cases)

        optgroups = []
        for optgroupName, options in posterDesignConfiguration.groups:
            optgroup = []
            optgroup.append('<optgroup label="')
            optgroup.append(optgroupName)
            optgroup.append('">')
            optgroup.append('\n')
            for optionName in options:
                optgroup.append('<option value="%s">'%optionName)
                optgroup.append(posterDesignConfiguration.items_actions[optionName][0])
                optgroup.append('</option>')
                optgroup.append('\n')
            optgroup.append('</optgroup>')
            optgroups.append("".join(optgroup))

        vars['selectOptions'] = "\n".join(optgroups)

        if self.__new:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf, new=True)
            vars["titleMessage"]= _("Creating new poster template")
            vars["hasBackground"]="false"
            vars["backgroundURL"]="false"
            vars["backgroundId"]=-1
            vars["backgroundPos"]="Stretch"
            vars["templateData"]="[]"
            vars["editingTemplate"]="false"


        elif self.__templateId is None:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf)
            vars["titleMessage"]= _("No template id given")
            vars["hasBackground"]="false"
            vars["backgroundURL"]="false"
            vars["backgroundId"]=-1
            vars["backgroundPos"]="Stretch"
            vars["templateData"] = "[]"
            vars["editingTemplate"]="false"


        else:
            vars["saveTemplateURL"]=urlHandlers.UHConfModifPosterPrinting.getURL(self.__conf)
            vars["titleMessage"]= _("Editing poster template")
            vars["editingTemplate"]="true"
            templateDataString = jsonEncode(self.__conf.getPosterTemplateManager().getTemplateData(self.__templateId))
            vars["templateData"]= templateDataString

            usedBackgroundId = self.__conf.getPosterTemplateManager().getTemplateById(self.__templateId).getUsedBackgroundId()
            vars["backgroundId"] = usedBackgroundId

            if usedBackgroundId != -1:
                vars["hasBackground"]="true"
                vars["backgroundURL"]=str(urlHandlers.UHConfModifPosterGetBackground.getURL(self.__conf, self.__templateId, usedBackgroundId))
                vars["backgroundPos"]=self.__conf.getPosterTemplateManager().getTemplateById(self.__templateId).getBackgroundPosition(usedBackgroundId)
            else:
                vars["hasBackground"]="false"
                vars["backgroundURL"]="false"
                vars["backgroundPos"]="Stretch"

        return vars


class WPConfModifPosterDesign(WPBadgeBase):

    def __init__(self, rh, conf, templateId=None, new=False, baseTemplateId="blank"):
        WPBadgeBase.__init__(self, rh, conf)
        self.__templateId = templateId
        self.__new = new
        self.__baseTemplate = baseTemplateId

    def _setActiveTab(self):
        self._tabPosters.setActive()

    def _getTabContent(self, params):
        wc = WConfModifPosterDesign(self._conf, self.__templateId, self.__new)
        return wc.getHTML()

    def sortByName(x,y):
        return cmp(x.getFamilyName(),y.getFamilyName())

class WPConfModifPreviewCSS( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, conf, **kwargs):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf, **kwargs)

        self._conf = conf
        self._cssTplsModule = ModuleHolder().getById("cssTpls")

    def _applyDecoration( self, body ):
        """
        """
        return "%s%s%s"%( self._getHeader(), body, self._getFooter() )

    def _getBody( self, params ):
        params['confId'] = self._conf.getId()
        params['conf'] = self._conf

        ###############################
        # injecting ConferenceDisplay #
        ###############################
        p = WPConferenceDisplay( self._rh, self._conf )
        p.event = self._conf.as_event
        p.logo_url = p.event.logo_url if p.event.has_logo else None
        params["bodyConf"] = p._applyConfDisplayDecoration(p._getBody(params))
        ###############################
        ###############################

        wc = WPreviewPage()
        return wc.getHTML(params)

    def _getHeadContent(self):
        path = Config.getInstance().getCssBaseURL()
        try:
            timestamp = os.stat(__file__).st_mtime
        except OSError:
            timestamp = 0
        printCSS = '<link rel="stylesheet" type="text/css" href="{}/Conf_Basic.css?{}">\n'.format(path, timestamp)

        if self._kwargs['css_url']:
            printCSS += '<link rel="stylesheet" type="text/css" href="{url}">'.format(url=self._kwargs['css_url'])
        return printCSS


class WPreviewPage( wcomponents.WTemplated ):
    pass
