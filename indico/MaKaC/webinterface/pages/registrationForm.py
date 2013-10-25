# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
from flask import session, request
from indico.web.flask.util import url_for

from MaKaC.webinterface.pages.conferences import WConfDisplayBodyBase
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.navigation as navigation
from MaKaC.registration import LabelInput
import string
from MaKaC import registration
from MaKaC.webinterface import wcomponents
from xml.sax.saxutils import quoteattr
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from indico.core import config as Configuration
from datetime import timedelta
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.webinterface.common.countries import CountryHolder
from MaKaC.webinterface.pages.base import WPBase
from indico.core.config import Config
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from MaKaC.registration import RadioGroupInput, TextareaInput

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
        self._tabETicket = self._tabCtrl.newTab("eticket", _("e-ticket"),
                url_for("event_mgmt.confModifETicket", self._conf))

        self._setActiveTab()

        if not self._conf.hasEnabledSection("regForm"):
            self._tabRegFormSetup.disable()
            self._tabRegistrants.disable()
            self._tabEPay.disable()
            self._tabRegistrationPreview.disable()
            self._tabETicket.disable()

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
            if isinstance(gs, registration.GeneralSectionForm) and not gs.isRequired():
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
            if not isinstance(gs, registration.GeneralSectionForm) or not gs.isRequired():
                toggleLink = """<a href=%s><img src="%s" alt="%s" class="imglink"></a>""" % (quoteattr(str(urlStatus)), img, text)
            else:
                toggleLink = ""
            html.append("""
                        <tr>
                        <td>%s</td>
                        <td>%s&nbsp;%s<a href=%s>%s</a></td>
                        </tr>
                        """%(toggleLink, selbox, checkbox, quoteattr(str(urlModif)), gs.getTitle()) )
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
                        """%(st.getId(), quoteattr(str(urlStatus)), st.getCaption().strip() or  i18nformat("""-- [%s]  _("status with no name") --""")%st.getId()) )
        if html == []:
            html.append("""<tr><td style="padding-left:20px"><ul><li>%s</li></ul><br>%s</td></tr>""" % (_("No statuses defined yet."), _("You can use this option in order to create general statuses you will be able to use afterwards in the list of registrants. For instance, you can create a status \"paid\" in order to check if someone has paid or not.")))
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
            vars["activated"] = True
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
            vars["extraTimeAmount"] = regForm.getEndExtraTimeAmount()
            vars["extraTimeUnit"] = regForm.getEndExtraTimeUnit()
            d = ""
            if regForm.getModificationEndDate() is not None:
                d = regForm.getModificationEndDate().strftime("%A %d %B %Y")
            vars["modificationEndDate"]=d
            vars["announcement"] = regForm.getAnnouncement()
            vars["disabled"] = ""
            vars["contactInfo"] = regForm.getContactInfo()
            vars["usersLimit"] = i18nformat("""--_("No limit")--""")
            if regForm.getUsersLimit() > 0:
                vars["usersLimit"] = regForm.getUsersLimit()
            vars["title"] = regForm.getTitle()
            vars["notification"] = i18nformat("""
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
                                    """)%(", ".join(regForm.getNotification().getToList()) or i18nformat("""--_("no TO list")--"""), ", ".join(regForm.getNotification().getCCList()) or i18nformat("""--_("no CC list")--"""))
            vars["mandatoryAccount"] =  _("Yes")
            if not regForm.isMandatoryAccount():
                vars["mandatoryAccount"] =  _("No")
            vars["notificationSender"] = regForm.getNotificationSender()
            vars["sendRegEmail"] = _("Yes")
            if not regForm.isSendRegEmail():
                vars["sendRegEmail"] = _("No")
            vars["sendReceiptEmail"] = _("Yes")
            if not regForm.isSendReceiptEmail():
                vars["sendReceiptEmail"] = _("No")
            vars["sendPaidEmail"] = _("Yes")
            if not regForm.isSendPaidEmail():
                vars["sendPaidEmail"] = _("No")
        else:
            vars["activated"] = False
            vars["changeTo"] = "True"
            vars["status"] =_("DISABLED")
            vars["changeStatus"] = _("ENABLE")
            vars["startDate"] = ""
            vars["endDate"] = ""
            vars["extraTimeAmount"] = ""
            vars["extraTimeUnit"] = ""
            vars["modificationEndDate"]=""
            vars["announcement"] = ""
            vars["disabled"] = 'disabled = "disabled"'
            vars["contactInfo"] = ""
            vars["usersLimit"] = ""
            vars["title"] = ""
            vars["notification"] = ""
            vars["mandatoryAccount"] = ""
            vars["notificationSender"] = ""
            vars["sendRegEmail"] = ""
            vars["sendReceiptEmail"] = ""
            vars["sendPaidEmail"] = ""
        vars["sections"] = self._getSectionsHTML()
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
        vars["announcement"] = regForm.getAnnouncement()
        vars["contactInfo"] = regForm.getContactInfo()
        vars["usersLimit"] = regForm.getUsersLimit()
        vars["title"] = regForm.getTitle()
        vars["toList"] = ", ".join(regForm.getNotification().getToList())
        vars["ccList"] = ", ".join(regForm.getNotification().getCCList())
        vars["mandatoryAccount"]=""
        if regForm.isMandatoryAccount():
            vars["mandatoryAccount"]= "CHECKED"
        vars["notificationSender"] = regForm.getNotificationSender()
        vars["sendRegEmail"] = ""
        vars["sendReceiptEmail"] = ""
        vars["sendPaidEmail"] = ""
        if regForm.isSendRegEmail():
            vars["sendRegEmail"] = "CHECKED"
        if regForm.isSendReceiptEmail():
            vars["sendReceiptEmail"] = "CHECKED"
        if regForm.isSendPaidEmail():
            vars["sendPaidEmail"] = "CHECKED"
        vars["extraTimeAmount"] = regForm.getEndExtraTimeAmount()
        vars["extraTimeUnit"] = regForm.getEndExtraTimeUnit()
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
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return "nothing"


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
            html =  i18nformat("""--_("None selected")--""")
        else:
            html = []
            for ses in sessions.getSessionList(True):
                billable = ""
                if ses.isBillable():
                    billable = " <i>[billable: %s]</i>" % ses.getPrice()
                cancelled = ""
                if ses.isCancelled():
                    cancelled = " <font color=\"red\">(cancelled)</font>"
                url = urlHandlers.UHConfModifRegFormSessionItemModify.getURL(ses)
                html.append("""
                        <input type="checkbox" name="sessionIds" value="%s"><a href=%s>%s</a>%s%s
                        """%(ses.getId(), quoteattr(str(url)), ses.getTitle(), billable, cancelled) )
            html = "<br>".join(html)
        return html

    def _getSessionFormTypeHTML(self, sessions):
        if sessions.getType()=="all":
            return  _("multiple")
        return  _("""2 choices <span style="color:red;">(session billing not possible)</span>""")

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
        html.append( i18nformat("""<option value="2priorities"%s> _("2 choices")</option>""")%selected)
        selected=""
        if sessions.getType()=="all":
            selected=" selected"
        html.append( i18nformat("""<option value="all"%s> _("multiple")</option>""")%selected)
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
            html =  i18nformat("""--  _("No sessions to add") --""")
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

class WPConfModifRegFormSessionItemModify( WPConfModifRegFormSessionsBase ):

    def __init__(self, rh, conf, sessionItem):
        WPConfModifRegFormSessionsBase.__init__(self, rh, conf)
        self._sessionItem = sessionItem

    def _getTabContent( self, params ):
        wc = WConfModifRegFormSessionItemModify(self._sessionItem)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormSessionItemPerformModify.getURL( self._sessionItem )))
            }
        return wc.getHTML(p)

class WConfModifRegFormSessionItemModify( wcomponents.WTemplated ):

    def __init__(self, sessionItem):
        self._sessionItem = sessionItem

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["caption"] = quoteattr(self._sessionItem.getCaption())
        vars["billable"] = ""
        if self._sessionItem.isBillable():
            vars["billable"] = """ checked="checked" """
        vars["price"] = self._sessionItem.getPrice()
        return vars

class WPConfModifRegFormAccommodationBase(WPConfModifRegFormSectionsBase):

    def __init__( self, rh, conference ):
        WPConfModifRegFormSectionsBase.__init__(self, rh, conference)
        self._targetSection = self._conf.getRegistrationForm().getAccommodationForm()

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", "Main", \
                urlHandlers.UHConfModifRegFormAccommodation.getURL( self._conf ) )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return  _("nothing")


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
                cancelled =  i18nformat(""" <font color=\"red\">( _("disabled") )</font>""")
            url = urlHandlers.UHConfModifRegFormAccommodationTypeModify.getURL(atype)
            limit =  i18nformat(""" <i>[ _("unlimited places") ]</i>""")
            if atype.getPlacesLimit() > 0:
                limit = " <i>[%s/%s place(s)]</i>"%(atype.getCurrentNoPlaces(), atype.getPlacesLimit())
            billable = ""
            if atype.isBillable():
                billable = " <i>[billable: %s]</i>" % atype.getPrice()
            html.append("""<tr>
                                <td align="left" style="padding-left:10px"><input type="checkbox" name="accommodationType" value="%s"><a href=%s>%s</a>%s%s%s</td>
                            </tr>
                        """%(atype.getId(), url, self.htmlText(atype.getCaption()), limit, billable, cancelled ) )
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
        vars["billable"] = ""
        if self._accoType.isBillable():
            vars["billable"] = """ checked="checked" """
        vars["price"] = self._accoType.getPrice()
        return vars

