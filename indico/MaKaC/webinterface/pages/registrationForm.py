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

    def getJSFiles(self):
        return conferences.WPConferenceModifBase.getJSFiles(self) + \
               self._includeJSPackage('regform_edition')

    def getCSSFiles(self):
        return conferences.WPConferenceModifBase.getCSSFiles(self) + \
            self._asset_env['regform_css'].urls()

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabRegFormSetup = self._tabCtrl.newTab( "regformsetup", _("Setup"), \
                urlHandlers.UHConfModifRegForm.getURL( self._conf ) )
        self._tabRegistrationPreview = self._tabCtrl.newTab( "edit", _("Edit"), \
                urlHandlers.UHConfModifRegistrationPreview.getURL( self._conf ) )
        self._tabRegistrants = self._tabCtrl.newTab( "registrants", _("Registrants"), \
                urlHandlers.UHConfModifRegistrantList.getURL( self._conf ) )
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
        vars["statuses"] = self._getStatusesHTML()
        vars["actionStatusesURL"]=quoteattr(str(urlHandlers.UHConfModifRegFormActionStatuses.getURL(self._conf)))
        return vars

class WPConfModifRegFormDataModification( WPConfModifRegFormBase ):

    def _getTabContent( self, params ):
        wc = WConfModifRegFormDataModification(self._conf)
        return wc.getHTML()


class WConfModifRegFormDataModification(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        vars["postURL"] = urlHandlers.UHConfModifRegFormPerformDataModification.getURL(self._conf)
        vars["sDay"] = ""
        vars["sMonth"] = ""
        vars["sYear"] = ""
        if regForm.getStartRegistrationDate() is not None:
            d = regForm.getStartRegistrationDate()
            vars["sDay"] = d.day
            vars["sMonth"] = d.month
            vars["sYear"] = d.year
        vars["eDay"] = ""
        vars["eMonth"] = ""
        vars["eYear"] = ""
        if regForm.getEndRegistrationDate() is not None:
            d = regForm.getEndRegistrationDate()
            vars["eDay"] = d.day
            vars["eMonth"] = d.month
            vars["eYear"] = d.year
        vars["meDay"] = ""
        vars["meMonth"] = ""
        vars["meYear"] = ""
        if regForm.getModificationEndDate() is not None:
            d = regForm.getModificationEndDate()
            vars["meDay"] = d.day
            vars["meMonth"] = d.month
            vars["meYear"] = d.year
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
            self._includeJSPackage('Management') + \
            self._includeJSPackage('regform_display')

    def getCSSFiles(self):
        return conferences.WPConferenceDefaultDisplayBase.getCSSFiles(self) + \
            self._asset_env['regform_css'].urls()

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
                html.append( """%s"""%wcomp.getHTML())
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
        vars["confId"] = self._conf.getId()
        vars["postURL"] = quoteattr(str(urlHandlers.UHConfRegistrationFormCreation.getURL(self._conf)))
        return vars


class WConfRegistrationFormPreview(WConfRegistrationFormDisplay):

    def getVars(self):
        vars = WConfRegistrationFormDisplay.getVars(self)
        return vars

    def getHTML(self):
        return WConfRegistrationFormDisplay.getHTML(self)

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
            self._includeJSPackage('regform_display')

    def getCSSFiles(self):
        return conferences.WPConferenceDefaultDisplayBase.getCSSFiles(self) + \
            self._asset_env['regform_css'].urls()

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
