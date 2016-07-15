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

from copy import copy

import MaKaC.webinterface.pages.main as main
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.conference as conference
from MaKaC.conference import CategoryManager
from indico.core.config import Config
from MaKaC.i18n import _
from indico.modules.events.util import preload_events
from indico.util.i18n import i18nformat

from MaKaC.webinterface.common.timezones import TimezoneRegistry
from MaKaC.common.timezoneUtils import nowutc
from pytz import timezone
from MaKaC.common.TemplateExec import truncateTitle

from MaKaC.common.fossilize import fossilize

from indico.core.index import Catalog
from indico.modules.categories.views import WPCategory
from indico.modules.events.layout import theme_settings
from indico.web.flask.templating import get_template_module
from indico.web.menu import render_sidemenu


def format_location(item):
    if item.inherit_location or not item.has_location_info:
        return u''
    tpl = get_template_module('events/display/indico/_common.html')
    return tpl.render_location(item)


class WPCategoryBase (main.WPMainBase):
    def __init__(self, rh, categ, **kwargs):
        new_categ = categ.as_new if categ else None
        main.WPMainBase.__init__(self, rh, _protected_object=new_categ, _current_category=new_categ, **kwargs)
        self._target = categ
        title = "Indico"
        if self._target:
            title = "Indico [%s]"%(self._target.getName() )
        self._setTitle(title)
        self._conf = None

    def getCSSFiles(self):
        return main.WPMainBase.getCSSFiles(self) + self._asset_env['category_sass'].urls()


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
        now = nowutc().astimezone(timezone(tz))
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
        vars["nocategs"] = False
        if not CategoryManager().getRoot().hasSubcategories():
            vars["nocategs"] = True
            rootcateg = CategoryManager().getRoot()
            if rootcateg.isProtected():
                vars["protection"] = "private"
            vars["categ"] = {"id":rootcateg.getId(), "title":rootcateg.getTitle()}
        #vars["event_type"] = ""
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

#---------------------------------------------------------------------------


class WPConferenceCreationMainData(WPCategory):
    def __init__(self, *args, **kwargs):
        WPCategory.__init__(self, *args, **kwargs)
        self._protected_object = None  # don't show protection icon in the top bar

    def _getWComponent(self):
        return WConferenceCreation(self.category, self._rh._event_type.name, self._rh)

    def _getBody(self, params):
        return self._getWComponent().getHTML(params)


class WPCategoryModifBase( WPCategoryBase ):

    _userData = ['favorite-user-ids']

    def getJSFiles(self):
        return (WPCategoryBase.getJSFiles(self) +
                main.WPMainBase.getJSFiles(self) +
                self._includeJSPackage('Management') +
                self._asset_env['modules_event_management_js'].urls())

    def getCSSFiles(self):
        return main.WPMainBase.getCSSFiles(self) + self._asset_env['event_management_sass'].urls()

    def _getHeader(self):
        wc = wcomponents.WHeader(self._getAW(), currentCategory=self._current_category,
                                 prot_obj=self._protected_object)
        return wc.getHTML({
            'subArea': self._getSiteArea(),
            'loginURL': self._escapeChars(str(self.getLoginURL())),
            'logoutURL': self._escapeChars(str(self.getLogoutURL()))
        })

    def _getNavigationDrawer(self):
        pars = {"target": self._target , "isModif" : True}
        return wcomponents.WNavigationDrawer( pars, bgColor = "white" )

    def _createTabCtrl( self ):
        pass

    def _setActiveTab( self ):
        pass

    def _getBody(self, params):
        self._createTabCtrl()
        self._setActiveTab()

        frame = WCategoryModifFrame()

        return frame.getHTML({
            "category": self._target,
            "body": self._getPageContent(params),
            "sideMenu": render_sidemenu('category-management-sidemenu-old', active_item=self.sidemenu_option,
                                        category=self._target)
        })

    def _getTabContent( self, params ):
        return "nothing"

    def _getPageContent( self, params ):
        return "nothing"

    def _getSiteArea(self):
        return "ModificationArea"


