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

from pytz import timezone

from indico.core.config import Config
from indico.modules.categories import Category
from indico.modules.categories.views import WPCategory
from indico.modules.events.layout import theme_settings
from indico.util.date_time import now_utc
from indico.util.i18n import _

from MaKaC.webinterface import wcomponents
from MaKaC.webinterface.common.timezones import TimezoneRegistry


class WConferenceCreation( wcomponents.WTemplated ):

    def __init__( self, targetCateg, type="conference", rh = None ):
        self._categ = targetCateg
        self._type = type
        self._rh = rh

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        navigator = ""
        vars["title"] = vars.get("title","")
        vars["description"] = vars.get("description","")
        vars["keywords"] = vars.get("keywords","")
        vars["contactInfo"] = vars.get("contactInfo","")
        av=self._rh._getUser()
        tz=av.getTimezone()
        now = now_utc().astimezone(timezone(tz))
        vars["sDay"] = vars.get("sDay",now.day)
        vars["sMonth"] = vars.get("sMonth",now.month)
        vars["sYear"] = vars.get("sYear",now.year)
        vars["sHour"] = vars.get("sHour","8")
        vars["sMinute"] = vars.get("sMinute","00")
        vars["eDay"] = vars.get("eDay",now.day)
        vars["eMonth"] = vars.get("eMonth",now.month)
        vars["eYear"] = vars.get("eYear",now.year)
        vars["eHour"] = vars.get("eHour","18")
        vars["eMinute"] = vars.get("eMinute","00")

        vars["sDay_"] = {}
        vars["sMonth_"] = {}
        vars["sYear_"] = {}
        vars["sHour_"] = {}
        vars["sMinute_"] = {}
        vars["dur_"] = {}

        for i in range(0,10):
            vars["sDay_"][i] = vars.get("sDay_%s"%i,now.day)
            vars["sMonth_"][i] = vars.get("sMonth_%s"%i,now.month)
            vars["sYear_"][i] = vars.get("sYear_%s"%i,now.year)
            vars["sHour_"][i] = vars.get("sHour_%s"%i,"8")
            vars["sMinute_"][i] = vars.get("sMinute_%s"%i,"00")
            vars["dur_"][i] = vars.get("dur_%s"%i,"60")
        vars["nbDates"] = vars.get("nbDates",1)
        seltitle = Config.getInstance().getDefaultTimezone()
        if self._categ:
            seltitle = self._categ.timezone
        vars["timezoneOptions"] = TimezoneRegistry.getShortSelectItemsHTML(seltitle)
        vars["locationName"] = vars.get("locationName","")
        vars["locationAddress"] = vars.get("locationAddress","")
        vars["roomName"] = vars.get("locationRoom","")
        vars["protection"] = "public"
        vars["categ"] = {"id":"", "title":_("-- please, choose a category --")}
        if self._categ and not self._categ.children:
            if self._categ.is_protected:
                vars["protection"] = "private"
            vars["categ"] = {"id": str(self._categ.id), "title": self._categ.title}
        elif not self._categ:
            root = Category.get_root()
            if not root.deep_children_count:
                if root.is_protected:
                    vars["protection"] = "private"
                vars["categ"] = {"id": root.id, "title": root.title}
        vars["navigator"] = navigator
        vars["orgText"] = ""
        if vars.get("orgText","") != "":
            vars["orgText"] = vars.get("orgText","")
        elif self._rh._getUser():
            vars["orgText"] = self._rh._getUser().getStraightFullName()
        vars["chairText"] = vars.get("chairText","")
        vars["supportEmail"] = vars.get("supportEmail","")
        styles = theme_settings.get_themes_for(self._type)
        styleoptions = ""
        defStyle = ""
        if self._categ:
            defStyle = self._categ.default_event_themes.get(self._type, '')
        if defStyle == "":
            defStyle = theme_settings.defaults[self._type]
        for theme_id, theme_data in styles.viewitems():
            if theme_id == defStyle:
                selected = "selected"
            else:
                selected = ""
            styleoptions += "<option value=\"%s\" %s>%s</option>" % (theme_id, selected, theme_data['title'])
        vars["styleOptions"] = styleoptions

        vars["chairpersonDefined"] = vars.get("chairpersonDefined", [])

        vars["useRoomBookingModule"] = Config.getInstance().getIsRoomBookingActive()

        return vars


class WPConferenceCreationMainData(WPCategory):
    def __init__(self, *args, **kwargs):
        WPCategory.__init__(self, *args, **kwargs)
        self._protected_object = None  # don't show protection icon in the top bar

    def _getWComponent(self):
        return WConferenceCreation(self.category, self._rh._event_type.name, self._rh)

    def _getBody(self, params):
        return self._getWComponent().getHTML(params)
