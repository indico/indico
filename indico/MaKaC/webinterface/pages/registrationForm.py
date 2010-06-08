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

import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.navigation as navigation
import string
from MaKaC import registration
from MaKaC.webinterface import wcomponents
from xml.sax.saxutils import quoteattr
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.webinterface.common.currency import CurrencyRegistry
from MaKaC.common import Configuration
from datetime import timedelta
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.webinterface.common.countries import CountryHolder
from MaKaC.webinterface.pages.base import WPBase
from MaKaC.common import Config
from MaKaC.i18n import _

####
# ----------------- MANAGEMENT AREA ---------------------------
class WPConfModifRegFormBase( conferences.WPConferenceModifBase ):

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabRegFormSetup = self._tabCtrl.newTab( "regformsetup", _("Setup"), \
                urlHandlers.UHConfModifRegForm.getURL( self._conf ) )
        self._tabRegistrants = self._tabCtrl.newTab( "registrants", _("Registrants"), \
                urlHandlers.UHConfModifRegistrantList.getURL( self._conf ) )
        self._tabRegistrationPreview = self._tabCtrl.newTab( "preview", _("Preview"), \
                urlHandlers.UHConfModifRegistrationPreview.getURL( self._conf ) )
        self._tabEPay = self._tabCtrl.newTab( "epay", _("e-payment"), \
                urlHandlers.UHConfModifEPayment.getURL( self._conf ) )

        self._setActiveTab()

        if not self._conf.hasEnabledSection("regForm"):
            self._tabRegFormSetup.disable()
            self._tabRegistrants.disable()
            self._tabEPay.disable()
            self._tabRegistrationPreview.disable()

    def _getPageContent(self, params):
        self._createTabCtrl()
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

    def _getTabContent(self, params):
        return "nothing"

    def _setActiveSideMenuItem(self):
        self._regFormMenuItem.setActive()

    def _setActiveTab(self):
        pass

class WPConfModifRegFormPreview( WPConfModifRegFormBase ):
    def _setActiveTab( self ):
        self._tabRegistrationPreview.setActive()

    def _getTabContent( self, params ):
        wc = WConfRegistrationFormPreview(self._conf, self._rh._getUser())
        return wc.getHTML()

class WPConfModifRegForm( WPConfModifRegFormBase ):
    def _setActiveTab( self ):
        self._tabRegFormSetup.setActive()

    def _getTabContent( self, params ):
        wc = WConfModifRegForm(self._conf)
        return wc.getHTML()