class WCategoryModifFrame(wcomponents.WTemplated):

    def __init__( self ):
        pass

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        return vars

class WPCategModifMain( WPCategoryModifBase ):
    sidemenu_option = 'general'


class WCategModifMain(wcomponents.WTemplated):

    def __init__( self, category ):
        self._categ = category

    def __getSubCategoryItems( self, sl, modifURLGen ):
        temp = []
        for categ in sl:
            id = categ.getId()
            selbox = """<select name="newpos%s" onChange="this.form.oldpos.value='%s';this.form.submit();">""" % (sl.index(categ),sl.index(categ))
            for i in range (1,len(sl)+1):
                if i==sl.index(categ)+1:
                    selbox += "<option selected value='%s'>%s" % (i-1,i)
                else:
                    selbox += "<option value='%s'>%s" % (i-1,i)
            selbox += """
                </select>"""
            temp.append("""
                <tr>
                    <td width="3%%">
                        <input type="checkbox" name="selectedCateg" value="%s">
                    </td>
                    <td>%s</td>
                    <td style="padding-left:10px;">
                        <a href="%s">%s</a>
                    </td>
                </tr>"""%(id, selbox,modifURLGen( categ ), categ.getName().strip() or "[no title]"))
        html = i18nformat("""
                <input type="hidden" name="oldpos">
                <table align="left" width="100%%">
                <tr>
                    <td width="3%%" nowrap><img src="%s" border="0" alt="Select all" onclick="javascript:selectAll(document.contentForm.selectedCateg)"><img src="%s" border="0" alt="Deselect all" onclick="javascript:deselectAll(document.contentForm.selectedCateg)"></td>
                    <td></td>
                    <td class="titleCellFormat" width="100%%" style="padding-left:10px;"> _("Category name")</td>
                </tr>
                %s
                </table>""")%(Config.getInstance().getSystemIconURL("checkAll"), Config.getInstance().getSystemIconURL("uncheckAll"), "".join( temp ))
        return html

    def __getConferenceItems(self, cl, modifURLGen):
        temp = []
        cl = list(cl)
        preload_events(cl)
        for conf in cl:
            temp.append("""
                <tr>
                    <td width="3%%">
                        <input type="checkbox" name="selectedConf" value="%s">
                    </td>
                    <td align="center" width="17%%">%s</td>
                    <td align="center" width="17%%">%s</td>
                    <td width="100%%"><a href="%s">%s</a></td>
                </tr>"""%(conf.getId(), conf.getAdjustedStartDate().date(), conf.getAdjustedEndDate().date(),modifURLGen(conf), conf.getTitle()))
        html = i18nformat("""<table align="left" width="100%%">
                <tr>
                    <td width="3%%" nowrap><img src="%s" border="0" alt="Select all" onclick="javascript:selectAll(document.contentForm.selectedConf)"><img src="%s" border="0" alt="Deselect all" onclick="javascript:deselectAll(document.contentForm.selectedConf)"></td>
                    <td align="center" width="17%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF; border-bottom: 1px solid #FFFFFF;"> _("Start date")</td>
                    <td align="center" width="17%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF; border-bottom: 1px solid #FFFFFF;"> _("End date")</td>
                    <td width="100%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF; border-bottom: 1px solid #FFFFFF;"> _("Conference title")</td>
                </tr>
        %s</table>""")%(Config.getInstance().getSystemIconURL("checkAll"), Config.getInstance().getSystemIconURL("uncheckAll"), "".join( temp ))
        return html

    def getVars( self ):

        index = Catalog.getIdx('categ_conf_sd').getCategory(self._categ.getId())
        vars = wcomponents.WTemplated.getVars( self )
        vars["locator"] = self._categ.getLocator().getWebForm()
        vars["name"] = self._categ.getName()

        vars["description"] = self._categ.getDescription()

        if self._categ.getIcon() is not None:
            vars["icon"] = """<img src="%s" width="16" height="16" alt="category">"""%urlHandlers.UHCategoryIcon.getURL( self._categ)
        else:
            vars["icon"] = "None"
        vars["dataModifButton"] = ""
        if not self._categ.isRoot():
            vars["dataModifButton"] = i18nformat("""<input type="submit" class="btn" value="_("modify")">""")
        vars["removeItemsURL"] = vars["actionSubCategsURL"]
        if not self._categ.getSubCategoryList():
            vars['containsEvents'] = True
            vars["removeItemsURL"] = vars["actionConferencesURL"]
            vars["items"] = self.__getConferenceItems(index.itervalues(), vars["confModifyURLGen"])
        else:
            vars['containsEvents'] = False
            vars["items"] = self.__getSubCategoryItems( self._categ.getSubCategoryList(), vars["categModifyURLGen"] )
        vars["defaultMeetingStyle"] = theme_settings.themes[theme_settings.defaults['meeting']]['title']
        vars["defaultLectureStyle"] = theme_settings.themes[theme_settings.defaults['simple_event']]['title']