class WPConfRemoveAccommodationType(WPConfModifRegFormAccommodationBase):

    def __init__(self, rh, conf, accoTypeIds, accommodationTypes):
        WPConfModifRegFormAccommodationBase.__init__(self, rh, conf)
        self._eventType="conference"
        if self._rh.getWebFactory() is not None:
            self._eventType=self._rh.getWebFactory().getId()

        self._accoTypeIds = accoTypeIds
        self._accommodationTypes = accommodationTypes

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent( self, params ):

        pcoords = ''.join(list("<li>{0}</li>".format(s) for s in self._accommodationTypes))

        msg = {'challenge': _("Are you sure that you want to DELETE these accomodation types?"),
               'target': "<ul>{0}</ul>".format(pcoords),
               'subtext': _("Note that if you delete this accomodation, registrants who applied for it will lose their accomodation info")
               }

        wc = wcomponents.WConfirmation()
        return wc.getHTML(msg,
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
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return  _("nothing")


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
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return  _("nothing")


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
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _getTabContent( self, params ):
        return  _("nothing")


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
                cancelled =  i18nformat("""<font color=\"red\">( _("cancelled") )</font>""")
                if se.getCancelledReason().strip():
                    cancelled =  i18nformat("""<font color=\"red\">( _("disabled"): %s)</font>""")%se.getCancelledReason().strip()
            limit = " <i>[unlimited places]</i>"
            if se.getPlacesLimit() > 0:
                limit = " <i>[%s/%s place(s)]</i>"%(se.getCurrentNoPlaces(), se.getPlacesLimit())
            billable = ""
            if se.isBillable():
                perPlace = ""
                if se.isPricePerPlace():
                    perPlace = ' <acronym title="per place">pp</acronym>'
                billable = " <i>[billable: %s%s]</i>" % (se.getPrice(), perPlace)
            url = urlHandlers.UHConfModifRegFormSocialEventItemModify.getURL(se)
            html.append("""<tr>
                                <td align="left" style="padding-left:10px"><input type="checkbox" name="socialEvents" value="%s"><a href=%s>%s</a>%s%s%s</td>
                            </tr>
                        """%(se.getId(), quoteattr(str(url)), self.htmlText(se.getCaption()), limit, billable, cancelled ) )
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
        vars["billable"] = ""
        if self._socialEventItem.isBillable():
            vars["billable"] = """ checked="checked" """
        vars["pricePerPlace"] = ""
        if self._socialEventItem.isPricePerPlace():
            vars["pricePerPlace"] = """ checked="checked" """
        vars["price"] = self._socialEventItem.getPrice()
        return vars

class WPConfRemoveSocialEvent(WPConfModifRegFormSocialEventBase):

    def __init__(self, rh, conf, socialEventIds, eventNames):
        WPConfModifRegFormSocialEventBase.__init__(self, rh, conf)
        self._eventType="conference"
        self._socialEventIds = socialEventIds
        self._eventNames = eventNames
        if self._rh.getWebFactory() is not None:
            self._eventType = self._rh.getWebFactory().getId()

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent( self, params ):

        social = ''.join(list("<li>{0}</li>".format(s) for s in self._eventNames))

        msg = {'challenge': _("Are you sure that you want to DELETE these social events?"),
               'target': "<ul>{0}</ul>".format(social),
               'subtext': _("Note that if you delete a social event, registrants who applied for it will lose their social event info")
               }

        wc = wcomponents.WConfirmation()
        return wc.getHTML( msg, \
                        urlHandlers.UHConfModifRegFormSocialEventRemove.getURL( self._conf ),\
                         {"socialEvents":self._socialEventIds}, \
                        confirmButtonCaption= _("Yes"), cancelButtonCaption= _("No") )

class WPConfModifRegFormStatusesRemConfirm(WPConfModifRegFormBase):

    def __init__(self,rh,target, stids):
        WPConfModifRegFormBase.__init__(self, rh, target)
        self._statusesIds = stids

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()

        statuses = ''.join(list("<li>{0}</li>".format(self._conf.getRegistrationForm().getStatusById(s).getCaption() \
                                                          or _('-- unnamed status --')) for s in self._statusesIds))

        msg = {'challenge': _("Are you sure you want to delete the following registration statuses?"),
               'target': "<ul>{0}</ul>".format(statuses),
               'subtext': _("Please note that any existing registrants will lose this information")
               }

        url=urlHandlers.UHConfModifRegFormActionStatuses.getURL(self._conf)
        return wc.getHTML(msg,url,{"statusesIds":self._statusesIds, "removeStatuses":"1"})

class WPConfModifRegFormGeneralSectionRemConfirm(WPConfModifRegFormBase):

    def __init__(self,rh,target, gss):
        WPConfModifRegFormBase.__init__(self, rh, target)
        self._generalSections = gss

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        ssHTML=["<ul>"]

        sections = ''.join(list("<li>{0}</li>".format(self._conf.getRegistrationForm().getGeneralSectionFormById(s).getTitle()) \
                                    for s in self._generalSections))

        msg = {'challenge': _("Are you sure you want to delete the following sections of the registration form?"),
               'target': "<ul>{0}</ul>".format(sections),
               'subtext': _("Please note that any existing registrants will lose this information")
               }

        url=urlHandlers.UHConfModifRegFormActionSection.getURL(self._conf)
        return wc.getHTML(msg, url, {"sectionsIds":self._generalSections, "removeSection":"1"})

class WPConfModifRegFormGeneralSectionBase(WPConfModifRegFormSectionsBase):

    def __init__(self, rh, gs):
        WPConfModifRegFormSectionsBase.__init__(self, rh, gs.getConference())
        self._targetSection=self._generalSectionForm=gs

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab("main", _("Main"),
                                             urlHandlers.UHConfModifRegFormGeneralSection.getURL(self._targetSection))
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
        enabledBulb = Configuration.Config.getInstance().getSystemIconURL("enabledSection")
        notEnabledBulb = Configuration.Config.getInstance().getSystemIconURL("disabledSection")
        enabledText = "Click to disable"
        disabledText = "Click to enable"
        ##############
        #jmf-start
        #for f in self._generalSection.getFields():
        for f in self._generalSection.getSortedFields():
        #jmf-end
        ##############
            url = urlHandlers.UHConfModifRegFormGeneralSectionFieldModif.getURL(f)
            spec = " <b>(%s"%f.getInput().getName()
            if f.isMandatory():
                spec =  i18nformat(""" %s, _("mandatory")""")%spec
            if f.isBillable():
                spec =  i18nformat(""" %s, _("Billable") = %s""")%(spec,self.htmlText(f.getPrice()))
            if f.getPlacesLimit():
                spec =  i18nformat(""" %s, _("Places") = %s/%s""")%(spec,f.getNoPlacesLeft(),f.getPlacesLimit())

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

            chkbox = ""
            if not f.isLocked('delete'):
                chkbox = """<input type="checkbox" name="fieldsIds" value="%s">""" % f.getId()

            urlStatus = urlHandlers.UHConfModifRegFormEnablePersonalField.getURL(self._conf)
            urlStatus.addParam("sectionFormId", self._generalSection.getId())
            urlStatus.addParam("personalfield", f.getId())
            img = enabledBulb
            imgAlt = enabledText
            if f.isDisabled():
                img = notEnabledBulb
                imgAlt = disabledText

            toggle = ""
            if not f.isLocked('disable') and self._generalSection is self._generalSection.getRegistrationForm().getPersonalData():
                toggle = """<a href=%s><img src="%s" alt="%s" class="imglink"></a>""" % (quoteattr(str(urlStatus)), img, imgAlt)

            html.append("""<tr>
                                <td align="left" style="padding-left:10px">%s</td><td>%s</td><td>%s</td><td><a href=%s>%s</a>%s</td>
                            </tr>
                        """%(toggle, selbox, chkbox, url, self.htmlText(f.getCaption()),spec) )
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
        disabled = ""
        if self._generalField and self._generalField.isLocked('input'):
            disabled = """ disabled="disabled"""
        html=["""<select name="input" onchange="javascript:$E('WConfModifRegFormGeneralSectionFieldEdit').dom.submit();  $E('submitButton').dom.disabled=true; $E('cancelButton').dom.disabled=true;"%s>""" % disabled]
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
        vars["description"] = ""
        vars["mandatory"] =  """ checked="checked" """
        vars["mandatoryLocked"] = False
        #vars["billable"]= """ checked="checked" """
        #vars["price"]=""
        if self._generalField is not None:
            vars["caption"] = quoteattr(self._generalField.getCaption())
            vars["description"] = self._generalField.getDescription()
            #vars["price"]= quoteattr(self._generalField.getPrice())
            if not self._generalField.isMandatory():
                vars["mandatory"] =  ""
            vars["mandatoryLocked"] = self._generalField.isLocked('mandatory')
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
        self._fields = fields

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        fields = ''.join(list("<li>{0}</li>".format(self._generalSectionForm.getFieldById(id).getCaption() \
                                                        for s in self._fields)))

        msg = {'challenge': _("Are you sure you want to delete the following fields of the section '{0}'".format(
                        self._generalSectionForm.getTitle())),
               'target': "<ul>{0}</ul>".format(fields),
               'subtext': _("Please note that any existing registrants will lose this information")
               }

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


class WPRegistrationForm(conferences.WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NERegistrationForm

    def _getBody(self, params):
        wc = WConfRegistrationForm(self._conf, self._getAW().getUser())
        return wc.getHTML()

    def _defineSectionMenu(self):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)


class WConfRegistrationForm(WConfDisplayBodyBase):

    _linkname = "registrationForm"

    def __init__(self, conf, av):
        self._conf = conf
        self._avatar = av

    def _getActionsHTML(self):
        html = ""
        regForm = self._conf.getRegistrationForm()
        if nowutc() < regForm.getStartRegistrationDate():
            return html
        else:
            submitOpt = ""
            registered = False
            if self._avatar is not None:
                registered = self._avatar.isRegisteredInConf(self._conf)
            if regForm.inRegistrationPeriod() and not registered:
                submitOpt = i18nformat("""<li><a href=%s> _("Show registration form")</a></li>""") % (quoteattr(str(urlHandlers.UHConfRegistrationFormDisplay.getURL(self._conf))))
            if registered:
                modify_registration_url = url_for(
                    "event.confRegistrationFormDisplay-modify",
                    self._conf)
                submitOpt = i18nformat(
                    """%s<li><a href=%s>
                        _("View or modify your already registration")
                       </a></li>""") % (submitOpt,
                                        quoteattr(str(modify_registration_url)))
            if registered and self._conf.getRegistrationForm().getETicket().isEnabled() and \
                    self._conf.getRegistrationForm().getETicket().isShownAfterRegistration():
                registrant = self._avatar.getRegistrantById(self._conf.getId())
                e_ticket_url = url_for("event.e-ticket-pdf", registrant,
                                       authkey=registrant.getRandomId())
                submitOpt = i18nformat(
                    """%s<li><a href=%s>
                            _("Download your e-ticket")
                       </a></li>""") % (submitOpt,
                                        quoteattr(str(e_ticket_url)))
            html = i18nformat("""
            <b> _("Possible actions you can carry out"):</b>
            <ul>
                %s
            </ul>
                   """) % (submitOpt)
        return html

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        wvars["body_title"] = self._getTitle()
        wvars["startDate"] = regForm.getStartRegistrationDate().strftime("%d %B %Y")
        wvars["endDate"] = regForm.getEndRegistrationDate().strftime("%d %B %Y")
        wvars["actions"] = self._getActionsHTML()
        wvars["announcement"] = regForm.getAnnouncement()
        wvars["title"] = regForm.getTitle()
        wvars["usersLimit"] = ""
        if regForm.getUsersLimit() > 0:
            wvars["usersLimit"] = i18nformat("""
                                <tr>
                                    <td nowrap class="displayField"><b> _("Max No. of registrants"):</b></td>
                                    <td width="100%%" align="left">%s</td>
                                </tr>
                                """) % regForm.getUsersLimit()
        wvars["contactInfo"] = ""
        if regForm.getContactInfo().strip() != "":
            wvars["contactInfo"] = i18nformat("""
                                <tr>
                                    <td nowrap class="displayField"><b> _("Contact info"):</b></td>
                                    <td width="100%%" align="left">%s</td>
                                </tr>
                                """) % regForm.getContactInfo()
        return wvars


class WPRegistrationFormDisplay( conferences.WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NERegistrationFormDisplay

    def getJSFiles(self):
        return conferences.WPConferenceDefaultDisplayBase.getJSFiles(self) + \
               self._includeJSPackage('Management')

    def _getBody(self, params):
        wc = WConfRegistrationFormDisplay(self._conf, self._rh._getUser())
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._newRegFormOpt)


class WConfRegistrationFormDisplay(WConfDisplayBodyBase):

    _linkname = "newEvaluation"

    def __init__(self, conf, user):
        self._currentUser = user
        self._conf = conf

    def _getWComp(self, sect, pdFormValues):
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
        return WConfRegFormGeneralSectionDisplay(sect, self._currentUser, pdFormValues)

    def _getOtherSectionsHTML(self):
        regForm = self._conf.getRegistrationForm()
        personalData = regForm.getPersonalData()
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._conf):
            pdFormValues = personalData.getValuesFromRegistrant(self._currentUser.getRegistrantById(self._conf.getId()))
        else:
            pdFormValues = personalData.getValuesFromAvatar(self._currentUser)

        html=[]
        for gs in regForm.getSortedForms():
            wcomp=self._getWComp(gs, pdFormValues)
            if gs.isEnabled():
                html.append( """
                            <tr>
                              <td align="left" style="padding-bottom:10px;">
                                %s
                              </td>
                            </tr>
                            """%wcomp.getHTML())
        return "".join(html)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        regForm = self._conf.getRegistrationForm()
        vars["body_title"] = self._getTitle()
        vars["title"] = regForm.getTitle()
        vars["postURL"] = quoteattr(str(urlHandlers.UHConfRegistrationFormCreation.getURL(self._conf)))
        vars["otherSections"]=self._getOtherSectionsHTML()
        return vars