class WConfModifRegForm( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def _getURL(self, sect):
        if sect.getId()=="sessions":
            return urlHandlers.UHConfModifRegFormSessions.getURL(self._conf)
        if sect.getId()=="accommodation":
            return urlHandlers.UHConfModifRegFormAccommodation.getURL(self._conf)
        if sect.getId()=="reasonParticipation":
            return urlHandlers.UHConfModifRegFormReasonParticipation.getURL(self._conf)
        if sect.getId()=="furtherInformation":
            return urlHandlers.UHConfModifRegFormFurtherInformation.getURL(self._conf)
        if sect.getId()=="socialEvents":
            return urlHandlers.UHConfModifRegFormSocialEvent.getURL(self._conf)
        return urlHandlers.UHConfModifRegFormGeneralSection.getURL(sect)

    def _getPersonalFieldsHTML(self):
        regForm=self._conf.getRegistrationForm()
        html=[]
        enabledBulb = Configuration.Config.getInstance().getSystemIconURL( "enabledSection" )
        notEnabledBulb = Configuration.Config.getInstance().getSystemIconURL( "disabledSection" )
        enabledText = "Click to disable"
        disabledText = "Click to enable"
        keys = regForm.getPersonalData().getSortedKeys()
        for key in keys:
            pdfield = regForm.getPersonalData().getDataItem(key)
            urlStatus = urlHandlers.UHConfModifRegFormEnablePersonalField.getURL(self._conf)
            urlStatus.addParam("personalfield", pdfield.getId())
            img = enabledBulb
            text = enabledText
            if not pdfield.isEnabled():
                img = notEnabledBulb
                text = disabledText
            urlSwitch = urlHandlers.UHConfModifRegFormSwitchPersonalField.getURL(self._conf)
            urlSwitch.addParam("personalfield", pdfield.getId())
            switch = "optional"
            if pdfield.isMandatory():
                switch = "mandatory"
            if pdfield.getId() not in ["email","firstName","surname"]:
                html.append("""
                        <tr>
                        <td><a href=%s><img src="%s" alt="%s" class="imglink"></a></td><td>&nbsp;%s</td><td>&nbsp;<a href="%s">%s</a></td>
                        </tr>
                        """%(quoteattr(str(urlStatus)), img, text, pdfield.getName(), urlSwitch, switch) )
            else:
                html.append("""
                        <tr>
                        <td></td><td>&nbsp;%s</td><td>&nbsp;%s</td>
                        </tr>
                        """%(pdfield.getName(), switch) )

        html.insert(0, """<table>""")
        html.append("</table>")
        return "".join(html)


    def _getSectionsHTML(self):
        regForm=self._conf.getRegistrationForm()
        html=[]
        enabledBulb = Configuration.Config.getInstance().getSystemIconURL( "enabledSection" )
        notEnabledBulb = Configuration.Config.getInstance().getSystemIconURL( "disabledSection" )
        enabledText =  _("Click to disable")
        disabledText =  _("Click to enable")
        for gs in regForm.getSortedForms():
            urlStatus = urlHandlers.UHConfModifRegFormEnableSection.getURL(self._conf)
            urlStatus.addParam("section", gs.getId())
            urlModif=self._getURL(gs)
            img = enabledBulb
            text = enabledText
            if not gs.isEnabled():
                img = notEnabledBulb
                text = disabledText
            checkbox="&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            if isinstance(gs, registration.GeneralSectionForm):
                checkbox="""
                        <input type="checkbox" name="sectionsIds" value="%s">&nbsp;
                        """%gs.getId()
            selbox = """<select name="newpos%s" onChange="this.form.oldpos.value='%s';this.form.submit();">""" % (regForm.getSortedForms().index(gs),regForm.getSortedForms().index(gs))
            for i in range(1,len(regForm.getSortedForms())+1):
                if i== regForm.getSortedForms().index(gs)+1:
                    selbox += "<option selected value='%s'>%s" % (i-1,i)
                else:
                    selbox += "<option value='%s'>%s" % (i-1,i)
            selbox += """
                </select>"""
            html.append("""
                        <tr>
                        <td>
                            <a href=%s><img src="%s" alt="%s" class="imglink"></a>&nbsp;%s&nbsp;%s<a href=%s>%s</a>
                        </td>
                        </tr>
                        """%(quoteattr(str(urlStatus)), img, text, selbox, checkbox, quoteattr(str(urlModif)), gs.getTitle()) )
        html.insert(0, """<input type="hidden" name="oldpos"><table>""")
        html.append("</table>")
        return "".join(html)

    def _getStatusesHTML(self):
        regForm=self._conf.getRegistrationForm()
        html=[]
        for st in regForm.getStatusesList():
            urlStatus = urlHandlers.UHConfModifRegFormStatusModif.getURL(self._conf)
            urlStatus.addParam("statusId", st.getId())
            html.append("""
                        <tr>
                        <td>
                            &nbsp;<input type="checkbox" name="statusesIds" value="%s">&nbsp;<a href=%s>%s</a>
                        </td>
                        </tr>
                        """%(st.getId(), quoteattr(str(urlStatus)), st.getCaption().strip() or  _("""-- [%s]  _("status with no name") --""")%st.getId()) )
        if html == []:
            html.append( _("""<tr><td style="padding-left:20px"><ul><li> _("No statuses defined yet").</li></ul><br>  _("You can use this option in order to create general statuses you will be able to use afterwards in the list of registrants. For instance, you can create a status "paid" in order to check if someone has paid or not").</td></tr>"""))
        html.insert(0, """<a href="" name="statuses"></a><table style="padding-top:20px">""")
        html.append("</table>")
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        vars["setStatusURL"]=urlHandlers.UHConfModifRegFormChangeStatus.getURL(self._conf)
        vars["dataModificationURL"]=urlHandlers.UHConfModifRegFormDataModification.getURL(self._conf)
        vars["enablePic"]=quoteattr(str(Configuration.Config.getInstance().getSystemIconURL( "enabledSection" )))
        vars["disablePic"]=quoteattr(str(Configuration.Config.getInstance().getSystemIconURL( "disabledSection" )))
        if regForm.isActivated():
            vars["changeTo"] = "False"
            vars["status"] =  _("ENABLED")
            vars["changeStatus"] =  _("DISABLE")
            d = ""
            if regForm.getStartRegistrationDate() is not None:
                d = regForm.getStartRegistrationDate().strftime("%A %d %B %Y")
            vars["startDate"]=d
            d = ""
            if regForm.getEndRegistrationDate() is not None:
                d = regForm.getEndRegistrationDate().strftime("%A %d %B %Y")
            vars["endDate"]=d
            d = ""
            if regForm.getModificationEndDate() is not None:
                d = regForm.getModificationEndDate().strftime("%A %d %B %Y")
            vars["modificationEndDate"]=d
            vars["announcement"] = regForm.getAnnouncement()
            vars["disabled"] = ""
            vars["contactInfo"] = regForm.getContactInfo()
            vars["usersLimit"] = _("""--_("No limit")--""")
            if regForm.getUsersLimit() > 0:
                vars["usersLimit"] = regForm.getUsersLimit()
            vars["title"] = regForm.getTitle()
            vars["notification"] = _("""
                                    <table>
                                        <tr>
                                            <td align="right"><b> _("To List"):</b></td>
                                            <td align="left">%s</td>
                                        </tr>
                                        <tr>
                                            <td align="right"><b> _("Cc List"):</b></td>
                                            <td align="left">%s</td>
                                        </tr>
                                    </table>
                                    """)%(", ".join(regForm.getNotification().getToList()) or _("""--_("no TO list")--"""), ", ".join(regForm.getNotification().getCCList()) or _("""--_("no CC list")--"""))
            vars["mandatoryAccount"] =  _("Yes")
            if not regForm.isMandatoryAccount():
                vars["mandatoryAccount"] =  _("No")
            vars["Currency"]=regForm.getCurrency()
        else:
            vars["changeTo"] = "True"
            vars["status"] =_("DISABLED")
            vars["changeStatus"] = _("ENABLE")
            vars["startDate"] = ""
            vars["endDate"] = ""
            vars["modificationEndDate"]=""
            vars["announcement"] = ""
            vars["disabled"] = 'disabled = "disabled"'
            vars["contactInfo"] = ""
            vars["usersLimit"] = ""
            vars["title"] = ""
            vars["notification"] = ""
            vars["mandatoryAccount"] = ""
            vars["Currency"]=""
        vars["sections"] = self._getSectionsHTML()
        vars["personalfields"] = self._getPersonalFieldsHTML()
        vars["actionSectionURL"]=quoteattr(str(urlHandlers.UHConfModifRegFormActionSection.getURL(self._conf)))
        vars["statuses"] = self._getStatusesHTML()
        vars["actionStatusesURL"]=quoteattr(str(urlHandlers.UHConfModifRegFormActionStatuses.getURL(self._conf)))
        return vars

class WPConfModifRegFormDataModification( WPConfModifRegFormBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormDataModification(self._conf)
        return wc.getHTML()

class WConfModifRegFormDataModification( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        vars["postURL"]=urlHandlers.UHConfModifRegFormPerformDataModification.getURL(self._conf)
        vars["sDay"]=""
        vars["sMonth"]=""
        vars["sYear"]=""
        if regForm.getStartRegistrationDate() is not None:
            d = regForm.getStartRegistrationDate()
            vars["sDay"]=d.day
            vars["sMonth"]=d.month
            vars["sYear"]=d.year
        vars["eDay"]=""
        vars["eMonth"]=""
        vars["eYear"]=""
        if regForm.getEndRegistrationDate() is not None:
            d = regForm.getEndRegistrationDate()
            vars["eDay"]=d.day
            vars["eMonth"]=d.month
            vars["eYear"]=d.year
        vars["meDay"]=""
        vars["meMonth"]=""
        vars["meYear"]=""
        if regForm.getModificationEndDate() is not None:
            d = regForm.getModificationEndDate()
            vars["meDay"]=d.day
            vars["meMonth"]=d.month
            vars["meYear"]=d.year
        vars["calendarIconURL"] = Config.getInstance().getSystemIconURL("calendar")
        vars["calendarSelectURL"] = urlHandlers.UHSimpleCalendar.getURL()
        vars["announcement"] = regForm.getAnnouncement()
        vars["contactInfo"] = regForm.getContactInfo()
        vars["usersLimit"] = regForm.getUsersLimit()
        vars["title"] = regForm.getTitle()
        vars["toList"] = ", ".join(regForm.getNotification().getToList())
        vars["ccList"] = ", ".join(regForm.getNotification().getCCList())
        vars["mandatoryAccount"]=""
        if regForm.isMandatoryAccount():
            vars["mandatoryAccount"]= _("CHECKED")
        vars["Currency"]="""<select name="%s">%s</select>"""%("Currency", CurrencyRegistry.getSelectItemsHTML(regForm.getCurrency()))
        return vars

class WPConfModifRegFormSectionsBase(WPConfModifRegFormBase):

    def _setActiveSideMenuItem(self):
        self._regFormMenuItem.setActive(True)

    def _getPageContent( self, params ):
        self._createTabCtrl()
        banner = wcomponents.WRegFormSectionBannerModif(self._targetSection, self._conf).getHTML()
        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner+html

class WPConfModifRegFormSessionsBase(WPConfModifRegFormSectionsBase):

    def __init__( self, rh, conference ):
        WPConfModifRegFormSectionsBase.__init__(self, rh, conference)
        self._targetSection = self._conf.getRegistrationForm().getSessionsForm()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main",  _("Main"), \
                urlHandlers.UHConfModifRegFormSessions.getURL( self._conf ) )
#        wf = self._rh.getWebFactory()
#        if wf:
#            wf.customiseTabCtrl( self._tabCtrl )
        self._setActiveTab()

#    def _applyFrame( self, body ):
#        frame = WRegFormSessionsModifFrame( self._conf, self._getAW() )
#        p = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
#            "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL, \
#            "confModifURLGen": urlHandlers.UHConfModifRegForm.getURL}
#        return frame.getHTML( body, **p )

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return "nothing"

#class WRegFormSessionsModifFrame(wcomponents.WTemplated):
#
#    def __init__(self, conf, aw):
#        self._conf = conf
#        self._aw = aw
#        self._sessions = self._conf.getRegistrationForm().getSessionsForm()
#
#    def getHTML( self, body, **params ):
#        params["body"] = body
#        return wcomponents.WTemplated.getHTML( self, params )
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        vars["context"] = wcomponents.WConfModifHeader( self._conf, self._aw ).getHTML(vars)
#        vars["title"] = self._sessions.getTitle()
#        vars["titleTabPixels"] = self.getTitleTabPixels()
#        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
#        vars["closeHeaderTags"] = self.getCloseHeaderTags()
#        return vars
#
#    def getOwnerComponent( self ):
#        wc = wcomponents.WConferenceModifFrame(self._conf, self._aw)
#        return wc
#
#    def getIntermediateVTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return 7 + wc.getIntermediateVTabPixels()
#
#    def getTitleTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return wc.getTitleTabPixels() - 7
#
#    def getCloseHeaderTags( self ):
#        wc = self.getOwnerComponent()
#        return "</table></td></tr>" + wc.getCloseHeaderTags()

class WPConfModifRegFormSessions( WPConfModifRegFormSessionsBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormSessions(self._conf)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormSessionsRemove.getURL( self._conf ))),
             'postAddURL': quoteattr(str(urlHandlers.UHConfModifRegFormSessionsAdd.getURL( self._conf ))),
             'dataModificationURL': quoteattr(str(urlHandlers.UHConfModifRegFormSessionsDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormSessions( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def _getSessionsHTML(self, sessions):
        if sessions.getSessionList() == []:
            html =  _("""--_("None selected")--""")
        else:
            html = []
            for ses in sessions.getSessionList(True):
                cancelled = ""
                if ses.isCancelled():
                    cancelled = "<font color=\"red\">(cancelled)</font>"
                html.append("""
                        <input type="checkbox" name="sessionIds" value="%s">%s %s
                        """%(ses.getId(), ses.getTitle(), cancelled) )
            html = "<br>".join(html)
        return html

    def _getSessionFormTypeHTML(self, sessions):
        if sessions.getType()=="all":
            return  _("multiple")
        return  _("2 choices")

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        sessions = regForm.getSessionsForm()
        vars["title"] = sessions.getTitle()
        vars["description"] =  sessions.getDescription()
        vars["type"] =  self._getSessionFormTypeHTML(sessions)
        vars["sessions"] = self._getSessionsHTML(sessions)
        return vars

class WPConfModifRegFormSessionsDataModif( WPConfModifRegFormSessionsBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormSessionsDataModif(self._conf)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormSessionsPerformDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormSessionsDataModif( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def _getSessionFormTypesHTML(self, sessions):
        html=["""<select name="sessionFormType">"""]
        selected=""
        if sessions.getType()=="2priorities":
            selected=" selected"
        html.append( _("""<option value="2priorities"%s> _("2 choices")</option>""")%selected)
        selected=""
        if sessions.getType()=="all":
            selected=" selected"
        html.append( _("""<option value="all"%s> _("multiple")</option>""")%selected)
        html.append("""</select>""")
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        sessions = regForm.getSessionsForm()
        vars["title"] = sessions.getTitle()
        vars["description"] =  sessions.getDescription()
        vars["types"] =  self._getSessionFormTypesHTML(sessions)
        return vars

class WPConfModifRegFormSessionsAdd( WPConfModifRegFormSessionsBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormSessionsAdd(self._conf)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormSessionsPerformAdd.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormSessionsAdd( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def _getSessionsHTML(self, sessions):
        html = []
        for ses in self._conf.getSessionList():
            if not sessions.hasSession(ses.getId()):
                html.append("""
                    <input type="checkbox" name="sessionIds" value="%s" >%s
                    """%(ses.getId(), ses.getTitle()) )
        if html == []:
            html =  _("""--  _("No sessions to add") --""")
        else:
            html = "<br>".join(html)
        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        sessions = regForm.getSessionsForm()
        vars["title"] = sessions.getTitle()
        vars["sessions"] = self._getSessionsHTML(sessions)
        return vars

class WPConfModifRegFormAccommodationBase(WPConfModifRegFormSectionsBase):

    def __init__( self, rh, conference ):
        WPConfModifRegFormSectionsBase.__init__(self, rh, conference)
        self._targetSection = self._conf.getRegistrationForm().getAccommodationForm()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", "Main", \
                urlHandlers.UHConfModifRegFormAccommodation.getURL( self._conf ) )
#        wf = self._rh.getWebFactory()
#        if wf:
#            wf.customiseTabCtrl( self._tabCtrl )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return  _("nothing")

#class WRegFormAccommodationModifFrame(wcomponents.WTemplated):
#
#    def __init__(self, conf, aw):
#        self._conf = conf
#        self._aw = aw
#        self._accommodation = self._conf.getRegistrationForm().getAccommodationForm()
#
#    def getHTML( self, body, **params ):
#        params["body"] = body
#        return wcomponents.WTemplated.getHTML( self, params )
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        vars["context"] = wcomponents.WConfModifHeader( self._conf, self._aw ).getHTML(vars)
#        vars["title"] = self._accommodation.getTitle()
#        vars["titleTabPixels"] = self.getTitleTabPixels()
#        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
#        vars["closeHeaderTags"] = self.getCloseHeaderTags()
#        return vars
#
#    def getOwnerComponent( self ):
#        wc = wcomponents.WConferenceModifFrame(self._conf, self._aw)
#        return wc
#
#    def getIntermediateVTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return 7 + wc.getIntermediateVTabPixels()
#
#    def getTitleTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return wc.getTitleTabPixels() - 7
#
#    def getCloseHeaderTags( self ):
#        wc = self.getOwnerComponent()
#        return "</table></td></tr>" + wc.getCloseHeaderTags()

class WPConfModifRegFormAccommodation( WPConfModifRegFormAccommodationBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormAccommodation(self._conf)
        p = {
             'dataModificationURL': quoteattr(str(urlHandlers.UHConfModifRegFormAccommodationDataModif.getURL( self._conf ))),
             'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormAccommodationTypeRemove.getURL( self._conf ))),
             'postNewURL': quoteattr(str(urlHandlers.UHConfModifRegFormAccommodationTypeAdd.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormAccommodation( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def _getAccommodationTypesHTML(self, accommodation):
        html=[]
        for atype in accommodation.getAccommodationTypesList():
            cancelled = ""
            if atype.isCancelled():
                cancelled =  _(""" <font color=\"red\">( _("disabled") )</font>""")
            url = urlHandlers.UHConfModifRegFormAccommodationTypeModify.getURL(atype)
            limit =  _(""" <i>[ _("unlimited places") ]</i>""")
            if atype.getPlacesLimit() > 0:
                limit = " <i>[%s/%s place(s)]</i>"%(atype.getCurrentNoPlaces(), atype.getPlacesLimit())
            html.append("""<tr>
                                <td align="left" style="padding-left:10px"><input type="checkbox" name="accommodationType" value="%s"><a href=%s>%s</a>%s%s</td>
                            </tr>
                        """%(atype.getId(), url, self.htmlText(atype.getCaption()), limit, cancelled ) )
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        accommodation = regForm.getAccommodationForm()
        vars["title"] = accommodation.getTitle()
        vars["description"] =  accommodation.getDescription()
        aDates = accommodation.getArrivalDates()
        vars["arrivalDates"] = "%s -> %s" % (aDates[0].strftime("%d %B %Y"),aDates[-1].strftime("%d %B %Y"))
        dDates = accommodation.getDepartureDates()
        vars["departureDates"] = "%s -> %s" % (dDates[0].strftime("%d %B %Y"),dDates[-1].strftime("%d %B %Y"))
        vars["accommodationTypes"] = self._getAccommodationTypesHTML(accommodation)
        return vars

class WPConfModifRegFormAccommodationDataModif( WPConfModifRegFormAccommodationBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormAccommodationDataModif(self._conf)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormAccommodationPerformDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormAccommodationDataModif( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        accommodation = regForm.getAccommodationForm()
        vars["title"] = accommodation.getTitle()
        vars["description"] =  accommodation.getDescription()
        vars["aoffset1"] = accommodation.getArrivalOffsetDates()[0]
        vars["aoffset2"] = accommodation.getArrivalOffsetDates()[1]
        vars["doffset1"] = accommodation.getDepartureOffsetDates()[0]
        vars["doffset2"] = accommodation.getDepartureOffsetDates()[1]
        return vars

class WPConfModifRegFormAccommodationTypeAdd( WPConfModifRegFormAccommodationBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormAccommodationTypeAdd()
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormAccommodationTypePerformAdd.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormAccommodationTypeAdd( wcomponents.WTemplated ):
    pass

class WPConfModifRegFormAccommodationTypeModify( WPConfModifRegFormAccommodationBase ):

    def __init__(self, rh, conf, accoType):
        WPConfModifRegFormAccommodationBase.__init__(self, rh, conf)
        self._accoType = accoType

    def _getTabContent( self, params ):
        wc = WConfModifRegFormAccommodationTypeModify(self._accoType)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormAccommodationTypePerformModify.getURL( self._accoType )))
            }
        return wc.getHTML(p)

class WConfModifRegFormAccommodationTypeModify( wcomponents.WTemplated ):

    def __init__(self, accoType):
        self._accoType = accoType

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["caption"] = quoteattr(self._accoType.getCaption())
        vars["placesLimit"] = self._accoType.getPlacesLimit()
        vars["checked"] = ""
        if self._accoType.isCancelled():
            vars["checked"] = """ checked="checked" """
        return vars

class WPConfRemoveAccommodationType(WPConfModifRegFormAccommodationBase):

    def __init__(self, rh, conf, accoTypeIds, accommodationTypes):
        WPConfModifRegFormAccommodationBase.__init__(self, rh, conf)
        self._eventType="conference"
        if self._rh.getWebFactory() is not None:
            self._eventType=self._rh.getWebFactory().getId()

        self._accoTypeIds = accoTypeIds
        self._accommodationTypes = []
        counter = 0
        for at in accommodationTypes :
            self._accommodationTypes.append("<li>%s</li>"%at)

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent( self, params ):
        msg =  _("""
        <font size="+2"> _("Are you sure that you want to DELETE this accomodation")? <br><table><tr><td align="left"><ul>%s</ul></td></tr></table></font><br>
        ( _("Note that if you delete this accomodation, registrants who applied for it
        will lose their accomodation info") )
              """)%("".join(self._accommodationTypes))
        wc = wcomponents.WConfirmation()
        return wc.getHTML( msg, \
                        urlHandlers.UHConfModifRegFormAccommodationTypeRemove.getURL(self._conf),\
                        {"accommodationType":self._accoTypeIds} , \
                        confirmButtonCaption= _("Yes"), cancelButtonCaption=  _("No"))

class WPConfModifRegFormFurtherInformationBase(WPConfModifRegFormSectionsBase):

    def __init__( self, rh, conference ):
        WPConfModifRegFormSectionsBase.__init__(self, rh, conference)
        self._targetSection = self._conf.getRegistrationForm().getFurtherInformationForm()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main",  _("Main"), \
                urlHandlers.UHConfModifRegFormFurtherInformation.getURL( self._conf ) )
#        wf = self._rh.getWebFactory()
#        if wf:
#            wf.customiseTabCtrl( self._tabCtrl )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return  _("nothing")

#class WRegFormFurtherInformationModifFrame(wcomponents.WTemplated):
#
#    def __init__(self, conf, aw):
#        self._conf = conf
#        self._aw = aw
#        self._furtherInformation = self._conf.getRegistrationForm().getFurtherInformationForm()
#
#    def getHTML( self, body, **params ):
#        params["body"] = body
#        return wcomponents.WTemplated.getHTML( self, params )
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        vars["context"] = wcomponents.WConfModifHeader( self._conf, self._aw ).getHTML(vars)
#        vars["title"] = self._furtherInformation.getTitle()
#        vars["titleTabPixels"] = self.getTitleTabPixels()
#        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
#        vars["closeHeaderTags"] = self.getCloseHeaderTags()
#        return vars
#
#    def getOwnerComponent( self ):
#        wc = wcomponents.WConferenceModifFrame(self._conf, self._aw)
#        return wc
#
#    def getIntermediateVTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return 7 + wc.getIntermediateVTabPixels()
#
#    def getTitleTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return wc.getTitleTabPixels() - 7
#
#    def getCloseHeaderTags( self ):
#        wc = self.getOwnerComponent()
#        return "</table></td></tr>" + wc.getCloseHeaderTags()

class WPConfModifRegFormFurtherInformation( WPConfModifRegFormFurtherInformationBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormFurtherInformation(self._conf)
        p = {
             'dataModificationURL': quoteattr(str(urlHandlers.UHConfModifRegFormFurtherInformationDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormFurtherInformation( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        fi = regForm.getFurtherInformationForm()
        vars["title"] = fi.getTitle()
        vars["content"] =  fi.getContent()
        return vars

class WPConfModifRegFormFurtherInformationDataModif( WPConfModifRegFormFurtherInformationBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormFurtherInformationDataModif(self._conf)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormFurtherInformationPerformDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormFurtherInformationDataModif( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        fi = regForm.getFurtherInformationForm()
        vars["title"] = fi.getTitle()
        vars["content"] =  fi.getContent()
        return vars

class WPConfModifRegFormReasonParticipationBase(WPConfModifRegFormSectionsBase):

    def __init__( self, rh, conference ):
        WPConfModifRegFormSectionsBase.__init__(self, rh, conference)
        self._targetSection = self._conf.getRegistrationForm().getReasonParticipationForm()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", "Main", \
                urlHandlers.UHConfModifRegFormReasonParticipation.getURL( self._conf ) )
#        wf = self._rh.getWebFactory()
#        if wf:
#            wf.customiseTabCtrl( self._tabCtrl )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return  _("nothing")

#class WRegFormReasonParticipationModifFrame(wcomponents.WTemplated):
#
#    def __init__(self, conf, aw):
#        self._conf = conf
#        self._aw = aw
#        self._reasonParticipation = self._conf.getRegistrationForm().getReasonParticipationForm()
#
#    def getHTML( self, body, **params ):
#        params["body"] = body
#        return wcomponents.WTemplated.getHTML( self, params )
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        vars["context"] = wcomponents.WConfModifHeader( self._conf, self._aw ).getHTML(vars)
#        vars["title"] = self._reasonParticipation.getTitle()
#        vars["titleTabPixels"] = self.getTitleTabPixels()
#        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
#        vars["closeHeaderTags"] = self.getCloseHeaderTags()
#        return vars
#
#    def getOwnerComponent( self ):
#        wc = wcomponents.WConferenceModifFrame(self._conf, self._aw)
#        return wc
#
#    def getIntermediateVTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return 7 + wc.getIntermediateVTabPixels()
#
#    def getTitleTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return wc.getTitleTabPixels() - 7
#
#    def getCloseHeaderTags( self ):
#        wc = self.getOwnerComponent()
#        return "</table></td></tr>" + wc.getCloseHeaderTags()

class WPConfModifRegFormReasonParticipation( WPConfModifRegFormReasonParticipationBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormReasonParticipation(self._conf)
        p = {
             'dataModificationURL': quoteattr(str(urlHandlers.UHConfModifRegFormReasonParticipationDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormReasonParticipation( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        rp = regForm.getReasonParticipationForm()
        vars["title"] = rp.getTitle()
        vars["description"] =  rp.getDescription()
        return vars

class WPConfModifRegFormReasonParticipationDataModif( WPConfModifRegFormReasonParticipationBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormReasonParticipationDataModif(self._conf)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormReasonParticipationPerformDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormReasonParticipationDataModif( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        rp = regForm.getReasonParticipationForm()
        vars["title"] = rp.getTitle()
        vars["description"] =  rp.getDescription()
        return vars

class WPConfModifRegFormSocialEventBase(WPConfModifRegFormSectionsBase):

    def __init__( self, rh, conference ):
        WPConfModifRegFormSectionsBase.__init__(self, rh, conference)
        self._targetSection = self._conf.getRegistrationForm().getSocialEventForm()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", "Main", \
                urlHandlers.UHConfModifRegFormSocialEvent.getURL( self._conf ) )
#        wf = self._rh.getWebFactory()
#        if wf:
#            wf.customiseTabCtrl( self._tabCtrl )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return  _("nothing")

#class WRegFormSocialEventModifFrame(wcomponents.WTemplated):
#
#    def __init__(self, conf, aw):
#        self._conf = conf
#        self._aw = aw
#        self._socialEvent = self._conf.getRegistrationForm().getSocialEventForm()
#
#    def getHTML( self, body, **params ):
#        params["body"] = body
#        return wcomponents.WTemplated.getHTML( self, params )
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        vars["context"] = wcomponents.WConfModifHeader( self._conf, self._aw ).getHTML(vars)
#        vars["title"] = self._socialEvent.getTitle()
#        vars["titleTabPixels"] = self.getTitleTabPixels()
#        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
#        vars["closeHeaderTags"] = self.getCloseHeaderTags()
#        return vars
#
#    def getOwnerComponent( self ):
#        wc = wcomponents.WConferenceModifFrame(self._conf, self._aw)
#        return wc
#
#    def getIntermediateVTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return 7 + wc.getIntermediateVTabPixels()
#
#    def getTitleTabPixels( self ):
#        wc = self.getOwnerComponent()
#        return wc.getTitleTabPixels() - 7
#
#    def getCloseHeaderTags( self ):
#        wc = self.getOwnerComponent()
#        return "</table></td></tr>" + wc.getCloseHeaderTags()

class WPConfModifRegFormSocialEvent( WPConfModifRegFormSocialEventBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormSocialEvent(self._conf)
        p = {
             'dataModificationURL': quoteattr(str(urlHandlers.UHConfModifRegFormSocialEventDataModif.getURL( self._conf ))),
             'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormSocialEventRemove.getURL( self._conf ))),
             'postNewURL': quoteattr(str(urlHandlers.UHConfModifRegFormSocialEventAdd.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormSocialEvent( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def _getSocialEventsHTML(self, socialEvent):
        html=[]
        for se in socialEvent.getSocialEventList(True):
            cancelled = ""
            if se.isCancelled():
                cancelled =  _("""<font color=\"red\">( _("cancelled") )</font>""")
                if se.getCancelledReason().strip():
                    cancelled =  _("""<font color=\"red\">( _("disabled"): %s)</font>""")%se.getCancelledReason().strip()
            limit = " <i>[unlimited places]</i>"
            if se.getPlacesLimit() > 0:
                limit = " <i>[%s/%s place(s)]</i>"%(se.getCurrentNoPlaces(), se.getPlacesLimit())
            url = urlHandlers.UHConfModifRegFormSocialEventItemModify.getURL(se)
            html.append("""<tr>
                                <td align="left" style="padding-left:10px"><input type="checkbox" name="socialEvents" value="%s"><a href=%s>%s</a>%s%s</td>
                            </tr>
                        """%(se.getId(), quoteattr(str(url)), self.htmlText(se.getCaption()), limit, cancelled ) )
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        socialEvent = regForm.getSocialEventForm()
        vars["title"] = socialEvent.getTitle()
        vars["description"] =  socialEvent.getDescription()
        vars["intro"] =  socialEvent.getIntroSentence()
        vars["selectionType"] = socialEvent.getSelectionTypeCaption()
        vars["socialEvents"] = self._getSocialEventsHTML(socialEvent)
        return vars

class WPConfModifRegFormSocialEventDataModif( WPConfModifRegFormSocialEventBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormSocialEventDataModif(self._conf)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormSocialEventPerformDataModif.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormSocialEventDataModif( wcomponents.WTemplated ):

    def __init__( self, conference ):
        self._conf = conference

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        socialEvent = regForm.getSocialEventForm()
        vars["title"] = socialEvent.getTitle()
        vars["description"] =  socialEvent.getDescription()
        vars["intro"] =  socialEvent.getIntroSentence()
        vars["socEvent"] = socialEvent
        return vars

class WPConfModifRegFormSocialEventAdd( WPConfModifRegFormSocialEventBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormSocialEventAdd()
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormSocialEventPerformAdd.getURL( self._conf )))
            }
        return wc.getHTML(p)

class WConfModifRegFormSocialEventAdd( wcomponents.WTemplated ):
    pass

class WPConfModifRegFormSocialEventItemModify( WPConfModifRegFormSocialEventBase ):

    def __init__(self, rh, conf, socialEventItem):
        WPConfModifRegFormSocialEventBase.__init__(self, rh, conf)
        self._socialEventItem = socialEventItem

    def _getTabContent( self, params ):
        wc = WConfModifRegFormSocialEventItemModify(self._socialEventItem)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormSocialEventItemPerformModify.getURL( self._socialEventItem )))
            }
        return wc.getHTML(p)

class WConfModifRegFormSocialEventItemModify( wcomponents.WTemplated ):

    def __init__(self, socialEventItem):
        self._socialEventItem = socialEventItem

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["caption"] = quoteattr(self._socialEventItem.getCaption())
        vars["checked"] = ""
        if self._socialEventItem.isCancelled():
            vars["checked"] = """ checked="checked" """
        vars["reason"] = ""
        if self._socialEventItem.getCancelledReason().strip() != "":
            vars["reason"] = self._socialEventItem.getCancelledReason()
        vars["maxPlace"] = self._socialEventItem.getMaxPlacePerRegistrant()
        vars["placesLimit"] = self._socialEventItem.getPlacesLimit()
        return vars

class WPConfRemoveSocialEvent(WPConfModifRegFormSocialEventBase):

    def __init__(self, rh, conf, socialEventIds, eventNames):
        WPConfModifRegFormSocialEventBase.__init__(self, rh, conf)
        self._eventType="conference"
        self._socialEventIds = socialEventIds
        self._eventNames = []
        for n in eventNames :
            self._eventNames.append("<li>%s</li>"%n)
        if self._rh.getWebFactory() is not None:
            self._eventType=self._rh.getWebFactory().getId()

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent( self, params ):
        msg =  _("""
        <font size="+2"> _("Are you sure that you want to DELETE this social event")? <br><table><tr><td align="left"><ul>%s</ul></td></tr></table></font><br>
        ( _("Note that if you delete this social event, registrants who applied for it
        will lose their social event info") )
              """)%("".join(self._eventNames))
        wc = wcomponents.WConfirmation()
        return wc.getHTML( msg, \
                        urlHandlers.UHConfModifRegFormSocialEventRemove.getURL( self._conf ),\
                         {"socialEvents":self._socialEventIds}, \
                        confirmButtonCaption= _("Yes"), cancelButtonCaption= _("No") )

class WPConfModifRegFormStatusesRemConfirm(WPConfModifRegFormBase):

    def __init__(self,rh,target, stids):
        WPConfModifRegFormBase.__init__(self, rh, target)
        self._statusesIds=stids

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        ssHTML=["<ul>"]
        for id in self._statusesIds:
            s=self._conf.getRegistrationForm().getStatusById(id)
            ssHTML.append("""
                                <li>%s</li>
                                """%(s.getCaption().strip() or  _("""-- [%s]  _("status with no name") --""")%s.getId()))
        ssHTML.append("</ul>")
        msg= _(""" _("Are you sure you want to delete the following statuses
        linked to the registration form module")?
        %s
        <font color="red">( _("note that current registrants will lose this info") )</font>""")%("".join(ssHTML))
        url=urlHandlers.UHConfModifRegFormActionStatuses.getURL(self._conf)
        return wc.getHTML(msg,url,{"statusesIds":self._statusesIds, "removeStatuses":"1"})

class WPConfModifRegFormGeneralSectionRemConfirm(WPConfModifRegFormBase):

    def __init__(self,rh,target, gss):
        WPConfModifRegFormBase.__init__(self, rh, target)
        self._generalSections=gss

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        ssHTML=["<ul>"]
        for id in self._generalSections:
            s=self._conf.getRegistrationForm().getGeneralSectionFormById(id)
            ssHTML.append("""
                                <li>%s</li>
                                """%(s.getTitle()))
        ssHTML.append("</ul>")
        msg= _("""  _("Are you sure you want to delete the following sections
        of the registration form")?
        %s
        <font color="red">( _("note that current registrants will lose this info"))</font>""")%("".join(ssHTML))
        url=urlHandlers.UHConfModifRegFormActionSection.getURL(self._conf)
        return wc.getHTML(msg,url,{"sectionsIds":self._generalSections, "removeSection":"1"})

class WPConfModifRegFormGeneralSectionBase(WPConfModifRegFormSectionsBase):

    def __init__(self, rh, gs):
        WPConfModifRegFormSectionsBase.__init__(self, rh, gs.getConference())
        self._targetSection=self._generalSectionForm=gs

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main",  _("Main"), \
                urlHandlers.UHConfModifRegFormGeneralSection.getURL( self._conf ) )
#        wf = self._rh.getWebFactory()
#        if wf:
#            wf.customiseTabCtrl( self._tabCtrl )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return "nothing"

class WRegFormGeneralSectionModifFrame(wcomponents.WTemplated):

    def __init__(self, gs, aw):
        self._conf = gs.getConference()
        self._aw = aw
        self._generalSection = gs

    def getHTML( self, body, **params ):
        params["body"] = body
        return wcomponents.WTemplated.getHTML( self, params )

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["context"] = wcomponents.WConfModifHeader( self._conf, self._aw ).getHTML(vars)
        vars["title"] = self._generalSection.getTitle()
        vars["titleTabPixels"] = self.getTitleTabPixels()
        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
        vars["closeHeaderTags"] = self.getCloseHeaderTags()
        return vars

    def getOwnerComponent( self ):
        wc = wcomponents.WConferenceModifFrame(self._conf, self._aw)
        return wc

    def getIntermediateVTabPixels( self ):
        wc = self.getOwnerComponent()
        return 7 + wc.getIntermediateVTabPixels()

    def getTitleTabPixels( self ):
        wc = self.getOwnerComponent()
        return wc.getTitleTabPixels() - 7

    def getCloseHeaderTags( self ):
        wc = self.getOwnerComponent()
        return "</table></td></tr>" + wc.getCloseHeaderTags()

class WPConfModifRegFormGeneralSection( WPConfModifRegFormGeneralSectionBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormGeneralSection(self._generalSectionForm)
        p = {
             'dataModificationURL': quoteattr(str(urlHandlers.UHConfModifRegFormGeneralSectionDataModif.getURL( self._generalSectionForm ))),
             'postActionURL': quoteattr(str(urlHandlers.UHConfModifRegFormGeneralSectionFieldRemove.getURL( self._generalSectionForm ))),
             'postNewURL': quoteattr(str(urlHandlers.UHConfModifRegFormGeneralSectionFieldAdd.getURL( self._generalSectionForm )))
            }
        return wc.getHTML(p)

class WConfModifRegFormGeneralSection( wcomponents.WTemplated ):

    def __init__( self, gs ):
        self._conf = gs.getConference()
        self._generalSection=gs

    def _getGeneralFieldsHTML(self):
        html=[]
        ##############
        #jmf-start
        #for f in self._generalSection.getFields():
        for f in self._generalSection.getSortedFields():
        #jmf-end
        ##############
            url = urlHandlers.UHConfModifRegFormGeneralSectionFieldModif.getURL(f)
            spec = " <b>(%s"%f.getInput().getName()
            if f.isMandatory():
                spec =  _(""" %s, _("mandatory") """)%spec
            if f.isBillable():
                spec =  _(""" %s , _("Billable") = %s """)%(spec,self.htmlText(f.getPrice()))

            spec = " %s)</b>"%spec

            #
            # add the selection box here for sorting...
            #

            selbox = """<select name="newpos%s" onChange="this.form.oldpos.value='%s';this.form.submit();">""" % (self._generalSection.getSortedFields().index(f),self._generalSection.getSortedFields().index(f))
            for i in range(1,len(self._generalSection.getSortedFields()) + 1):
                if i == self._generalSection.getSortedFields().index(f)+1:
                    selbox += "<option selected value='%s'>%s" % (i-1,i)
                else:
                    selbox += "<option value='%s'>%s" % (i-1,i)
            selbox += """
                </select>"""

            html.append("""<tr>
                                <td align="left" style="padding-left:10px">%s<input type="checkbox" name="fieldsIds" value="%s"><a href=%s>%s</a>%s</td>
                            </tr>
                        """%(selbox,f.getId(), url, self.htmlText(f.getCaption()),spec) )
                        #"""%(f.getId(), url, f.getCaption(),spec) )
        html.insert(0,"""<a href="" name="sections"></a><input type="hidden" name="oldpos"><table align="left">""")
        html.append("</table>")
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["title"] = self._generalSection.getTitle()
        vars["description"] =  self._generalSection.getDescription()
        vars["generalFields"] = self._getGeneralFieldsHTML()
        return vars

class WPConfModifRegFormGeneralSectionDataModif( WPConfModifRegFormGeneralSectionBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormGeneralSectionDataModif(self._generalSectionForm)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormGeneralSectionPerformDataModif.getURL( self._generalSectionForm )))
            }
        return wc.getHTML(p)

class WConfModifRegFormGeneralSectionDataModif( wcomponents.WTemplated ):

    def __init__( self, generalSectionForm ):
        self._generalSectionForm = generalSectionForm

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["title"] = quoteattr(self._generalSectionForm.getTitle())
        vars["description"] =  self._generalSectionForm.getDescription()
        return vars

class WPConfModifRegFormGeneralSectionFieldAdd( WPConfModifRegFormGeneralSectionBase ):

    def __init__(self, rh, section, tmpField):
        WPConfModifRegFormGeneralSectionBase.__init__(self, rh, section)
        self._tmpField=tmpField

    def _getTabContent( self, params ):
        wc = WConfModifRegFormGeneralSectionFieldEdit(self._tmpField)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormGeneralSectionFieldPerformAdd.getURL( self._generalSectionForm )))
            }
        return wc.getHTML(p)

class WConfModifRegFormGeneralSectionFieldEdit( wcomponents.WTemplated ):

    def __init__( self, generalField=None):
        self._generalField = generalField

    def _getFieldTypesHTML(self):
        html=["""<select name="input" onchange="javascript:$E(WConfModifRegFormGeneralSectionFieldEdit).dom.submit();">"""]
        keylist=registration.FieldInputs.getAvailableInputKeys()
        keylist.sort()
        for key in keylist:
            selec=""
            if self._generalField is not None:
                if self._generalField.getInput().getId() == key:
                    selec="selected"
            html.append("""
                        <option value="%s" %s>%s</option>
                        """%(key, selec, registration.FieldInputs.getAvailableInputKlassById(key).getName()))
        html.append("""</select>""")
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["caption"] = ""
        vars["mandatory"] =  """ checked="checked" """
        #vars["billable"]= """ checked="checked" """
        #vars["price"]=""
        if self._generalField is not None:
            vars["caption"] = quoteattr(self._generalField.getCaption())
            #vars["price"]= quoteattr(self._generalField.getPrice())
            if not self._generalField.isMandatory():
                vars["mandatory"] =  ""
            #if not self._generalField.isBillable():
            #    vars["billable"] =  ""
        vars["inputtypes"]=self._getFieldTypesHTML()
        vars["specialOptions"]=""
        if self._generalField is not None:
            vars["specialOptions"]=self._generalField.getInput()._getSpecialOptionsHTML()
        return vars

class WPConfModifRegFormGeneralSectionFieldModif( WPConfModifRegFormGeneralSectionBase ):

    def __init__(self, rh, field, tmpField):
        WPConfModifRegFormGeneralSectionBase.__init__(self, rh, field.getParent())
        self._sectionField=field
        self._tmpField=tmpField

    def _getTabContent( self, params ):
        wc = WConfModifRegFormGeneralSectionFieldEdit(self._tmpField)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormGeneralSectionFieldPerformModif.getURL( self._sectionField )))
            }
        return wc.getHTML(p)

class WPConfModifRegFormGeneralSectionFieldRemConfirm(WPConfModifRegFormGeneralSectionBase):

    def __init__(self,rh,gs, fields):
        WPConfModifRegFormGeneralSectionBase.__init__(self, rh, gs)
        self._fields=fields

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        fieldsHTML=["<ul>"]
        for id in self._fields:
            f=self._generalSectionForm.getFieldById(id)
            fieldsHTML.append("""
                                <li>%s</li>
                                """%(f.getCaption()))
        fieldsHTML.append("</ul>")
        msg= _(""" _("Are you sure you want to delete the following fields
        of the section '%s'")?
        %s
        <font color="red">( _("note that current registrants will lose this info"))</font>""")%(self._generalSectionForm.getTitle(),
                "".join(fieldsHTML))
        url=urlHandlers.UHConfModifRegFormGeneralSectionFieldRemove.getURL(self._generalSectionForm)
        return wc.getHTML(msg,url,{"fieldsIds":self._fields})

class WPConfModifRegFormStatusModif( WPConfModifRegFormBase ):

    def __init__(self, rh, st, tmpst):
        WPConfModifRegFormBase.__init__(self, rh, st.getConference())
        self._status=st
        self._tempStatus=tmpst

    def _getTabContent( self, params ):
        wc = WConfModifRegFormStatusModif(self._status, self._tempStatus)
        p = {

             'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormStatusPerformModif.getURL( self._status )))
            }
        return wc.getHTML(p)

class WConfModifRegFormStatusModif( wcomponents.WTemplated ):

    def __init__( self, st, tmpst ):
        self._conf = st.getConference()
        self._status=st
        self._tempStatus=tmpst

    def _getStatusValuesHTML(self):
        html=["""<table>"""]
        for v in self._tempStatus.getStatusValuesList(True):
            default=""
            if self._tempStatus.getDefaultValue() is not None and  self._tempStatus.getDefaultValue().getId() == v.getId():
                default="""<i><b> (default)</b></i>"""
            html.append("""<tr>
                                <td align="left" style="padding-left:10px"><input type="checkbox" name="valuesIds" value="%s">%s%s</td>
                            </tr>
                        """%(v.getId(), self.htmlText(v.getCaption()), default) )
        html.append("""</table>""")
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["caption"] = self._tempStatus.getCaption()
        vars["values"] = self._getStatusValuesHTML()
        return vars

# ----------------------------------------------------------

# ----------------- DISPLAY AREA ---------------------------

class WPRegistrationForm( conferences.WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NERegistrationForm

    def _getBody( self, params ):
        wc = WConfRegistrationForm( self._conf, self._getAW().getUser() )
        pars = {"menuStatus":self._rh._getSession().getVar("menuStatus") or "open"}
        return wc.getHTML(pars)

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

class WConfRegistrationForm(wcomponents.WTemplated):

    def __init__(self, conf, av):
        self._conf = conf
        self._avatar = av

    def _getActionsHTML( self, showActions = False ):
        html = ""
        if showActions:
            regForm = self._conf.getRegistrationForm()
            if nowutc() < regForm.getStartRegistrationDate():
                return html
            else:
                submitOpt = ""
                registered = False
                if self._avatar is not None:
                    registered = self._avatar.isRegisteredInConf(self._conf)
                if regForm.inRegistrationPeriod() and not registered:
                   submitOpt =  _("""<li><a href=%s> _("Show registration form")</a></li>""")%(quoteattr(str(urlHandlers.UHConfRegistrationFormDisplay.getURL( self._conf ))))
                if registered:
                    submitOpt =  _("""%s<li><a href=%s> _("View or modify your already registration")</a></li>""")%(submitOpt, quoteattr(str("")))
                html =  _("""
                <b> _("Possible actions you can carry out"):</b>
                <ul>
                    %s
                </ul>
                       """)%( submitOpt )
        return html

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        regForm = self._conf.getRegistrationForm()
        vars["startDate"] = regForm.getStartRegistrationDate().strftime("%d %B %Y")
        vars["endDate"] = regForm.getEndRegistrationDate().strftime("%d %B %Y")
        vars["actions"] = self._getActionsHTML(vars["menuStatus"] == "close")
        vars["announcement"] = regForm.getAnnouncement()
        vars["title"] = regForm.getTitle()
        vars["usersLimit"] = ""
        if regForm.getUsersLimit() > 0:
            vars["usersLimit"] =  _("""
                                <tr>
                                    <td nowrap class="displayField"><b> _("Max No. of registrants"):</b></td>
                                    <td width="100%%" align="left">%s</td>
                                </tr>
                                """)%regForm.getUsersLimit()
        vars["contactInfo"] = ""
        if regForm.getContactInfo().strip()!="":
            vars["contactInfo"] =  _("""
                                <tr>
                                    <td nowrap class="displayField"><b> _("Contact info"):</b></td>
                                    <td width="100%%" align="left">%s</td>
                                </tr>
                                """ )%regForm.getContactInfo()
        return vars

class WPRegistrationFormDisplay( conferences.WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NERegistrationFormDisplay

    def _getBody( self, params ):
        wc = WConfRegistrationFormDisplay( self._conf, self._rh._getUser() )
        pars = {"menuStatus":self._rh._getSession().getVar("menuStatus") or "open"}
        return wc.getHTML(pars)

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._newRegFormOpt)

class WConfRegistrationFormDisplay(wcomponents.WTemplated):

    def __init__(self, conf, user):
        self._currentUser = user
        self._conf = conf

    def _getWComp(self, sect):
        if sect == self._conf.getRegistrationForm().getReasonParticipationForm():
            return WConfRegFormReasonParticipationDisplay(self._conf, self._currentUser)
        if sect == self._conf.getRegistrationForm().getSessionsForm():
            if self._conf.getRegistrationForm().getSessionsForm().getType()=="all":
                return WConfRegFormSessionsAllDisplay(self._conf, self._currentUser)
            else:
                return WConfRegFormSessions2PrioritiesDisplay(self._conf, self._currentUser)
        if sect == self._conf.getRegistrationForm().getAccommodationForm():
            return WConfRegFormAccommodationDisplay(self._conf, self._currentUser)
        if sect == self._conf.getRegistrationForm().getFurtherInformationForm():
            return WConfRegFormFurtherInformationDisplay(self._conf)
        if sect == self._conf.getRegistrationForm().getSocialEventForm():
            return WConfRegFormSocialEventDisplay(self._conf, self._currentUser)
        return WConfRegFormGeneralSectionDisplay(sect, self._currentUser)

    def _getOtherSectionsHTML(self):
        regForm=self._conf.getRegistrationForm()
        html=[]
        for gs in regForm.getSortedForms():
            wcomp=self._getWComp(gs)
            if gs.isEnabled():
                html.append( """
                            <tr>
                              <td><br></td>
                            </tr>
                            <tr>
                              <td align="left">
                                %s
                              </td>
                            </tr>
                            """%wcomp.getHTML())
        return "".join(html)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        regForm = self._conf.getRegistrationForm()
        vars["title"] = regForm.getTitle()
        vars["postURL"] = quoteattr(str(urlHandlers.UHConfRegistrationFormCreation.getURL(self._conf)))
        vars["personalData"] = WConfRegFormPersonalDataDisplay(self._conf, self._currentUser).getHTML()
        vars["otherSections"]=self._getOtherSectionsHTML()
        return vars

class WConfRegistrationFormPreview( WConfRegistrationFormDisplay ):

    def getVars(self):
        vars = WConfRegistrationFormDisplay.getVars(self)
        return vars

    def getHTML(self):
        return WConfRegistrationFormDisplay.getHTML(self)

class WConfRegFormGeneralSectionDisplay(wcomponents.WTemplated):

    def __init__(self, gs, currentUser):
        self._generalSection = gs
        self._currentUser = currentUser

    def _getFieldsHTML(self, miscGroup=None):
        html=[]
        registrant=None
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._generalSection.getConference()):
            registrant = self._currentUser.getRegistrantById(self._generalSection.getConference().getId())
        #jmf
        for f in self._generalSection.getSortedFields():
            miscItem=None
            if miscGroup is not None and miscGroup.getResponseItemById(f.getId()) is not None:
                miscItem=miscGroup.getResponseItemById(f.getId())
            html.append("""
                        <tr>
                          <td>
                             %s
                          </td>
                        </tr>
                        """%(f.getInput().getModifHTML(miscItem, registrant)) )
        return "".join(html)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self._generalSection.getTitle()
        vars["description"] = self._generalSection.getDescription()
        miscGroup=None
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._generalSection.getConference()):
            registrant = self._currentUser.getRegistrantById(self._generalSection.getConference().getId())
            miscGroup = registrant.getMiscellaneousGroupById(self._generalSection.getId())
        vars["fields"]=self._getFieldsHTML(miscGroup)
        return vars

class WConfRegFormPersonalDataDisplay(wcomponents.WTemplated):

    def __init__(self, conf, user):
        self._conf = conf
        self._currentUser = user

    def _getItemHTML(self, item, value):
        inputHTML = ""
        if item.getId() == "email":
            if self._currentUser is None or self._conf.canManageRegistration(self._currentUser):
                inputHTML = """<input type="text" name="%s" value="%s" size="40">"""%(item.getId(), value)
            else:
                inputHTML = """<input type="hidden" name="%s" value="%s">%s"""%(item.getId(), value, value)
        elif item.getInput() == "hidden":
            inputHTML = """<input type="%s" name="%s" value="%s">%s"""%(item.getInput(), item.getId(), value, value)
        elif item.getInput() == "list":
            if item.getId() == "title":
                for title in TitlesRegistry().getList():
                    selected = ""
                    if value == title:
                        selected = "selected"
                    inputHTML += """<option value="%s" %s>%s</option>"""%(title, selected, title)
                inputHTML = """<select name="%s">%s</select>"""%(item.getId(), inputHTML)
            elif item.getId() == "country":
                inputHTML= _("""<option value="">--  _("Select a country") --</option>""")
                for ck in CountryHolder().getCountrySortedKeys():
                    selected = ""
                    if value == ck:
                        selected = "selected"
                    inputHTML += """<option value="%s" %s>%s</option>"""%(ck, selected, CountryHolder().getCountryById(ck))
                inputHTML = """<select name="%s">%s</select>"""%(item.getId(), inputHTML)

        else:
            inputHTML = """<input type="%s" name="%s" size="40" value="%s">"""%(item.getInput(), item.getId(), value)
        mandatory="&nbsp; &nbsp;"
        if item.isMandatory():
            mandatory = """<font color="red">* </font>"""
        html = """
                <tr>
                    <td nowrap class="displayField">%s<b>%s</b></td>
                    <td width="100%%" align="left">%s</td>
                </tr>
                """%(mandatory, item.getName(), inputHTML)
        return html

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        personalData = self._conf.getRegistrationForm().getPersonalData()
        data = []
        sortedKeys = personalData.getSortedKeys()
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._conf):
            formValues = personalData.getValuesFromRegistrant(self._currentUser.getRegistrantById(self._conf.getId()))
        else:
            formValues = personalData.getValuesFromAvatar(self._currentUser)
        for key in sortedKeys:
            item = personalData.getDataItem(key)
            if item.isEnabled():
                data.append(self._getItemHTML(item, formValues.get(item.getId(), "")))
        vars["data"] = "".join(data)
        return vars

class WConfRegFormReasonParticipationDisplay(wcomponents.WTemplated):

    def __init__(self, conf, currentUser):
        self._conf = conf
        self._currentUser = currentUser

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        regForm = self._conf.getRegistrationForm()
        rp = regForm.getReasonParticipationForm()
        vars["title"] = rp.getTitle()
        vars["description"] = rp.getDescription()
        vars["reasonParticipation"] = ""
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._conf):
            vars["reasonParticipation"] = self._currentUser.getRegistrantById(self._conf.getId()).getReasonParticipation()
        return vars

class WConfRegFormSessionsBase(wcomponents.WTemplated):

    def __init__(self, conf, currentUser):
        self._conf = conf
        self._currentUser = currentUser
        self._sessionForm = self._conf.getRegistrationForm().getSessionsForm()
        self._selectedSessions = []
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._conf):
            self._selectedSessions = self._currentUser.getRegistrantById(self._conf.getId()).getSessionList()

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self._sessionForm.getTitle()
        vars["description"] = self._sessionForm.getDescription()
        return vars

class WConfRegFormSessionsDisplay(WConfRegFormSessionsBase):

    def _getSessionsHTML(self, sessions):
        if sessions.getSessionList() == []:
            html =  _("""--_("None selected")--""")
        else:
            html = []
            for ses in sessions.getSessionList(True):
                selected = ""
                if ses in self._selectedSessions:
                    selected = "selected"
                html.append("""
                        <input type="checkbox" name="sessionIds" value="%s" %s>%s
                        """%(ses.getId(), selected, ses.getTitle()) )
            html = "<br>".join(html)
        return html

    def getVars(self):
        vars = WConfRegFormSessionsBase.getVars( self )
        vars ["sessions"] = self._getSessionsHTML(self._sessionForm)
        return vars

class WConfRegFormSessions2PrioritiesDisplay(WConfRegFormSessionsBase):

    def _getSessionsHTML(self, sessions, selectName, sessionValue):
        selected = ""
        if sessionValue is None:
            selected = "selected"
        html = [ _("""<select name="%s">
                        <option value="nosession" %s>--_("None selected")--</option>""")%(selectName, selected)]
        for ses in sessions.getSessionList(True):
            selected = ""
            if ses == sessionValue:
                selected = "selected"
            html.append("""
                    <option value="%s" %s>%s</option>
                    """%(ses.getId(), selected, ses.getTitle()) )
        html = """%s</select>"""%("".join(html))
        return html

    def getVars(self):
        vars = WConfRegFormSessionsBase.getVars( self )
        ses1 = None
        if len(self._selectedSessions)>0:
            ses1 = self._selectedSessions[0]
        vars ["sessions1"] = self._getSessionsHTML(self._sessionForm, "session1", ses1)
        ses2 = None
        if len(self._selectedSessions)>1:
            ses2 = self._selectedSessions[1]
        vars["sessions2"] = self._getSessionsHTML(self._sessionForm, "session2", ses2)
        return vars


def cmpSessionByStartDateThenTitle(x, y):
    if cmp(x.getStartDate(),y.getStartDate()):
        return cmp(x.getStartDate(),y.getStartDate())
    else:
        return cmp(x.getTitle(),y.getTitle())

class WConfRegFormSessionsAllDisplay(WConfRegFormSessionsBase):

    def _getSessionsHTML(self):
        html=[]
        sessionList = self._sessionForm.getSessionList()
        sessionList.sort(cmpSessionByStartDateThenTitle)
        for session in sessionList :
            selected=""
            if session in self._selectedSessions:
                selected=" checked"
            html.append("""<input type="checkbox" name="sessions" value="%s"%s>%s"""%(session.getId(), selected, session.getTitle()) )
        return "<br>".join(html)

    def getVars(self):
        vars = WConfRegFormSessionsBase.getVars( self )
        vars ["sessions"] = self._getSessionsHTML()
        return vars

class WConfRegFormAccommodationDisplay(wcomponents.WTemplated):

    def __init__(self, conf, currentUser):
        self._conf = conf
        self._accommodation = self._conf.getRegistrationForm().getAccommodationForm()
        self._currentUser = currentUser

    def _getDatesHTML(self, name, currentDate, startDate=None, endDate=None):
        if name=="arrivalDate":
            dates = self._accommodation.getArrivalDates()
        elif name=="departureDate":
            dates = self._accommodation.getDepartureDates()
        else:
            dates = []
            curDate = startDate = self._conf.getStartDate() - timedelta(days=1)
            endDate = self._conf.getEndDate() + timedelta(days=1)
            while curDate <= endDate:
                dates.append(curDate)
                curDate += timedelta(days=1)
        selected = ""
        if currentDate is None:
            selected = "selected"
        html = [ _("""
                <select name="%s">
                <option value="nodate" %s>--_("select a date")--</option>
                """)%(name, selected)]
        for date in dates:
            selected = ""
            if currentDate is not None and currentDate.strftime("%d-%B-%Y") == date.strftime("%d-%B-%Y"):
                selected = "selected"
            html.append("""
                        <option value=%s %s>%s</option>
                        """%(quoteattr(str(date.strftime("%d-%m-%Y"))), selected, date.strftime("%d-%B-%Y")))
        html.append("</select>")
        return "".join(html)

    def _getAccommodationTypesHTML(self, currentAccoType):
        html=[]
        for atype in self._accommodation.getAccommodationTypesList():
            if not atype.isCancelled():
                if atype.getPlacesLimit() <= 0 or atype.hasAvailablePlaces():
                    selected = ""
                    if currentAccoType == atype:
                        selected = "checked=\"checked\""
                    placesLeft = ""
                    if atype.getNoPlacesLeft() > 0:
                        placesLeft = " <font color='green'><i>[%s place(s) left]</i></font>"%atype.getNoPlacesLeft()
                    html.append("""<tr>
                                        <td align="left" style="padding-left:10px"><input type="radio" name="accommodationType" value="%s" %s>%s%s</td>
                                    </tr>
                                """%(atype.getId(), selected, atype.getCaption(), placesLeft ) )
                else:
                    html.append("""<tr>
                                     <td align="left" style="padding-left:10px">&nbsp;&nbsp;&nbsp;<b>-</b> %s <font color="red">\
                                     (no places left)</font></td>
                                   </tr>
                        """%(atype.getCaption() ) )
            else:
                html.append( _("""<tr>
                                 <td align="left" style="padding-left:10px">&nbsp;&nbsp;&nbsp;<b>-</b> %s <font color="red">( _("not available at present") )</font></td>
                               </tr>
                            """)%(atype.getCaption() ) )
        if currentAccoType is not None and currentAccoType.isCancelled() and currentAccoType not in self._accommodation.getAccommodationTypesList():
            html.append( _("""<tr>
                                <td align="left" style="padding-left:10px">&nbsp;&nbsp;&nbsp;<b>-</b> %s <font color="red">( _("not available at present") )</font></td>
                            </tr>
                        """)%(currentAccoType.getCaption() ) )
        return "".join(html)


    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        currentArrivalDate = None
        currentDepartureDate = None
        currentAccoType = None
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._conf):
            registrant = self._currentUser.getRegistrantById(self._conf.getId())
            acco = registrant.getAccommodation()
            currentArrivalDate = None
            currentDepartureDate = None
            currentAccoType = None
            if acco is not None:
                currentArrivalDate = acco.getArrivalDate()
                currentDepartureDate = acco.getDepartureDate()
                currentAccoType = acco.getAccommodationType()
        vars["title"] = self._accommodation.getTitle()
        vars["description"] = self._accommodation.getDescription()
        vars["arrivalDate"] = self._getDatesHTML("arrivalDate", currentArrivalDate)
        vars["departureDate"] = self._getDatesHTML("departureDate", currentDepartureDate)
        vars["accommodationTypes"] = self._getAccommodationTypesHTML(currentAccoType)
        return vars

class WConfRegFormSocialEventDisplay(wcomponents.WTemplated):

    def __init__(self, conf, currentUser):
        self._conf = conf
        self._socialEvent = self._conf.getRegistrationForm().getSocialEventForm()
        self._currentUser = currentUser

    def _getSocialEventsHTML(self, socialEvents=[]):
        html=[]
        for se in self._socialEvent.getSocialEventList(True):
            if not se.isCancelled():
                checked = ""
                for ser in socialEvents:
                    if se == ser.getSocialEventItem():
                        se = ser
                        checked = "checked=\"checked\""
                        break
                optList = []
                for i in range(1, se.getMaxPlacePerRegistrant()+1):
                    selected = ""
                    if isinstance(se, registration.SocialEvent) and i == se.getNoPlaces():
                        selected = " selected"
                    optList.append("""<option value="%s"%s>%s"""%(i, selected, i))
                if len(optList)>0:
                    optList.insert(0, """<select name="places-%s">"""%se.getId())
                    optList.append("</select>")
                seItem=se
                if isinstance(se, registration.SocialEvent):
                    seItem = se.getSocialEventItem()
                placesLeft = ""
                if seItem.getPlacesLimit() > 0:
                    placesLeft = " <font color='green'><i>[%s place(s) left]</i></font>"%seItem.getNoPlacesLeft()
                inputType="checkbox"
                if self._socialEvent.getSelectionTypeId() == "unique":
                    inputType="radio"
                html.append("""<tr>
                                    <td align="left" nowrap style="padding-left:10px"><input type="%s" name="socialEvents" value="%s" %s>%s&nbsp;&nbsp;
                                    </td>
                                    <td width="100%%" align="left">
                                       %s%s
                                    </td>
                                </tr>
                            """%(inputType, se.getId(), checked, se.getCaption(), "".join(optList), placesLeft ) )
            else:
                cancelledReason = ""
                if se.getCancelledReason().strip():
                    cancelledReason = "(%s)"%se.getCancelledReason().strip()
                html.append("""<tr>
                                        <td align="left" colspan="4" nowrap style="padding-left:10px">&nbsp;&nbsp;&nbsp;<b>-</b> %s <font color="red">%s</font></td>
                                    </tr>
                                """%(se.getCaption(), cancelledReason ) )
        for se in socialEvents:
            if se.isCancelled and se.getSocialEventItem() not in self._socialEvent.getSocialEventList():
                cancelledReason = ""
                if se.getCancelledReason().strip():
                    cancelledReason = "(%s)"%se.getCancelledReason().strip()
                html.append("""<tr>
                                    <td align="left" colspan="4" nowrap style="padding-left:10px">&nbsp;&nbsp;&nbsp;<b>-</b> %s <font color="red">%s</font></td>
                                </tr>
                            """%(se.getCaption(), cancelledReason ) )
        return "".join(html)


    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        socialEvents = []
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._conf):
            registrant = self._currentUser.getRegistrantById(self._conf.getId())
            socialEvents = registrant.getSocialEvents()
        vars["title"] = self._socialEvent.getTitle()
        vars["description"] = self._socialEvent.getDescription()
        vars["intro"] =  self._socialEvent.getIntroSentence()
        vars["socialEvents"] = self._getSocialEventsHTML(socialEvents)
        return vars

class WConfRegFormFurtherInformationDisplay(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        fi = self._conf.getRegistrationForm().getFurtherInformationForm()
        vars["title"] = fi.getTitle()
        vars["content"] = fi.getContent()
        return vars

class WPRegFormInactive( conferences.WPConferenceDefaultDisplayBase ):

    def _getBody( self, params ):
        wc = WConfRegFormDeactivated()
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

class WConfRegFormDeactivated(wcomponents.WTemplated):
    pass

class WPRegistrationFormAlreadyRegistered( conferences.WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NERegistrationFormDisplay

    def _getBody( self, params ):
        wc = WConfRegistrationFormAlreadyRegistered( self._conf )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

class WConfRegistrationFormAlreadyRegistered(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

class WPRegistrationFormCreationDone( conferences.WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NERegistrationFormDisplay

    def __init__(self, rh, conf, reg):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant=reg

    def _getBody( self, params ):
        wc = WConfRegistrationFormCreationDone( self._registrant )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)



class WConfRegistrationFormCreationDone(wcomponents.WTemplated):

    def __init__( self, registrant ):
        self._registrant = registrant
        self._conf = self._registrant.getConference()

    def _getSessionsHTML(self):
        regForm = self._conf.getRegistrationForm()
        sessions = self._registrant.getSessionList()
        if regForm.getSessionsForm().isEnabled():
            if regForm.getSessionsForm().getType() == "2priorities":
                session1 = _("""<font color=\"red\">--_("not selected")--</font>""")
                session2 = "-- not selected --"
                if len(sessions) > 0:
                    session1 = sessions[0].getTitle()
                    if sessions[0].isCancelled():
                        session1 = _("""%s <font color=\"red\">( _("cancelled") )""")%session1
                if len(sessions) > 1:
                    session2 = sessions[1].getTitle()
                    if sessions[1].isCancelled():
                        session2 =  _("""%s <font color=\"red\">( _("cancelled") )""")%session2
                text=  _("""
                        <table>
                          <tr>
                            <td align="right"><b> _("First Priority"):</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b> _("Other option"):</b></td>
                            <td align="left">%s</td>
                          </tr>
                        </table>
                        """)%(session1, session2)
                return  _("""
                        <tr>
                          <td style="color:black"><b>%s</b></td>
                          <td bgcolor="white" class="blacktext">%s</td>
                        </tr>
                        <tr>
                          <td colspan="4" style="border-top:2px solid black">&nbsp;</td>
                        </tr>
                        """)%(regForm.getSessionsForm().getTitle(),text)
            if regForm.getSessionsForm().getType() == "all":
                sessionList =  _("""<font color=\"red\">--_("not selected")--</font>""")
                if len(sessions) > 0:
                    sessionList=["<ul>"]
                    for ses in sessions:
                        sesText = "<li>%s</li>"%ses.getTitle()
                        if ses.isCancelled():
                            sesText =  _("""<li>%s <font color=\"red\">( _("cancelled") )</font></li>""")%ses.getTitle()
                        sessionList.append(sesText)
                    sessionList.append("</ul>")
                    sessionList="".join(sessionList)
                text= """
                        <table>
                          <tr>
                            <td align="left">%s</td>
                          </tr>
                        </table>
                        """%(sessionList)
                return  _("""
                        <tr>
                          <td style="color:black"><b>%s</b></td>
                          <td bgcolor="white" class="blacktext">%s</td>
                        </tr>
                        <tr>
                          <td colspan="4" style="border-top:2px solid black">&nbsp;</td>
                        </tr>
                        """)%(regForm.getSessionsForm().getTitle(), text)
        return ""

    def _getAccommodationHTML(self):
        regForm = self._conf.getRegistrationForm()
        if regForm.getAccommodationForm().isEnabled():
            accommodation = self._registrant.getAccommodation()
            accoType = _("""<font color=\"red\">--_("not selected")--</font>""")
            cancelled = ""
            if accommodation is not None and accommodation.getAccommodationType() is not None:
                accoType = accommodation.getAccommodationType().getCaption()
                if accommodation.getAccommodationType().isCancelled():
                    cancelled = """<font color=\"red\">( """+_("disabled")+""" )</font>"""
            arrivalDate = """<font color=\"red\">--""" + _("not selected") + """--</font>"""
            if accommodation is not None and accommodation.getArrivalDate() is not None:
                arrivalDate = accommodation.getArrivalDate().strftime("%d-%B-%Y")
            departureDate = """<font color=\"red\">--""" + _("not selected") + """--</font>"""
            if accommodation is not None and accommodation.getDepartureDate() is not None:
                departureDate = accommodation.getDepartureDate().strftime("%d-%B-%Y")
            accoTypeHTML = ""
            if regForm.getAccommodationForm().getAccommodationTypesList() !=[]:
                accoTypeHTML = """
                          <tr>
                            <td align="right"><b>Accommodation type:</b></td>
                            <td align="left">%s %s</td>
                          </tr>"""%(accoType, cancelled)

            text = _("""
                        <table>
                          <tr>
                            <td align="right"><b> _("Arrival date"):</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b> _("Departure date"):</b></td>
                            <td align="left">%s</td>
                          </tr>
                          %s
                        </table>
                        """)%(arrivalDate, departureDate, accoTypeHTML)
            return _("""
                    <tr>
                      <td style="color:black"><b> _("Accommodation")</b></td>
                      <td bgcolor="white" class="blacktext">%s</td>
                    </tr>
                    <tr>
                      <td colspan="4" style="border-top:2px solid black">&nbsp;</td>
                    </tr>
                    """)%(text)
        return ""

    def _getSocialEventsHTML(self):
        regForm = self._conf.getRegistrationForm()
        text = ""
        if regForm.getSocialEventForm().isEnabled():
            socialEvents = self._registrant.getSocialEvents()
            r = []
            for se in socialEvents:
                cancelled = ""
                if se.isCancelled():
                    cancelled =  _("""<font color=\"red\">( _("cancelled") )</font>""")
                    if se.getCancelledReason().strip():
                        cancelled =  _("""<font color=\"red\">( _("cancelled"): %s)</font>""")%se.getCancelledReason().strip()
                r.append( _("""
                            <tr>
                              <td align="left">%s <b>[%s  _("place(s) needed")]</b> %s</td>
                            </tr>
                         """)%(se.getCaption(), se.getNoPlaces(), cancelled))
            if r == []:
                text =  _("""--  _("no social events selected") --""")
            else:
                text = """
                        <table>
                          %s
                        </table>
                        """%("".join(r))
            text =  _("""
                    <tr>
                      <td style="color:black"><b>%s</b></td>
                      <td bgcolor="white" class="blacktext">%s</td>
                    </tr>
                    <tr>
                      <td colspan="4" style="border-top:2px solid black">&nbsp;</td>
                    </tr>
                    """)%(regForm.getSocialEventForm().getTitle(), text)
        return text

    def _getReasonParticipationHTML(self):
        regForm = self._conf.getRegistrationForm()
        if regForm.getReasonParticipationForm().isEnabled():
            return  _("""
                    <tr>
                      <td style="color:black"><b> _("Reason for participation")</b></td>
                      <td bgcolor="white" class="blacktext">%s</td>
                    </tr>
                    <tr>
                      <td colspan="4" style="border-top:2px solid black">&nbsp;</td>
                    </tr>
                    """)%(self.htmlText( self._registrant.getReasonParticipation() ))
        return ""

    def _getMiscInfoItemsHTML(self, gsf):
        regForm = self._conf.getRegistrationForm()
        miscGroup=self._registrant.getMiscellaneousGroupById(gsf.getId())
        html=["""<table>"""]
        #jmf
        for f in gsf.getSortedFields():
            miscItem=None
            price=""
            currancy=""
            if miscGroup is not None:
                miscItem=miscGroup.getResponseItemById(f.getId())
            v= _("""--_("no value selected")--""")
            if f.isBillable():
                price=f.getPrice()
                currancy=regForm.getCurrency()
            if miscItem is not None:
                v=miscItem.getValue()
                if miscItem.isBillable():
                    price=miscItem.getPrice()
                    currancy=regForm.getCurrency()
            if v is None : v=""
            html.append("""
                    <tr>
                       <td align="right"><b>%s:</b></td>
                       <td align="left">%s</td>
                       <td align="right">%s&nbsp;&nbsp;%s</td>
                    </tr>
                    """%(f.getCaption(),v,price,currancy) )
        if miscGroup is not None:
            for miscItem in miscGroup.getResponseItemList():
                    f=gsf.getFieldById(miscItem.getId())
                    if f is None:
                        html.append( _("""
                                    <tr>
                                       <td align="right" nowrap><b>%s:</b></td>
                                       <td align="left">%s <font color="red">( _("cancelled") )</font></td>
                                    </tr>
                                    """)%(miscItem.getCaption(), miscItem.getValue()) )
        if len(html)==1:
            html.append( _("""
                        <tr><td><font color="black"><i>--_("No fields")--</i></font></td></tr>
                        """))
        html.append("</table>")
        return "".join(html)

    def _getMiscInfoItemsHTMLBilllable(self, gsf,total):
        regForm = self._conf.getRegistrationForm()
        miscGroup=self._registrant.getMiscellaneousGroupById(gsf.getId())
        html=[""""""]
        if miscGroup is not None:
            for miscItem in miscGroup.getResponseItemList():
                _billlable=False
                price=0.0
                quantity=0
                value=""
                caption=miscItem.getCaption()
                currency=miscItem.getCurrency()
                if miscItem is not None:
                    v=miscItem.getValue()
                    if miscItem.isBillable():
                        _billlable=miscItem.isBillable()
                        #caption=miscItem.getValue()
                        value=miscItem.getValue()
                        price=string.atof(miscItem.getPrice())
                        quantity=miscItem.getQuantity()
                        total["value"]+=price*quantity
                if value != "":
                    value=":%s"%value
                if(quantity>0):
                    html.append("""
                            <tr>
                               <td ><b>%i</b></td>
                               <td>%s:%s%s</td>
                               <td align="right" style="padding-right:10px" nowrap >%s</td>
                               <td align="right"nowrap >%s&nbsp;&nbsp;%s</td>
                            </tr>
                            """%(quantity,gsf.getTitle(),caption,value,price,price*quantity,currency) )
        return "".join(html)


    def _getMiscellaneousInfoHTML(self, gsf):
        html=[]
        if gsf.isEnabled():
            html.append("""
                <tr>
                  <td style="color:black"><b>%s</b></td>
                  <td bgcolor="white" class="blacktext">%s</td>
                </tr>
                <tr>
                  <td colspan="4" style="border-top:2px solid black">&nbsp;</td>
                </tr>
                """%(gsf.getTitle(), self._getMiscInfoItemsHTML(gsf) ) )
        return "".join(html)

    def _getPaymentInfo(self):
        regForm = self._conf.getRegistrationForm()
        modPay=self._conf.getModPay()
        html=[]
        if modPay.isActivated() and self._registrant.doPay():
            total={}
            total["value"]=0
            html.append( _(""" <tr><td colspan="2"><table width="100%%">
                            <tr>
                            <tr><td colspan="4" class="title"><b>_("Payment summary")</b></td></tr>
                            <tr>
                                <td style="color:black"><b> _("Quantity")</b></td>
                                <td style="color:black"><b> _("Item")</b></td>
                                <td style="color:black;padding-right:10px" nowrap ><b>_("Unit Price")</b></td>
                                <td style="color:black"><b> _("Cost")</b></td>
                            </tr>
                        """))
            for gsf in self._registrant.getMiscellaneousGroupList():
                    html.append("""<tr>%s</tr>"""%(self._getMiscInfoItemsHTMLBilllable(gsf,total)))

            url=urlHandlers.UHConfRegistrationFormconfirmBooking.getURL(self._registrant)
            url.addParam("registrantId", self._registrant.getId())
            url.addParam("confId", self._conf.getId())

            condChecking=""
            if modPay.hasPaymentConditions():
                condChecking="""<!--<tr><td>Please ensure that you have read the terms and conditions before continuing.</td></tr>
                                <tr><td>I have read and agree to the terms and conditions and understand that by confirming this order I will be entering into a binding transaction.</td></tr>-->
                                <tr>
                                    <td><input type="checkbox" name="conditions"/>I have read and accept the terms and conditions and understand that by confirming this order I will be entering into a binding transaction (<a href="#" onClick="window.open('%s','Conditions','width=400,height=200,resizable=yes,scrollbars=yes'); return false;">Terms and conditions</a>).</td>
                                </tr>
                                <tr>
                                    <td><br></td>
                                </tr>"""%str(urlHandlers.UHConfRegistrationFormConditions.getURL(self._conf))

            html.append( _("""
                            <tr>&nbsp;</tr>
                            <tr>
                               <td ><b> _("TOTAL")</b></td>
                               <td></td>
                               <td></td>
                               <td align="right"nowrap>%s&nbsp;&nbsp;%s</td>
                            </tr>
                            <form name="epay" action="%s" method="POST">
                            <tr>
                              <table width="100%%">

                                <tr><td>&nbsp;</td></tr>
                                %s
                                <tr>
                                  <td align="right" nowrap><input type="submit" value="Next ->" onclick="return checkConditions()" ></td>
                                </tr>
                               </table>
                            </tr>
                            </form> <td  colspan="4" style="border-top:2px solid black">&nbsp;</td></tr>
                            </table></td></tr>
                            """)%(total["value"],regForm.getCurrency(),url,condChecking))
        return "".join(html)

    def _getPDInfoHTML(self):
        personalData = self._conf.getRegistrationForm().getPersonalData()
        sortedKeys = personalData.getSortedKeys()
        html = ""
        for key in sortedKeys:
            pdfield = personalData.getDataItem(key)
            fieldTitle = pdfield.getName()
            fieldValue = ""
            if key == "title":
                fieldValue = self.htmlText( self._registrant.getTitle() )
            elif key == "firstName":
                fieldValue = self.htmlText( self._registrant.getFirstName() )
            elif key == "surname":
                fieldValue = self.htmlText( self._registrant.getFamilyName() )
            elif key == "position":
                fieldValue = self.htmlText( self._registrant.getPosition() )
            elif key == "institution":
                fieldValue = self.htmlText( self._registrant.getInstitution() )
            elif key == "address":
                fieldValue = self.htmlText( self._registrant.getAddress() )
            elif key == "city":
                fieldValue = self.htmlText( self._registrant.getCity() )
            elif key == "country":
                fieldValue = self.htmlText( self._registrant.getCountry() )
            elif key == "phone":
                fieldValue = self.htmlText( self._registrant.getPhone() )
            elif key == "email":
                fieldValue = self.htmlText( self._registrant.getEmail() )
            elif key == "fax":
                fieldValue = self.htmlText( self._registrant.getFax() )
            elif key == "personalHomepage":
                fieldValue = self.htmlText( self._registrant.getPersonalHomepage() )
            if pdfield.isEnabled():
                html += """
                            <tr>
                              <td style="color:black"><b>%s</b></td>
                              <td bgcolor="white" class="blacktext">%s</td>
                            </tr>""" % (fieldTitle,fieldValue)
        return html

    def _getFormSections(self):
        sects = []
        regForm = self._conf.getRegistrationForm()
        for formSection in regForm.getSortedForms():
            if formSection.getId() == "reasonParticipation":
                sects.append(self._getReasonParticipationHTML())
            elif formSection.getId() == "sessions":
                sects.append(self._getSessionsHTML())
            elif formSection.getId() == "accommodation":
                sects.append(self._getAccommodationHTML())
            elif formSection.getId() == "socialEvents":
                sects.append(self._getSocialEventsHTML())
            elif formSection.getId() == "furtherInformation":
                pass
            else:
                sects.append(self._getMiscellaneousInfoHTML(formSection))
        return "".join(sects)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["id"] = self._registrant.getId()
        vars["pdfields"] = self._getPDInfoHTML()
        vars["registrationDate"] = _("""--_("date unknown")--""")
        if self._registrant.getRegistrationDate() is not None:
            vars["registrationDate"] = self._registrant.getAdjustedRegistrationDate().strftime("%d-%B-%Y %H:%M")
        vars["dataModificationURL"] = quoteattr(str(urlHandlers.UHRegistrantDataModification.getURL(self._registrant)))
        vars["otherSections"] = self._getFormSections()
        vars["paymentInfo"]  = self._getPaymentInfo()
        vars["epaymentAnnounce"] = ""
        if self._conf.getModPay().isActivated() and self._registrant.doPay():
            vars["epaymentAnnounce"] = """<br><font color="black">Please proceed to the <b>payment of your order</b> (by using the "Next" button down this page). You will then receive the payment details.</font>"""
        return vars

class WPRegistrationFormconfirmBooking( conferences.WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NERegistrationFormDisplay

    def __init__(self, rh, conf, reg):
        conferences.WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._registrant=reg

    def _getBody( self, params ):
        wc = WRegistrationFormconfirmBooking( self._registrant )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

class WRegistrationFormconfirmBooking(wcomponents.WTemplated):
    def __init__( self, registrant ):
        self._registrant = registrant
        self._conf = self._registrant.getConference()
        self.modPay = self._conf.getModPay()

    def _getModPayHTML(self):
        forms=""
        html=[]

        regForm = self._conf.getRegistrationForm()
        for m in self.modPay.getSortedModPay():
            if m.isEnabled():
                forms=forms+"""
                <tr>
                <td></td>
                <td><b>%s</b></td>
                %s
                </tr>
                """%(m.getTitle(),m.getFormHTML(self._registrant.getTotal(),regForm.getCurrency(),self._conf,self._registrant))
        #forms=forms+"</table>"

        if forms:
            html.append( _("""
                    <tr>&nbsp;</tr>
                    <tr>
                    <td colspan="4" style="color:black"><b>Pay by credit card online with:</b></td>
                    </tr>
                    <tr>
                    %s
                    </tr>
                    <tr><td  colspan="4" style="border-top:2px solid black">&nbsp;</td></tr>
                """)%"".join(forms))
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["modPay"]=self._getModPayHTML()
        vars["modPayDetails"] = self.modPay.getPaymentDetails()
        return vars

class WPRegistrationFormSignIn( conferences.WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NERegistrationFormDisplay

    def _getBody( self, params ):
        urlCreateAccount=urlHandlers.UHConfUserCreation.getURL( self._conf )
        urlCreateAccount.addParam("returnURL",urlHandlers.UHConfRegistrationFormDisplay.getURL(self._conf))
        p = { \
    "postURL": urlHandlers.UHConfSignIn.getURL( self._conf ), \
    "returnURL": urlHandlers.UHConfRegistrationFormDisplay.getURL(self._conf), \
    "createAccountURL": urlCreateAccount, \
    "forgotPassordURL": urlHandlers.UHConfSendLogin.getURL( self._conf ), \
    "login": "", \
    "msg": "" }
        wc = WConfRegistrationFormSignIn( self._conf, p )
        return wc.getHTML(p)

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._newRegFormOpt)

class WConfRegistrationFormSignIn(wcomponents.WTemplated):

    def __init__(self, conf, p):
        self._conf = conf
        self._params = p

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        wc = wcomponents.WSignIn()
        vars["signIn"] = wc.getHTML(self._params)
        return vars

class WPRegistrationFormModify( conferences.WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NERegistrationFormModify

    def _getBody( self, params ):
        wc = WConfRegistrationFormModify( self._conf, self._rh._getUser() )
        pars = {"menuStatus":self._rh._getSession().getVar("menuStatus") or "open"}
        return wc.getHTML(pars)

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._viewRegFormOpt)

class WConfRegistrationFormModify(WConfRegistrationFormDisplay):

    def getVars(self):
        vars = WConfRegistrationFormDisplay.getVars( self )
        registrant = self._currentUser.getRegistrantById(self._conf.getId())
        vars["postURL"] = quoteattr(str(urlHandlers.UHConfRegistrationFormPerformModify.getURL(self._conf)))
        return vars

class WPRegistrationFormFull( conferences.WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NERegistrationFormDisplay

    def _getBody( self, params ):
        wc = WConfRegistrationFormFull( self._conf )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

class WConfRegistrationFormFull(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["limit"] = self._conf.getRegistrationForm().getUsersLimit()
        return vars

class WPRegistrationFormClosed( conferences.WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NERegistrationFormDisplay

    def _getBody( self, params ):
        wc = WConfRegistrationFormClosed( self._conf )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

class WConfRegistrationFormClosed(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        regForm=self._conf.getRegistrationForm()
        vars["title"]= _("Impossible to register")
        vars["msg"]= _("No period for registration")
        if nowutc()<regForm.getStartRegistrationDate():
            vars["title"]= _("Registration is not open yet")
            vars["msg"]= _("Sorry but the registration is not open yet:")
        elif regForm.getEndRegistrationDate()<nowutc():
            vars["title"]= _("Registration is closed")
            vars["msg"]= _("Sorry but the registration is now closed:")
        vars["startDate"] = self._conf.getRegistrationForm().getStartRegistrationDate().strftime("%A %d %B %Y")
        vars["endDate"] = self._conf.getRegistrationForm().getEndRegistrationDate().strftime("%A %d %B %Y")
        return vars

class WPRegistrationFormConditions(WPBase):

    def __init__(self, rh, conf):
        WPBase.__init__(self, rh)
        self._conf = conf

    def _display( self, params ):
        wc = WConfRegistrationFormConditions( self._conf )
        return wc.getHTML()

class WConfRegistrationFormConditions(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["conditions"]=self._conf.getModPay().getConditions()
        return vars