##        vars["defaultVisibility"] = self._categ.getVisibility()
        vars["defaultTimezone"] = self._categ.getTimezone()
        visibility = self._categ.getVisibility()
        categpath = self._categ.getCategoryPath()
        categpath.reverse()
        if visibility > len(categpath):
            vars["defaultVisibility"] = _("Everywhere")
        elif visibility == 0:
            vars["defaultVisibility"] = _("Nowhere")
        else:
            categId = categpath[visibility-1]
            cat = conference.CategoryManager().getById(categId)
            vars["defaultVisibility"] = cat.getName()

        return vars


class WPCategoryModification( WPCategModifMain ):

    def _getPageContent( self, params ):
        wc = WCategModifMain( self._target )
        pars = { \
"dataModificationURL": urlHandlers.UHCategoryDataModif.getURL( self._target ), \
"addSubCategoryURL": urlHandlers.UHCategoryCreation.getURL(self._target),
"addConferenceURL": urlHandlers.UHConferenceCreation.getURL( self._target ), \
"confModifyURLGen": urlHandlers.UHConferenceModification.getURL, \
"categModifyURLGen": urlHandlers.UHCategoryModification.getURL, \
"actionSubCategsURL": urlHandlers.UHCategoryActionSubCategs.getURL(self._target),
"actionConferencesURL": urlHandlers.UHCategoryActionConferences.getURL(self._target)}
        return wc.getHTML( pars )


class WCategoryDataModification(wcomponents.WTemplated):

    def __init__( self, category ):
        self._categ = category

    def _getVisibilityHTML(self):
        visibility = self._categ.getVisibility()
        topcat = self._categ
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
                vis.append("""<option value="%s" %s>%s</option>""" % (level, selected, truncateTitle(topcat.getName(), 70)))
            topcat = topcat.getOwner()
        selected = ""
        if visibility > level:
            selected = "selected"
        vis.append( i18nformat("""<option value="999" %s> _("Everywhere")</option>""") % selected)
        vis.reverse()
        return "".join(vis)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["name"] = self._categ.getName()
        vars["description"] = self._categ.getDescription()
        vars["visibility"] = self._getVisibilityHTML()
        vars["timezoneOptions"] = TimezoneRegistry.getShortSelectItemsHTML(self._categ.getTimezone())
        if self._categ.getIcon() is not None:
            vars["icon"] = """<img src="%s" width="16" height="16" alt="category">"""%urlHandlers.UHCategoryIcon.getURL( self._categ)
        else:
            vars["icon"] = "None"
        for evt_type in ("simple_event", "meeting"):
            themes = theme_settings.get_themes_for(evt_type)
            styleoptions = ""
            for theme_id, theme_data in themes.viewitems():
                defStyle = self._categ.getDefaultStyle(evt_type)
                if defStyle == "":
                    defStyle = theme_settings.defaults[evt_type]
                if theme_id == defStyle:
                    selected = "selected"
                else:
                    selected = ""
                styleoptions += "<option value=\"%s\" %s>%s</option>" % (theme_id, selected,
                                                                         theme_data['title'])
            vars["%sStyleOptions" % evt_type] = styleoptions

        return vars