class WConfRegistrationFormPreview(WConfRegistrationFormDisplay):

    def getVars(self):
        vars = WConfRegistrationFormDisplay.getVars(self)
        return vars

    def getHTML(self):
        return WConfRegistrationFormDisplay.getHTML(self)

class WConfRegFormGeneralSectionDisplay(wcomponents.WTemplated):

    def __init__(self, gs, currentUser, pdFormValues=None):
        self._generalSection = gs
        self._currentUser = currentUser
        self._pdFormValues = pdFormValues

    def _getFieldsHTML(self, miscGroup=None):
        html=[]
        registrant=None
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._generalSection.getConference()):
            registrant = self._currentUser.getRegistrantById(self._generalSection.getConference().getId())
        #jmf
        for f in self._generalSection.getSortedFields():
            if f.isDisabled():
                continue
            miscItem=None
            if miscGroup is not None and miscGroup.getResponseItemById(f.getId()) is not None:
                miscItem=miscGroup.getResponseItemById(f.getId())
            default = ""
            if self._generalSection is self._generalSection.getRegistrationForm().getPersonalData():
                default = self._pdFormValues.get(f.getPDField(), "")

            valign = "middle"
            try:
                description = f.getInput().getParent().getDescription()
            except AttributeError: # just to avoid cases where description attribute is not defined (almost never)
                description = None
            # if the element is a textarea, it has description, or it contains radio buttons, we have to align it on top
            if isinstance(f.getInput(), TextareaInput) or ("type=\"radio\"" in f.getInput().getModifHTML(miscItem, registrant, default)) or description:
                valign = "top"

            if f.getInput().useWholeRow():
                html.append("""
                        <tr>
                          <td colspan="2" valign="%s">
                             %s
                          </td>
                        </tr>
                            """%(valign, f.getInput().getModifHTML(miscItem, registrant, default)))
            else:
                html.append("""
                            <tr>
                              <td class="regFormCaption" valign="%s">
                                  <span class="regFormCaption">%s</span>
                                  <span class="regFormMandatoryField">%s</span>
                              </td>
                              <td>
                                 %s
                              </td>
                            </tr>
                            """%(valign, f.getInput().getModifLabelCol(), f.getInput().getMandatoryCol(miscItem), f.getInput().getModifHTML(miscItem, registrant, default)))

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
                inputHTML = """<input type="text" id="%s" name="%s" value="%s" size="40">"""%(item.getId(), item.getId(), value)
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
                inputHTML = """<select id="%s" name="%s">%s</select>"""%(item.getId(), item.getId(), inputHTML)
            elif item.getId() == "country":
                inputHTML= i18nformat("""<option value="">--  _("Select a country") --</option>""")
                for ck in CountryHolder().getCountrySortedKeys():
                    selected = ""
                    if value == ck:
                        selected = "selected"
                    inputHTML += """<option value="%s" %s>%s</option>"""%(ck, selected, CountryHolder().getCountryById(ck))
                inputHTML = """<select id="%s" name="%s">%s</select>"""%(item.getId(), item.getId(), inputHTML)

        else:
            inputHTML = """<input type="%s" id="%s" name="%s" size="40" value="%s">"""%(item.getInput(), item.getId(), item.getId(), value)
        if item.isMandatory():
            addParam = """<script>addParam($E('%s'), 'text', false);</script>""" % item.getId()
        else:
            addParam = ''
        inputHTML = "%s%s"%(inputHTML, addParam)
        mandatory="&nbsp; &nbsp;"
        if item.isMandatory():
            mandatory = """<font color="red">* </font>"""
        html = """
                <tr>
                    <td nowrap class="displayField">%s<b>%s</b></td>
                    <td width="100%%" align="left">%s</td>
                </tr>
                """%(mandatory, _(item.getName()), inputHTML)
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
        self._regSessions = []
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._conf):
            self._regSessions = [ses.getRegSession() for ses in self._currentUser.getRegistrantById(self._conf.getId()).getSessionList()]

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self._sessionForm.getTitle()
        vars["description"] = self._sessionForm.getDescription()
        return vars