class WPCategoryDataModification(WPCategModifMain):

    def _getPageContent(self, params):
        wc = WCategoryDataModification(self._target)
        pars = {"postURL": urlHandlers.UHCategoryPerformModification.getURL(self._target)}
        return wc.getHTML(pars)


class WCategoryCreation(wcomponents.WTemplated):

    def __init__(self, target):
        self.__target = target

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["locator"] = self.__target.getLocator().getWebForm()

        for evt_type in ("simple_event", "meeting"):
            styleoptions = ""

            for theme_id, theme_data in theme_settings.get_themes_for(evt_type).viewitems():
                defStyle = self.__target.getDefaultStyle(evt_type)

                if defStyle == "":
                    defStyle = theme_settings.defaults[evt_type]
                if theme_id == defStyle:
                    selected = "selected"
                else:
                    selected = ""

                styleoptions += "<option value=\"%s\" %s>%s</option>" % (theme_id, selected, theme_data['title'])
            vars[evt_type + "StyleOptions"] = styleoptions

        default_tz = Config.getInstance().getDefaultTimezone()
        vars["timezoneOptions"] = TimezoneRegistry.getShortSelectItemsHTML(default_tz)
        vars["categTitle"] = self.__target.getTitle()
        if self.__target.isProtected():
            vars["categProtection"] = "private"
        else:
            vars["categProtection"] = "public"
        vars["numConferences"] = len(self.__target.conferences)

        return vars


class WPCategoryCreation(WPCategModifMain):

    def _getPageContent(self, params):
        wc = WCategoryCreation(self._target)
        pars = {"categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
                "postURL": urlHandlers.UHCategoryPerformCreation.getURL(self._target)}
        return wc.getHTML(pars)


class WCategoryDeletion(object):

    def __init__(self, categoryList):
        self._categList = categoryList

    def getHTML(self, actionURL):
        categories = []

        for categ in self._categList:
            categories.append("""<li><i>%s</i></li>""" % categ.getName())

        msg = {'challenge': _("Are you sure that you want to delete the following categories?"),
               'target': "".join(categories),
               'important': True,
               'subtext': _("Note that all the existing sub-categories below will also be deleted")
               }

        wc = wcomponents.WConfirmation()
        categIdList = []

        for categ in self._categList:
            categIdList.append(categ.getId())

        return wc.getHTML(msg, actionURL, {"selectedCateg": categIdList},
                          confirmButtonCaption=_("Yes"),
                          cancelButtonCaption=_("No"),
                          severity='danger')


class WConferenceDeletion(wcomponents.WTemplated):
    pass


class WPSubCategoryDeletion(WPCategModifMain):

    def _getPageContent(self, params):
        selCategs = params["subCategs"]
        wc = WCategoryDeletion(selCategs)
        return wc.getHTML(urlHandlers.UHCategoryActionSubCategs.getURL(self._target))


class WPConferenceDeletion(WPCategModifMain):

    def _getPageContent(self, params):
        wc = WConferenceDeletion()
        return wc.getHTML({'eventList': params["events"],
                           'postURL': urlHandlers.UHCategoryActionConferences.getURL(self._target),
                           'cancelButtonCaption': _("No"),
                           'confirmButtonCaption': _("Yes")})


class WItemReallocation(wcomponents.WTemplated):

    def __init__(self, itemList):
        self._itemList = itemList

    def getHTML(self, selectTree, params):
        self._sTree = selectTree
        return wcomponents.WTemplated.getHTML(self, params)

    def _getItemDescription(self, item):
        return ""

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        l = []
        for item in self._itemList:
            l.append("<li><b>%s</b>"%self._getItemDescription(item))
        vars["selectedItems"] = "".join(l)
        vars["categTree"] = self._sTree.getHTML()
        return vars


class WCategoryReallocation( WItemReallocation ):

    def _getItemDescription( self, item ):
        return item.getName()


class WConferenceReallocation( WItemReallocation ):

    def _getItemDescription( self, item ):
        return item.getTitle()


class CategSelectTree:

    def __init__( self, aw, excludedCat, expandedCat, \
                        selectURLGen, expandURLGen, movingConference = 0 ):
        self._aw = aw
        self._excludedCategs = excludedCat
        self._expandedCategs = expandedCat
        self._selectURLGen = selectURLGen
        self._expandURLGen = expandURLGen
        self._movingConference = movingConference

    def _getItem( self, categ, level=0 ):
        if not categ.canAccess( self._aw ):
            return ""
        html = ""
        for i in range(level):
            html = "%s&nbsp;&nbsp;&nbsp;"%html
        cfg = Config.getInstance()
        if categ in self._excludedCategs:
            return """%s<img src="%s" border="0" alt=""> %s"""%(html, cfg.getSystemIconURL("collapsd.png"), categ.getName())
        if (self._movingConference) and categ.getSubCategoryList():
            title = """%s"""%categ.getName()
        else:
            title = """<a href="%s">%s</a>"""%(self._selectURLGen( categ ), \
                                                categ.getName())
        if categ in self._expandedCategs:
            ex = copy( self._expandedCategs )
            ex.remove( categ )
            html = """%s<a href="%s"><img src="%s" border="0" alt=""></a> %s"""%(html, self._expandURLGen( ex ), cfg.getSystemIconURL("exploded.png"), title)
            for subcat in categ.getSubCategoryList():
                html = "%s<br>%s"%(html, self._getItem(subcat, level+1) )
        else:
            html = """%s<a href="%s"><img src="%s" border="0" alt=""></a> %s"""%(html, self._expandURLGen( self._expandedCategs+[categ] ), cfg.getSystemIconURL("collapsd.png"), title)
        return html

    def getHTML( self ):
        cm = conference.CategoryManager()
        return self._getItem( cm.getRoot() )


class WPCategoryReallocation( WPCategModifMain ):

    def _getReAllocateCategsURL( self, destination ):
        url = urlHandlers.UHCategoryActionSubCategs.getURL( destination )
        selectedCategs = []
        for c in self._categs:
            selectedCategs.append( c.getId() )
        url.addParam( "selectedCateg", selectedCategs )
        url.addParam( "confirm", "" )
        url.addParam( "reallocate", "" )
        return url

    def _getCategExpandCategURL( self, expandedCategs ):
        selected = []
        for c in self._categs:
            selected.append( c.getId() )
        expanded = []
        for c in expandedCategs:
            expanded.append( c.getId() )
        url = urlHandlers.UHCategoryActionSubCategs.getURL( self._target )
        url.addParam( "selectedCateg", selected )
        url.addParam( "ex", expanded )
        url.addParam( "reallocate", "" )
        return url

    def _getExpandedCategs( self, params ):
        exIdList = params.get("ex", [])
        if not isinstance( exIdList, list ):
            exIdList = [ exIdList ]
        expanded = []
        cm = conference.CategoryManager()
        for categId in exIdList:
            expanded.append( cm.getById( categId ) )
        return expanded

    def _getPageContent( self, params ):
        self._categs = params["subCategs"]
        expanded = self._getExpandedCategs( params )
        pars = {"cancelURL": urlHandlers.UHCategoryModification.getURL( self._target ) }
        tree = CategSelectTree( self._getAW(), self._categs, \
                                            expanded, \
                                            self._getReAllocateCategsURL, \
                                            self._getCategExpandCategURL )
        wc = WCategoryReallocation( self._categs )
        return wc.getHTML( tree, pars )