class WConfRegFormSessionsDisplay(WConfRegFormSessionsBase):

    def _getSessionsHTML(self, sessions):
        if sessions.getSessionList() == []:
            html =  i18nformat("""--_("None selected")--""")
        else:
            html = []
            for ses in sessions.getSessionList(True):
                selected = ""
                if ses in self._regSessions:
                    selected = "selected"
                price = ""
                if ses.isBillable() and sessions.getType() != "2priorities":
                    price = " [%s %s]" % (ses.getPrice(), self._conf.getRegistrationForm().getCurrency())
                html.append("""
                        <input type="checkbox" name="sessionIds" value="%s" %s>%s%s
                        """%(ses.getId(), selected, ses.getTitle(), price) )
            html = "<br>".join(html)
        return html

    def getVars(self):
        vars = WConfRegFormSessionsBase.getVars( self )
        vars ["sessions"] = self._getSessionsHTML(self._sessionForm)
        return vars

class WConfRegFormSessions2PrioritiesDisplay(WConfRegFormSessionsBase):

    def _getSessionsHTML(self, sessions, selectName, sessionValue, mandatory=False):
        selected = ""
        if sessionValue is None:
            selected = "selected"
        if mandatory:
            addParam = """<script>addParam($E('%s'), 'text', false, function(value) {
                                                                       if (value === "nosession") {
                                                                          return Html.span({}, "Please choose an option");
                                                                       }else {
                                                                       return null;
                                                                       }
                                                                    });</script>""" % selectName
        else:
            addParam = ''
        html = [ i18nformat("""<select id="%s" name="%s">
                        <option value="nosession" %s>--_("Select a session")--</option>""")%(selectName, selectName, selected)]
        for ses in sessions.getSessionList(True):
            selected = ""
            if ses == sessionValue:
                selected = "selected"
            html.append("""
                    <option value="%s" %s>%s</option>
                    """%(ses.getId(), selected, ses.getTitle()) )
        html = """%s</select>%s"""%("".join(html), addParam)
        return html

    def getVars(self):
        vars = WConfRegFormSessionsBase.getVars( self )
        ses1 = None
        if len(self._regSessions)>0:
            ses1 = self._regSessions[0]
        vars ["sessions1"] = self._getSessionsHTML(self._sessionForm, "session1", ses1, True)
        ses2 = None
        if len(self._regSessions)>1:
            ses2 = self._regSessions[1]
        vars["sessions2"] = self._getSessionsHTML(self._sessionForm, "session2", ses2)
        return vars


def cmpSessionByStartDateThenTitle(x, y):
    if cmp(x.getStartDate(),y.getStartDate()):
        return cmp(x.getStartDate(),y.getStartDate())
    else:
        return cmp(x.getTitle(),y.getTitle())

class WConfRegFormSessionsAllDisplay(WConfRegFormSessionsBase):

    def _getSessionsHTML(self, alreadyPaid):
        html=[]
        sessionList = self._sessionForm.getSessionList()
        sessionList.sort(cmpSessionByStartDateThenTitle)
        for session in sessionList :
            selected=""
            if session in self._regSessions:
                selected=" checked"
            disabled = ""
            if alreadyPaid and session.isBillable():
                disabled = " disabled"
            price = ""
            if session.isBillable():
                price = " [%s %s]" % (session.getPrice(), self._conf.getRegistrationForm().getCurrency())
            html.append("""<input type="checkbox" name="sessions" value="%s"%s%s>%s%s"""%(session.getId(), selected, disabled, session.getTitle(), price) )
        return "<br>".join(html)

    def getVars(self):
        vars = WConfRegFormSessionsBase.getVars( self )
        alreadyPaid = False
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._conf):
            registrant = self._currentUser.getRegistrantById(self._conf.getId())
            alreadyPaid = registrant.getPayed()
        vars ["sessions"] = self._getSessionsHTML(alreadyPaid)
        return vars