class WPConferenceReallocation( WPCategModifMain ):

    def _getReAllocateConfsURL( self, destination ):
        url = urlHandlers.UHCategoryActionConferences.getURL( destination )
        url.addParam( "srcCategId", self._target.getId() )
        url.addParam( "selectedConf", self._confIds)
        url.addParam( "confirm", "" )
        url.addParam( "reallocate", "" )
        return url

    def _getExpandCategURL( self, expandedCategs ):
        expanded = []
        for c in expandedCategs:
            expanded.append( c.getId() )
        url = urlHandlers.UHCategoryActionConferences.getURL( self._target )
        url.addParam( "ex", expanded )
        url.addParam( "reallocate", "" )
        url.addParam( "selectedConf", self._confIds )
        return url

    def _getExpandedCategs( self, params ):
        exIdList = params.get("ex", [])
        if not isinstance( exIdList, list ):
            exIdList = [ exIdList ]
        expanded = []
        cm = conference.CategoryManager()
        for categId in exIdList:
            expanded.append( cm.getById( categId ) )
        return expanded

    def _getPageContent( self, params ):
        self._confs = params["confs"]
        self._confIds = []
        for c in self._confs:
            self._confIds.append( c.getId() )
        expanded = self._getExpandedCategs( params )
        pars = {"cancelURL": urlHandlers.UHCategoryModification.getURL( self._target ) }
        tree = CategSelectTree( self._getAW(), [], \
                                            expanded, \
                                            self._getReAllocateConfsURL, \
                                            self._getExpandCategURL, 1 )
        wc = WConferenceReallocation( self._confs )
        return wc.getHTML( tree, pars )


class WCategModifAC(wcomponents.WTemplated):

    def __init__( self, category ):
        self._categ = category

    def _getControlUserList(self):
        result = fossilize(self._categ.getManagerList())
        # get pending users
        for email in self._categ.getAccessController().getModificationEmail():
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["modifyControlFrame"] = wcomponents.WModificationControlFrame().getHTML(self._categ)
        if self._categ.isRoot() :
            type = 'Home'
        else :
            type = 'Category'

        vars["accessControlFrame"] = wcomponents.WAccessControlFrame().getHTML(\
                                                    self._categ,\
                                                    vars["setVisibilityURL"],\
                                                    type)
        if not self._categ.isProtected():
            df =  wcomponents.WDomainControlFrame( self._categ )
            vars["accessControlFrame"] += "<br>%s"%df.getHTML()
        vars["confCreationControlFrame"] = ""
        vars["categoryId"] = self._categ.getId()
        if not self._categ.getSubCategoryList():
            frame = wcomponents.WConfCreationControlFrame( self._categ )
            p = { "setStatusURL": vars["setConferenceCreationControlURL"] }
            vars["confCreationControlFrame"] = frame.getHTML(p)
        vars["managers"] = self._getControlUserList()
        return vars

class WPCategModifAC( WPCategoryModifBase ):
    sidemenu_option = 'protection'

    def _getPageContent(self, params):
        wc = WCategModifAC(self._target)
        pars = {
            "setVisibilityURL": urlHandlers.UHCategorySetVisibility.getURL(self._target),
            "setConferenceCreationControlURL": urlHandlers.UHCategorySetConfCreationControl.getURL(self._target)
        }
        return wc.getHTML(pars)

#---------------------------------------------------------------------------------

class WCategModifTools(wcomponents.WTemplated):

    def __init__( self, category ):
        self._categ = category

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["deleteButton"] = ""
        vars["id"] = self._categ.getId()
        if not self._categ.isRoot():
            vars["deleteButton"] = i18nformat("""<input type="submit" class="btn" value="_("delete this category")">""")
        return vars


class WPCategModifTools( WPCategoryModifBase ):
    sidemenu_option = 'tools'

    def _getPageContent( self, params ):
        wc = WCategModifTools( self._target )
        pars = { \
"deleteCategoryURL": urlHandlers.UHCategoryDeletion.getURL(self._target) }
        return wc.getHTML( pars )


class WPCategoryDeletion( WPCategModifTools ):

    def _getPageContent( self, params ):
        wc = WCategoryDeletion( [self._target] )
        return wc.getHTML( urlHandlers.UHCategoryDeletion.getURL( self._target ) )