class WConfRegFormAccommodationDisplay(wcomponents.WTemplated):

    def __init__(self, conf, currentUser):
        self._conf = conf
        self._accommodation = self._conf.getRegistrationForm().getAccommodationForm()
        self._currentUser = currentUser

    def _getDatesHTML(self, name, currentDate, startDate=None, endDate=None, alreadyPaid=False):
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
        disabled = ""
        if alreadyPaid:
            disabled = " disabled"
        html = [ i18nformat("""
                <select id="%s" name="%s"%s>
                <option value="nodate" %s>--_("select a date")--</option>
                """)%(name, name, disabled, selected)]
        for date in dates:
            selected = ""
            if currentDate is not None and currentDate.strftime("%d-%B-%Y") == date.strftime("%d-%B-%Y"):
                selected = "selected"
            html.append("""
                        <option value=%s %s>%s</option>
                        """%(quoteattr(str(date.strftime("%d-%m-%Y"))), selected, date.strftime("%d-%B-%Y")))

        addParam = """<script>addParam($E('%s'), 'text', false, function(value) {
                                                                       if (value === "nodate") {
                                                                          return Html.span({}, "Please choose an option");
                                                                       }else {
                                                                       return null;
                                                                       }
                                                                    });</script>""" % name
        html.append("</select>%s"%addParam)
        return "".join(html)

    def _getAccommodationTypesHTML(self, currentAccoType, alreadyPaid):
        html=[]
        for atype in self._accommodation.getAccommodationTypesList():
            if not atype.isCancelled():
                selected = ""
                if currentAccoType == atype:
                    selected = "checked=\"checked\""
                disabled = ""
                if alreadyPaid and (atype.isBillable() or (currentAccoType and currentAccoType.isBillable())):
                    disabled = ' disabled="disabled"'
                placesLeft = ""

                if not atype.hasAvailablePlaces():
                    placesLeft = " <span style='color:red;'>(no places left)</span>"
                    if currentAccoType != atype and not disabled:
                        disabled = ' disabled="disabled"'
                elif atype.getPlacesLimit() > 0:
                    placesLeft = " <span style='color:green; font-style:italic;'>[%s place(s) left]</span>"%atype.getNoPlacesLeft()
                priceCol = ""
                if atype.isBillable():
                    priceCol = """<td align="right">%s %s per night</td>""" % (atype.getPrice(), self._conf.getRegistrationForm().getCurrency())

                html.append("""<tr>
                                    <td align="left" style="padding-left:10px"><input type="radio" id="accommodationType" name="accommodationType" value="%s" %s%s>%s%s</td>
                                    %s
                                </tr>
                            """%(atype.getId(), selected, disabled, atype.getCaption(), placesLeft, priceCol ) )
            else:
                html.append( i18nformat("""<tr>
                                 <td align="left" style="padding-left:10px">&nbsp;&nbsp;&nbsp;<b>-</b> %s <font color="red">( _("not available at present") )</font></td>
                               </tr>
                            """)%(atype.getCaption() ) )

        html.append("""<script>addParam($E('accommodationType'), 'radio', false);</script>""")
        if currentAccoType is not None and currentAccoType.isCancelled() and currentAccoType not in self._accommodation.getAccommodationTypesList():
            html.append( i18nformat("""<tr>
                                <td align="left" style="padding-left:10px">&nbsp;&nbsp;&nbsp;<b>-</b> %s <font color="red">( _("not available at present") )</font></td>
                            </tr>
                        """)%(currentAccoType.getCaption() ) )
        return "".join(html)


    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        currentArrivalDate = None
        currentDepartureDate = None
        currentAccoType = None
        alreadyPaid = False
        alreadyPaidAcco = False
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._conf):
            registrant = self._currentUser.getRegistrantById(self._conf.getId())
            acco = registrant.getAccommodation()
            currentArrivalDate = None
            currentDepartureDate = None
            currentAccoType = None
            alreadyPaid = registrant.getPayed()
            if acco is not None:
                currentArrivalDate = acco.getArrivalDate()
                currentDepartureDate = acco.getDepartureDate()
                currentAccoType = acco.getAccommodationType()
                alreadyPaidAcco = alreadyPaid and acco.isBillable()
        vars["title"] = self._accommodation.getTitle()
        vars["description"] = self._accommodation.getDescription()
        vars["arrivalDate"] = self._getDatesHTML("arrivalDate", currentArrivalDate, alreadyPaid=alreadyPaidAcco)
        vars["departureDate"] = self._getDatesHTML("departureDate", currentDepartureDate, alreadyPaid=alreadyPaidAcco)
        vars["accommodationTypes"] = self._getAccommodationTypesHTML(currentAccoType, alreadyPaid)
        return vars

class WConfRegFormSocialEventDisplay(wcomponents.WTemplated):

    def __init__(self, conf, currentUser):
        self._conf = conf
        self._socialEvent = self._conf.getRegistrationForm().getSocialEventForm()
        self._currentUser = currentUser

    def _getSocialEventsHTML(self, socialEvents=[], alreadyPaid=False):
        html=[]
        for se in self._socialEvent.getSocialEventList(True):
            if not se.isCancelled():
                checked = ""
                for ser in socialEvents:
                    if se == ser.getSocialEventItem():
                        se = ser
                        checked = "checked=\"checked\""
                        break
                disabled = ""
                if se.isBillable() and alreadyPaid:
                    disabled = ' disabled="disabled"'
                optList = []
                for i in range(1, se.getMaxPlacePerRegistrant()+1):
                    selected = ""
                    if isinstance(se, registration.SocialEvent) and i == se.getNoPlaces():
                        selected = " selected"
                    optList.append("""<option value="%s"%s%s>%s"""%(i, selected, disabled, i))
                if len(optList)>0:
                    optList.insert(0, """<select name="places-%s"%s>"""%(se.getId(), disabled))
                    optList.append("</select>")
                seItem=se
                if isinstance(se, registration.SocialEvent):
                    seItem = se.getSocialEventItem()
                placesLeft = ""
                if seItem.getPlacesLimit() > 0:
                    placesLeft = "<span class='placesLeft'>[%s place(s) left]</span>"%seItem.getNoPlacesLeft()
                priceCol = ""
                if seItem.isBillable():
                    perPlace = ""
                    if seItem.isPricePerPlace():
                        perPlace = '&nbsp;<acronym title="" onmouseover="IndicoUI.Widgets.Generic.tooltip(this, event, \'per place\')">pp</acronym>'
                    priceCol = """<td align="right" nowrap>%s&nbsp;%s%s</td>""" % (seItem.getPrice(), self._conf.getRegistrationForm().getCurrency(), perPlace)

                inputType="checkbox"
                if self._socialEvent.getSelectionTypeId() == "unique":
                    inputType="radio"
                html.append("""<tr>
                                    <td align="left" style="padding-left:10px"><input type="%s" name="socialEvents" value="%s" %s%s>%s&nbsp;&nbsp;</td>
                                    <td align="left" nowrap>
                                       %s%s
                                    </td>
                                    %s
                                </tr>
                            """%(inputType, se.getId(), checked, disabled, se.getCaption(), "".join(optList), placesLeft, priceCol ) )
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
        alreadyPaid = False
        if self._currentUser is not None and self._currentUser.isRegisteredInConf(self._conf):
            registrant = self._currentUser.getRegistrantById(self._conf.getId())
            socialEvents = registrant.getSocialEvents()
            alreadyPaid = registrant.getPayed()
        vars["title"] = self._socialEvent.getTitle()
        vars["description"] = self._socialEvent.getDescription()
        vars["intro"] =  self._socialEvent.getIntroSentence()
        vars["socialEvents"] = self._getSocialEventsHTML(socialEvents, alreadyPaid)
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
        wc = WConfRegFormDeactivated(self._conf)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)


class WConfRegFormDeactivated(WConfDisplayBodyBase):

    _linkname = "registrationForm"

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        return wvars


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


class WConfRegistrationFormCreationDone(WConfDisplayBodyBase):

    _linkname = "NewRegistration"

    def __init__(self, registrant):
        self._registrant = registrant
        self._conf = self._registrant.getConference()

    def _getSessionsHTML(self):
        regForm = self._conf.getRegistrationForm()
        sessions = self._registrant.getSessionList()
        if regForm.getSessionsForm().isEnabled():
            if regForm.getSessionsForm().getType() == "2priorities":
                session1 = i18nformat("""<font color=\"red\">--_("not selected")--</font>""")
                session2 = "-- not selected --"
                if len(sessions) > 0:
                    session1 = sessions[0].getTitle()
                    if sessions[0].isCancelled():
                        session1 = i18nformat("""%s <font color=\"red\">( _("cancelled") )""")%session1
                if len(sessions) > 1:
                    session2 = sessions[1].getTitle()
                    if sessions[1].isCancelled():
                        session2 =  i18nformat("""%s <font color=\"red\">( _("cancelled") )""")%session2
                text = i18nformat("""
                        <table>
                          <tr>
                            <td align="left" class="regFormDoneCaption">_("First Priority"):</td>
                            <td align="left" class="regFormDoneData">%s</td>
                          </tr>
                          <tr>
                            <td align="left" class="regFormDoneCaption">_("Other option"):</td>
                            <td align="left" class="regFormDoneData">%s</td>
                          </tr>
                        </table>
                        """)%(session1, session2)
                return  _("""
                        <tr>
                          <td class="regFormDoneTitle">%s</td>
                        </tr>
                        <tr>
                          <td style="padding-bottom: 15px;">%s</td>
                        </tr>
                        """)%(regForm.getSessionsForm().getTitle(),text)
            if regForm.getSessionsForm().getType() == "all":
                sessionList =  i18nformat("""<font color=\"red\">--_("not selected")--</font>""")
                if len(sessions) > 0:
                    sessionList=["<ul>"]
                    for ses in sessions:
                        sesText = "<li>%s</li>"%ses.getTitle()
                        if ses.isCancelled():
                            sesText =  i18nformat("""<li>%s <font color=\"red\">( _("cancelled") )</font></li>""")%ses.getTitle()
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
                          <td class="regFormDoneTitle">%s</td>
                        </tr>
                        <tr>
                          <td style="padding-bottom: 15px;">%s</td>
                        </tr>
                        """)%(regForm.getSessionsForm().getTitle(), text)
        return ""

    def _getAccommodationHTML(self):
        regForm = self._conf.getRegistrationForm()
        if regForm.getAccommodationForm().isEnabled():
            accommodation = self._registrant.getAccommodation()
            accoType = i18nformat("""<font color=\"red\">--_("not selected")--</font>""")
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
                            <td align="left" class="regFormDoneCaption">Accommodation type</td>
                            <td align="left" class="regFormDoneData">%s %s</td>
                          </tr>"""%(accoType, cancelled)

            text = i18nformat("""
                        <table>
                          <tr>
                            <td align="left" class="regFormDoneCaption">_("Arrival date")</td>
                            <td align="left" class="regFormDoneData">%s</td>
                          </tr>
                          <tr>
                            <td align="left" class="regFormDoneCaption">_("Departure date")</td>
                            <td align="left" class="regFormDoneData">%s</td>
                          </tr>
                          %s
                        </table>
                        """)%(arrivalDate, departureDate, accoTypeHTML)
            return i18nformat("""
                    <tr>
                      <td class="regFormDoneTitle">_("Accommodation")</td>
                    </tr>
                    <tr>
                      <td style="padding-bottom: 15px;">%s</td>
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
                    cancelled =  i18nformat("""<font color=\"red\">( _("cancelled") )</font>""")
                    if se.getCancelledReason().strip():
                        cancelled =  i18nformat("""<font color=\"red\">( _("cancelled"): %s)</font>""")%se.getCancelledReason().strip()
                r.append( i18nformat("""
                            <tr>
                              <td align="left">
                                  <span class="regFormDoneCaption">%s</span>
                                  <span class="regFormDonePlacesNeeded">(%s  _("place(s) needed"))</span>
                                  <span>%s</span>
                            </td>
                            </tr>
                         """)%(se.getCaption(), se.getNoPlaces(), cancelled))
            if r == []:
                text =  i18nformat("""--  _("no social events selected") --""")
            else:
                text = """
                        <table>
                          %s
                        </table>
                        """%("".join(r))
            text =  _("""
                    <tr>
                      <td class="regFormDoneTitle">%s</td>
                    </tr>
                    <tr>
                      <td style="padding-bottom: 15px;">%s</td>
                    </tr>
                    """)%(regForm.getSocialEventForm().getTitle(), text)
        return text

    def _getReasonParticipationHTML(self):
        regForm = self._conf.getRegistrationForm()
        if regForm.getReasonParticipationForm().isEnabled():
            return  i18nformat("""
                    <tr>
                      <td class="regFormDoneTitle">_("Reason for participation")</td>
                    </tr>
                    <tr>
                      <td class="regFormDoneData" style="padding-bottom: 15px;">%s</td>
                    </tr>
                    """)%(self.htmlText( self._registrant.getReasonParticipation() ))
        return ""

    def _formatValue(self, fieldInput, value):
        try:
            return str(fieldInput.getValueDisplay(value))
        except:
            return str(value).strip()

    def _getMiscInfoItemsHTML(self, gsf):
        regForm = self._conf.getRegistrationForm()
        miscGroup=self._registrant.getMiscellaneousGroupById(gsf.getId())
        html=["""<table>"""]
        #jmf
        for f in gsf.getSortedFields():
            miscItem=None
            price=""
            currancy=""
            fieldInput = None
            if miscGroup is not None:
                miscItem=miscGroup.getResponseItemById(f.getId())
                if miscItem is None: continue # for fields created after the registration of the user, we skip it.
                fieldInput = miscItem.getGeneralField().getInput()
            v= i18nformat("""--_("no value selected")--""")
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
                       <td align="left" class="regFormDoneCaption">%s</td>
                       <td class="regFormDoneData">%s</td>
                       <td align="right" class="regFormDoneData">%s&nbsp;&nbsp;%s</td>
                    </tr>
                    """%(f.getCaption(), self._formatValue(fieldInput, v), price, currancy) )
        if miscGroup is not None:
            for miscItem in miscGroup.getResponseItemList():
                    f=gsf.getFieldById(miscItem.getId())
                    if f is None:
                        html.append( i18nformat("""
                                    <tr>
                                       <td align="right" nowrap><b>%s:</b></td>
                                       <td align="left">%s <font color="red">( _("cancelled") )</font></td>
                                    </tr>
                                    """)%(miscItem.getCaption(), self._formatValue(fieldInput, miscItem.getValue())) )
        if len(html)==1:
            html.append( i18nformat("""
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
                    fieldInput = miscItem.getGeneralField().getInput()
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
                               <td style="padding-left: 5px;">%s:%s%s</td>
                               <td align="right" style="padding-right:10px;">%i</td>
                               <td align="right" style="padding-right:10px" nowrap >%s</td>
                               <td align="right"nowrap >%s&nbsp;&nbsp;%s</td>
                            </tr>
                            """%(gsf.getTitle(), caption, self._formatValue(fieldInput, value), quantity, price,price*quantity,currency) )
        return "".join(html)


    def _getFormItemsHTMLBilllable(self, bf, total):
        html=[""]
        for item in bf.getBilledItems():
            caption = item.getCaption()
            currency = item.getCurrency()
            price = item.getPrice()
            quantity = item.getQuantity()
            total["value"] += price*quantity
            if quantity > 0:
                html.append("""
                        <tr>
                           <td align="left" style="padding-left: 5px;">%s</td>
                           <td align="right" style="padding-right:10px;">%i</td>
                           <td align="right" style="padding-right:10px" nowrap >%s</td>
                           <td align="right"nowrap >%s&nbsp;&nbsp;%s</td>
                        </tr>
                        """%(caption, quantity, price, price*quantity, currency))
        return "".join(html)


    def _getMiscellaneousInfoHTML(self, gsf):
        html=[]
        if gsf.isEnabled():
            html.append("""
                <tr>
                  <td class="regFormDoneTitle">%s</td>
                </tr>
                <tr>
                  <td style="padding-bottom: 15px;">%s</td>
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
            html.append( i18nformat(""" <tr><td colspan="2"><table width="100%" cellpadding="3">
                            <tr>
                                <td colspan="4" class="regFormDoneTitle">_("Payment summary")</td>
                            </tr>
                            <tr>
                                <td class="subGroupTitleRegForm" style="padding-left: 5px;">_("Item")</td>
                                <td class="subGroupTitleRegForm" style="padding-right:10px;">_("Quantity")</td>
                                <td nowrap class="subGroupTitleRegForm" style="padding-right:10px;">_("Unit Price")</td>
                                <td align="right" class="subGroupTitleRegForm">_("Cost")</td>
                            </tr>
                        """))
            for gsf in self._registrant.getMiscellaneousGroupList():
                html.append("""<tr>%s</tr>"""%(self._getMiscInfoItemsHTMLBilllable(gsf,total)))
            for bf in self._registrant.getBilledForms():
                html.append("""<tr>%s</tr>"""%(self._getFormItemsHTMLBilllable(bf,total)))

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

            html.append( i18nformat("""
                            <tr>
                               <td></td>
                               <td></td>
                               <td align="right" class="subGroupTitleRegForm" style="padding: 10px 10px 0 0;">_("TOTAL")</td>
                               <td align="right" nowrap class="subGroupTitleRegForm" style="padding-top: 10px;">%s&nbsp;&nbsp;%s</td>
                            </tr>
                            <form name="epay" action="%s" method="POST">
                            <tr>
                              <table width="100%%">
                                %s
                                <tr>
                                  <td align="right" nowrap><input type="submit" class="regFormButton" value="Next ->" onclick="return checkConditions()" ></td>
                                </tr>
                               </table>
                            </tr>
                            </form></tr>
                            </table></td></tr>
                            """)%(total["value"],regForm.getCurrency(),url,condChecking))
        return "".join(html)

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
        wvars = wcomponents.WTemplated.getVars( self )

        wvars["body_title"] = self._getTitle()
        wvars["id"] = self._registrant.getId()
        wvars["registrationDate"] = i18nformat("""--_("date unknown")--""")

        if self._registrant.getRegistrationDate() is not None:
            wvars["registrationDate"] = self._registrant.getAdjustedRegistrationDate().strftime("%d-%B-%Y %H:%M")
        wvars["otherSections"] = self._getFormSections()
        wvars["paymentInfo"] = self._getPaymentInfo()
        wvars["epaymentAnnounce"] = ""

        modEticket = self._conf.getRegistrationForm().getETicket()

        if modEticket.isEnabled() and modEticket.isShownAfterRegistration():
            wvars["pdfTicketURL"] = url_for(
                "event.e-ticket-pdf",
                self._registrant,
                authkey=self._registrant.getRandomId())

        if self._conf.getModPay().isActivated() and self._registrant.doPay():
            wvars["epaymentAnnounce"] = """<br><span>Please proceed to the <b>payment of your order</b> (by using the "Next" button down this page). You will then receive the payment details.</span>"""
        return wvars

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

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["modPayDetails"] = self.modPay.getPaymentDetails()
        vars["payMods"] = self.modPay.getSortedEnabledModPay()
        vars["registrant"] = self._registrant
        vars["conf"] = self._conf
        vars["lang"] = session.lang
        vars["secure"] = request.is_secure
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

    def getJSFiles(self):
        return conferences.WPConferenceDefaultDisplayBase.getJSFiles(self) + \
               self._includeJSPackage('Management')

    def _getBody(self, params):
        wc = WConfRegistrationFormModify(self._conf, self._rh._getUser())
        return wc.getHTML()

    def _defineSectionMenu( self ):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._viewRegFormOpt)


class WConfRegistrationFormModify(WConfRegistrationFormDisplay):

    _linkname = "ViewMyRegistration"

    def getVars(self):
        wvars = WConfRegistrationFormDisplay.getVars(self)
        registrant = self._currentUser.getRegistrantById(self._conf.getId())
        wvars["postURL"] = quoteattr(str(urlHandlers.UHConfRegistrationFormPerformModify.getURL(self._conf)))
        return wvars


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
        elif regForm.getAllowedEndRegistrationDate()<nowutc():
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

class WFileInputField(wcomponents.WTemplated):

    def __init__(self, field, item, default = None ):
        self._field = field
        self._item = item
        self._default = default

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["field"] = self._field

        htmlName = self._field.getHTMLName()
        value = self._default

        if self._item is not None:
            value =self._item.getValue() if self._item.getValue() else None
            htmlName = self._item.getHTMLName()

        vars["value"] = value
        vars["htmlName"] = htmlName
        return vars
