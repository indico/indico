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

import string
from xml.sax.saxutils import quoteattr

import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.navigation as navigation
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.i18n import _
from MaKaC.registration import LabelInput
from MaKaC.webinterface import wcomponents
from MaKaC.webinterface.pages.base import WPBase
from MaKaC.webinterface.pages.conferences import WConfDisplayBodyBase
from indico.modules.payment import event_settings as payment_event_settings
from indico.modules.payment.models.transactions import TransactionStatus
from indico.util.fossilize import fossilize
from indico.util.i18n import i18nformat
from indico.web.flask.util import url_for


# ----------------- MANAGEMENT AREA ---------------------------


class WPConfModifRegFormBase(conferences.WPConferenceModifBase):

    def getJSFiles(self):
        return conferences.WPConferenceModifBase.getJSFiles(self) + \
            self._includeJSPackage('regform')

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._tabRegFormSetup = self._tabCtrl.newTab("regformsetup", _("Setup"),
                                                     urlHandlers.UHConfModifRegForm.getURL(self._conf))
        self._tabRegistrationPreview = self._tabCtrl.newTab("edit", _("Edit"),
                                                        urlHandlers.UHConfModifRegistrationModification.getURL(self._conf))
        self._tabRegistrants = self._tabCtrl.newTab("registrants", _("Registrants"),
                                                    urlHandlers.UHConfModifRegistrantList.getURL(self._conf))
        self._tabStats = self._tabCtrl.newTab('stats', _("Stats"), url_for('event_mgmt.registration_stats', self._conf))
        self._tabPayment = self._tabCtrl.newTab("payment", _("Payment"), url_for('payment.event_settings', self._conf))
        self._tabETicket = self._tabCtrl.newTab("eticket", _("E-Ticket"), url_for('event_mgmt.confModifETicket',
                                                                                  self._conf))

        self._setActiveTab()

        if not self._conf.hasEnabledSection("regForm"):
            self._tabRegFormSetup.disable()
            self._tabRegistrants.disable()
            self._tabStats.disable()
            self._tabPayment.disable()
            self._tabRegistrationPreview.disable()
            self._tabETicket.disable()

    def _getPageContent(self, params):
        self._createTabCtrl()
        return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))

    def _getTabContent(self, params):
        return "nothing"

    def _setActiveSideMenuItem(self):
        self._regFormMenuItem.setActive()

    def _setActiveTab(self):
        pass

    def getCSSFiles(self):
        return conferences.WPConferenceModifBase.getCSSFiles(self) + \
            self._asset_env['registrationform_sass'].urls()


class WPConfModifRegFormPreview(WPConfModifRegFormBase):
    def _setActiveTab(self):
        self._tabRegistrationPreview.setActive()

    def _getTabContent(self, params):
        wc = WConfRegistrationFormPreview(self._conf, self._rh._getUser())
        return wc.getHTML()


class WPConfModifRegForm(WPConfModifRegFormBase):
    def _setActiveTab(self):
        self._tabRegFormSetup.setActive()

    def _getTabContent(self, params):
        wc = WConfModifRegForm(self._conf)
        return wc.getHTML()


class WConfModifRegForm(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def _getStatusesHTML(self):
        regForm = self._conf.getRegistrationForm()
        html = []
        for st in regForm.getStatusesList():
            urlStatus = urlHandlers.UHConfModifRegFormStatusModif.getURL(self._conf)
            urlStatus.addParam("statusId", st.getId())
            html.append("""
                        <tr>
                        <td>
                            &nbsp;<input type="checkbox" name="statusesIds" value="%s">&nbsp;<a href=%s>%s</a>
                        </td>
                        </tr>
                        """ % (st.getId(), quoteattr(str(urlStatus)), st.getCaption().strip() or i18nformat("""-- [%s]  _("status with no name") --""") % st.getId()))
        if html == []:
            html.append("""<tr><td style="padding-left:20px"><ul><li>%s</li></ul><br>%s</td></tr>""" % (_("No statuses defined yet."), _("You can use this option in order to create general statuses you will be able to use afterwards in the list of registrants. For instance, you can create a status \"paid\" in order to check if someone has paid or not.")))
        html.insert(0, """<a href="" name="statuses"></a><table style="padding-top:20px">""")
        html.append("</table>")
        return "".join(html)

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        wvars["setStatusURL"] = urlHandlers.UHConfModifRegFormChangeStatus.getURL(self._conf)
        wvars["dataModificationURL"] = urlHandlers.UHConfModifRegFormDataModification.getURL(self._conf)
        if regForm.isActivated():
            wvars["activated"] = True
            wvars["changeTo"] = "False"
            d = ""
            if regForm.getStartRegistrationDate() is not None:
                d = regForm.getStartRegistrationDate().strftime("%A %d %B %Y")
            wvars["startDate"] = d
            d = ""
            if regForm.getEndRegistrationDate() is not None:
                d = regForm.getEndRegistrationDate().strftime("%A %d %B %Y")
            wvars["endDate"] = d
            wvars["extraTimeAmount"] = regForm.getEndExtraTimeAmount()
            wvars["extraTimeUnit"] = regForm.getEndExtraTimeUnit()
            d = ""
            if regForm.getModificationEndDate() is not None:
                d = regForm.getModificationEndDate().strftime("%A %d %B %Y")
            wvars["modificationEndDate"] = d
            wvars["announcement"] = regForm.getAnnouncement()
            wvars["disabled"] = ""
            wvars["contactInfo"] = regForm.getContactInfo()
            wvars["usersLimit"] = i18nformat("""--_("No limit")--""")
            if regForm.getUsersLimit() > 0:
                wvars["usersLimit"] = regForm.getUsersLimit()
            wvars["title"] = regForm.getTitle()
            wvars["notification"] = i18nformat("""
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
                                    """) % (", ".join(regForm.getNotification().getToList()) or i18nformat("""--_("no TO list")--"""), ", ".join(regForm.getNotification().getCCList()) or i18nformat("""--_("no CC list")--"""))
            wvars["mandatoryAccount"] = _("Yes")
            if not regForm.isMandatoryAccount():
                wvars["mandatoryAccount"] = _("No")
            wvars["notificationSender"] = regForm.getNotificationSender()
            wvars["sendRegEmail"] = _("Yes")
            if not regForm.isSendRegEmail():
                wvars["sendRegEmail"] = _("No")
            wvars["sendReceiptEmail"] = _("Yes")
            wvars["sendPaidEmail"] = _("Yes")
            if not regForm.isSendPaidEmail():
                wvars["sendPaidEmail"] = _("No")
        else:
            wvars["activated"] = False
            wvars["changeTo"] = "True"
            wvars["startDate"] = ""
            wvars["endDate"] = ""
            wvars["extraTimeAmount"] = ""
            wvars["extraTimeUnit"] = ""
            wvars["modificationEndDate"] = ""
            wvars["announcement"] = ""
            wvars["disabled"] = 'disabled = "disabled"'
            wvars["contactInfo"] = ""
            wvars["usersLimit"] = ""
            wvars["title"] = ""
            wvars["notification"] = ""
            wvars["mandatoryAccount"] = ""
            wvars["notificationSender"] = ""
            wvars["sendRegEmail"] = ""
            wvars["sendReceiptEmail"] = ""
            wvars["sendPaidEmail"] = ""
        wvars["statuses"] = self._getStatusesHTML()
        wvars["actionStatusesURL"] = quoteattr(str(urlHandlers.UHConfModifRegFormActionStatuses.getURL(self._conf)))
        return wvars


class WPConfModifRegFormDataModification(WPConfModifRegFormBase):

    def _getTabContent(self, params):
        wc = WConfModifRegFormDataModification(self._conf)
        return wc.getHTML()


class WConfModifRegFormDataModification(wcomponents.WTemplated):

    def __init__(self, conference):
        self._conf = conference

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        wvars["postURL"] = urlHandlers.UHConfModifRegFormPerformDataModification.getURL(self._conf)
        wvars["sDay"] = ""
        wvars["sMonth"] = ""
        wvars["sYear"] = ""
        if regForm.getStartRegistrationDate() is not None:
            d = regForm.getStartRegistrationDate()
            wvars["sDay"] = d.day
            wvars["sMonth"] = d.month
            wvars["sYear"] = d.year
        wvars["eDay"] = ""
        wvars["eMonth"] = ""
        wvars["eYear"] = ""
        if regForm.getEndRegistrationDate() is not None:
            d = regForm.getEndRegistrationDate()
            wvars["eDay"] = d.day
            wvars["eMonth"] = d.month
            wvars["eYear"] = d.year
        wvars["meDay"] = ""
        wvars["meMonth"] = ""
        wvars["meYear"] = ""
        if regForm.getModificationEndDate() is not None:
            d = regForm.getModificationEndDate()
            wvars["meDay"] = d.day
            wvars["meMonth"] = d.month
            wvars["meYear"] = d.year
        wvars["announcement"] = regForm.getAnnouncement()
        wvars["contactInfo"] = regForm.getContactInfo()
        wvars["usersLimit"] = regForm.getUsersLimit()
        wvars["title"] = regForm.getTitle()
        wvars["toList"] = ", ".join(regForm.getNotification().getToList())
        wvars["ccList"] = ", ".join(regForm.getNotification().getCCList())
        wvars["mandatoryAccount"] = ""
        if regForm.isMandatoryAccount():
            wvars["mandatoryAccount"] = "CHECKED"
        wvars["notificationSender"] = regForm.getNotificationSender()
        wvars["sendRegEmail"] = ""
        wvars["sendPaidEmail"] = ""
        if regForm.isSendRegEmail():
            wvars["sendRegEmail"] = "CHECKED"
        if regForm.isSendPaidEmail():
            wvars["sendPaidEmail"] = "CHECKED"
        wvars["extraTimeAmount"] = regForm.getEndExtraTimeAmount()
        wvars["extraTimeUnit"] = regForm.getEndExtraTimeUnit()
        return wvars


class WPConfModifRegFormStatusesRemConfirm(WPConfModifRegFormBase):

    def __init__(self, rh, target, stids):
        WPConfModifRegFormBase.__init__(self, rh, target)
        self._statusesIds = stids

    def _getTabContent(self, params):
        wc = wcomponents.WConfirmation()

        statuses = ''.join(list("<li>{0}</li>".format(self._conf.getRegistrationForm().getStatusById(s).getCaption()
                                                      or _('-- unnamed status --')) for s in self._statusesIds))

        msg = {'challenge': _("Are you sure you want to delete the following registration statuses?"),
               'target': "<ul>{0}</ul>".format(statuses),
               'subtext': _("Please note that any existing registrants will lose this information")
               }

        url = urlHandlers.UHConfModifRegFormActionStatuses.getURL(self._conf)
        return wc.getHTML(msg, url, {"statusesIds": self._statusesIds, "removeStatuses": "1"})


class WPConfModifRegFormStatusModif(WPConfModifRegFormBase):

    def __init__(self, rh, st, tmpst):
        WPConfModifRegFormBase.__init__(self, rh, st.getConference())
        self._status = st
        self._tempStatus = tmpst

    def _getTabContent(self, params):
        wc = WConfModifRegFormStatusModif(self._status, self._tempStatus)
        p = {'postURL': quoteattr(str(urlHandlers.UHConfModifRegFormStatusPerformModif.getURL(self._status)))}
        return wc.getHTML(p)


class WConfModifRegFormStatusModif(wcomponents.WTemplated):

    def __init__(self, st, tmpst):
        self._conf = st.getConference()
        self._status = st
        self._tempStatus = tmpst

    def _getStatusValuesHTML(self):
        html = ["""<table>"""]
        for v in self._tempStatus.getStatusValuesList(True):
            default = ""
            if self._tempStatus.getDefaultValue() is not None and self._tempStatus.getDefaultValue() == v.getId():
                default = """<i><b> (default)</b></i>"""
            html.append("""<tr>
                                <td align="left" style="padding-left:10px"><input type="checkbox" name="valuesIds" value="%s">%s%s</td>
                            </tr>
                        """ % (v.getId(), self.htmlText(v.getCaption()), default))
        html.append("""</table>""")
        return "".join(html)

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["caption"] = self._tempStatus.getCaption()
        wvars["values"] = self._getStatusValuesHTML()
        return wvars

# ----------------------------------------------------------
# ----------------- DISPLAY AREA ---------------------------


class WPRegistrationForm(conferences.WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NERegistrationForm

    def _getBody(self, params):
        wc = WConfRegistrationForm(self._conf, self._getAW().getUser(),
                                   params.get('registrant'), params.get('registrant_id'), params.get('authkey'))
        return wc.getHTML()

    def _defineSectionMenu(self):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

    def getCSSFiles(self):
        return conferences.WPConferenceDefaultDisplayBase.getCSSFiles(self) + \
            self._asset_env['registrationform_sass'].urls()


class WConfRegistrationForm(WConfDisplayBodyBase):

    _linkname = 'registration'

    def __init__(self, conf, av, registrant, registrant_id=None, authkey=None):
        self._conf = conf
        self._avatar = av
        self._registrant = registrant
        self._authparams = {'registrantId': registrant_id, 'authkey': authkey}

    def _formatValue(self, fieldInput, value):
        try:
            return str(fieldInput.getValueDisplay(value))
        except:
            return str(value).strip()

    def _getAccommodationHTML(self):
        regForm = self._conf.getRegistrationForm()
        if regForm.getAccommodationForm().isEnabled():
            accommodation = self._registrant.getAccommodation()
            accoType = i18nformat("""<span class="not-selected">_("Not selected")</span>""")
            cancelled = ""
            if accommodation is not None and accommodation.getAccommodationType() is not None:
                accoType = accommodation.getAccommodationType().getCaption()
                if accommodation.getAccommodationType().isCancelled():
                    cancelled = """<span class="not-selected">( """ + _("disabled") + """)</span>"""
            arrivalDate = """<span class="not-selected">""" + _("Not selected") + """</span>"""
            if accommodation is not None and accommodation.getArrivalDate() is not None:
                arrivalDate = accommodation.getArrivalDate().strftime("%d-%B-%Y")
            departureDate = """<span class="not-selected">""" + _("Not selected") + """</span>"""
            if accommodation is not None and accommodation.getDepartureDate() is not None:
                departureDate = accommodation.getDepartureDate().strftime("%d-%B-%Y")
            accoTypeHTML = ""
            if regForm.getAccommodationForm().getAccommodationTypesList() != []:
                accoTypeHTML = i18nformat("""
                          <tr>
                            <td align="left" class="regform-done-caption">_("Type")</td>
                            <td align="left" class="regform-done-data">%s %s</td>
                          </tr>""" % (accoType, cancelled))

            text = i18nformat("""
                        <table>
                          <tr>
                            <td align="left" class="regform-done-caption">_("Arrival")</td>
                            <td align="left" class="regform-done-data">%s</td>
                          </tr>
                          <tr>
                            <td align="left" class="regform-done-caption">_("Departure")</td>
                            <td align="left" class="regform-done-data">%s</td>
                          </tr>
                          %s
                        </table>
                        """) % (arrivalDate, departureDate, accoTypeHTML)
            return i18nformat("""
                    <tr>
                      <td class="regform-done-title">_("Accommodation")</td>
                    </tr>
                    <tr>
                      <td>%s</td>
                    </tr>
                    """) % (text)
        return ""

    def _getActions(self):
        actions = []
        regForm = self._conf.getRegistrationForm()
        eticket = regForm.getETicket()
        if not self._registrant and regForm.inRegistrationPeriod() and not regForm.isFull():
            actions.append('register')
        if self._registrant and regForm.inModificationPeriod():
            actions.append('modify')
        if self._registrant and eticket.isEnabled() and eticket.isShownAfterRegistration():
            actions.append('download')
        return actions

    def _getFormItemsHTMLBillable(self, bf, total):
        html = [""]
        for item in bf.getBilledItems():
            caption = item.getCaption()
            currency = item.getCurrency()
            price = item.getPrice()
            quantity = item.getQuantity()
            total["value"] += price * quantity
            if quantity > 0:
                html.append("""
                        <tr class="regform-done-table-item">
                           <td align="left">%s</td>
                           <td align="right" nowrap>%i</td>
                           <td align="right" nowrap>%s</td>
                           <td align="right" nowrap>%s <em>%s</em></td>
                        </tr>
                        """ % (caption, quantity, price, price * quantity, currency))
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
        return "".join(s.decode('utf-8') for s in sects).encode('utf-8')

    def _getMiscellaneousInfoHTML(self, gsf):
        html = []
        if gsf.isEnabled():
            html.append("""
                <tr>
                  <td class="regform-done-title">%s</td>
                </tr>
                <tr>
                  <td>%s</td>
                </tr>
                """ % (gsf.getTitle(), self._getMiscInfoItemsHTML(gsf)))
        return "".join(html)

    def _getMiscInfoItemsHTML(self, gsf):
        regForm = self._conf.getRegistrationForm()
        miscGroup = self._registrant.getMiscellaneousGroupById(gsf.getId())
        html = ["""<table>"""]
        for f in (f for f in gsf.getSortedFields() if not isinstance(f.getInput(), LabelInput)):
            miscItem = None
            fieldInput = None
            if miscGroup is not None:
                miscItem = miscGroup.getResponseItemById(f.getId())
                if miscItem is None:  # for fields created after the registration of the user, we skip it.
                    continue
                fieldInput = miscItem.getGeneralField().getInput()
            v = """<span class="not-selected">""" + _("No value selected") + """</span>"""
            if miscItem is not None:
                v = miscItem.getValue()
            if v is None:
                v = ""
            html.append("""
                    <tr>
                       <td class="regform-done-caption">%s</td>
                       <td class="regform-done-data">%s</td>
                    </tr>
                    """ % (f.getCaption(), self._formatValue(fieldInput, v)))
        if miscGroup is not None:
            for miscItem in (f for f in miscGroup.getResponseItemList() if not isinstance(f.getGeneralField().getInput(), LabelInput)):
                fieldInput = miscItem.getGeneralField().getInput()
                f = gsf.getFieldById(miscItem.getId())
                if f is None:
                    html.append(i18nformat("""
                                <tr>
                                   <td class="regform-done-caption">%s</td>
                                   <td class="regform-done-data">%s <span class="not-selected">(_("Cancelled"))</span></td>
                                </tr>
                                """) % (miscItem.getCaption(), self._formatValue(fieldInput, miscItem.getValue())))
        if len(html) == 1:
            html.append(i18nformat("""
                        <tr><td><font color="black"><i>--_("No fields")--</i></font></td></tr>
                        """))
        html.append("</table>")
        return "".join(html)

    def _getMiscInfoItemsHTMLBillable(self, gsf, total):
        miscGroup = self._registrant.getMiscellaneousGroupById(gsf.getId())
        html = [""""""]
        if miscGroup is not None:
            for miscItem in miscGroup.getResponseItemList():
                price = 0.0
                quantity = 0
                value = ""
                caption = miscItem.getCaption()
                currency = miscItem.getCurrency()
                if miscItem is not None:
                    if gsf.getGeneralSection().getFieldById(miscItem.getId()) is None:
                        continue
                    if miscItem.getGeneralField().isDisabled():
                        continue
                    fieldInput = miscItem.getGeneralField().getInput()
                    if miscItem.isBillable():
                        value = miscItem.getValue()
                        price = string.atof(miscItem.getPrice())
                        quantity = miscItem.getQuantity()
                        total["value"] += price * quantity
                if value != "":
                    value = ":%s" % value
                if quantity > 0:
                    html.append("""
                            <tr class="regform-done-table-item">
                               <td>%s: %s%s</td>
                               <td align="right" nowrap>%i</td>
                               <td align="right" nowrap>%s</td>
                               <td align="right" nowrap>%s <em>%s</em></td>
                            </tr>
                            """ % (gsf.getTitle(), caption, self._formatValue(fieldInput, value),
                                   quantity, price, price * quantity, currency))
        return "".join(html)

    def _getPaymentInfo(self):
        enabled = payment_event_settings.get(self._conf, 'enabled')
        if not self._registrant or not enabled:
            return
        html = []
        if enabled and self._registrant.getTotal():
            total = {}
            total["value"] = 0
            html.append(i18nformat(""" <tr><td colspan="2">
                        <table width="100%" cellpadding="3" cellspacing="0">
                            <tr>
                                <td class="regform-done-table-title">
                                    _("Item")
                                </td>
                                <td align="right" class="regform-done-table-title">
                                    _("Quantity")
                                </td>
                                <td align="right" class="regform-done-table-title" nowrap>
                                    _("Unit Price")
                                </td>
                                <td align="right" class="regform-done-table-title">
                                    _("Cost")
                                </td>
                            </tr>
                        """))
            for gsf in self._registrant.getMiscellaneousGroupList():
                html.append("""%s""" % (self._getMiscInfoItemsHTMLBillable(gsf, total)))
            for bf in self._registrant.getBilledForms():
                html.append("""%s""" % (self._getFormItemsHTMLBillable(bf, total)))

            html.append(i18nformat("""
                                <tr>
                                    <td align="right" class="regform-done-table-total" colspan="3">
                                        _("TOTAL")
                                    </td>
                                    <td align="right" class="regform-done-table-total" nowrap>
                                        %s <em>%s</em>
                                    </td>
                                </tr>
                            </table></td></tr>
                            """) % (total["value"], payment_event_settings.get(self._conf, 'currency')))
        return "".join(html)

    def _getReasonParticipationHTML(self):
        regForm = self._conf.getRegistrationForm()
        if regForm.getReasonParticipationForm().isEnabled():
            if self.htmlText(self._registrant.getReasonParticipation()) is not "":
                text = self.htmlText(self._registrant.getReasonParticipation())
            else:
                text = """<span class="not-selected">""" + _("No reason given") + """</span>"""
            return i18nformat("""
                    <tr>
                      <td class="regform-done-title">_("Reason for participation")</td>
                    </tr>
                    <tr>
                      <td>%s</td>
                    </tr>
                    """) % (text)
        return ""

    def _getSessionsHTML(self):
        regForm = self._conf.getRegistrationForm()
        sessions = self._registrant.getSessionList()
        if regForm.getSessionsForm().isEnabled():
            if regForm.getSessionsForm().getType() == "2priorities":
                session1 = i18nformat("""<span class="not-selected">_("Not selected")</span>""")
                session2 = i18nformat("""<span class="not-selected">_("Not selected")</span>""")
                if len(sessions) > 0:
                    session1 = sessions[0].getTitle()
                    if sessions[0].isCancelled():
                        session1 = i18nformat("""%s <span class="not-selected">(_("Cancelled"))</span>""") % session1
                if len(sessions) > 1:
                    session2 = sessions[1].getTitle()
                    if sessions[1].isCancelled():
                        session2 = i18nformat("""%s <span class="not-selected">(_("Cancelled"))</span>""") % session2
                text = i18nformat("""
                        <table>
                          <tr>
                            <td class="regform-done-caption">_("Preferred choice")</td>
                            <td class="regform-done-data">%s</td>
                          </tr>
                          <tr>
                            <td class="regform-done-caption">_("Secondary choice")</td>
                            <td class="regform-done-data">%s</td>
                          </tr>
                        </table>
                        """) % (session1, session2)
                return _("""
                        <tr>
                          <td class="regform-done-title">%s</td>
                        </tr>
                        <tr>
                          <td>%s</td>
                        </tr>
                        """) % (regForm.getSessionsForm().getTitle(), text)
            if regForm.getSessionsForm().getType() == "all":
                sessionList = i18nformat("""<span class="not-selected">_("No sessions selected")</span>""")
                if len(sessions) > 0:
                    sessionList = ["<ul>"]
                    for ses in sessions:
                        sesText = "<li>%s</li>" % ses.getTitle()
                        if ses.isCancelled():
                            sesText = i18nformat("""<li>%s <span class="not-selected">(_("Cancelled"))</span></li>""") % ses.getTitle()
                        sessionList.append(sesText)
                    sessionList.append("</ul>")
                    sessionList = "".join(sessionList)
                text = """
                        <table>
                          <tr>
                            <td align="left">%s</td>
                          </tr>
                        </table>
                        """ % (sessionList)
                return _("""
                        <tr>
                          <td class="regform-done-title">%s</td>
                        </tr>
                        <tr>
                          <td>%s</td>
                        </tr>
                        """) % (regForm.getSessionsForm().getTitle(), text)
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
                    cancelled = i18nformat("""<span class="not-selected">(_("Cancelled"))</span>""")
                    if se.getCancelledReason().strip():
                        cancelled = i18nformat("""<span class="not-selected">(_("Cancelled"): %s)</span>""") % se.getCancelledReason().strip()
                r.append(i18nformat("""
                            <tr>
                                <td align="left">
                                    <span class="regform-done-caption">%s</span>
                                    <span class="regFormDonePlacesNeeded">%s _("place(s) needed")</span>
                                    <span>%s</span>
                                </td>
                            </tr>
                         """) % (se.getCaption(), se.getNoPlaces(), cancelled))
            if r == []:
                text = """<span class="not-selected">""" + _("No social events selected") + """</span>"""
            else:
                text = """
                        <table>
                          %s
                        </table>
                        """ % ("".join(r))
            text = _("""
                    <tr>
                      <td class="regform-done-title">%s</td>
                    </tr>
                    <tr>
                      <td>%s</td>
                    </tr>
                    """) % (regForm.getSocialEventForm().getTitle(), text)
        return text

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()

        wvars["conf"] = self._conf
        wvars["confId"] = self._conf.getId()
        wvars["registrant"] = self._registrant
        wvars["authparams"] = self._authparams
        wvars["body_title"] = self._getTitle()
        wvars["in_registration_period"] = regForm.inRegistrationPeriod()
        wvars["is_full"] = regForm.isFull()
        wvars["startDate"] = regForm.getStartRegistrationDate()
        wvars["endDate"] = regForm.getEndRegistrationDate()
        wvars["nowutc"] = nowutc()
        wvars["actions"] = self._getActions()
        wvars["announcement"] = regForm.getAnnouncement()
        wvars["title"] = regForm.getTitle()
        wvars["usersLimit"] = ""
        wvars["TransactionStatus"] = TransactionStatus

        if regForm.getUsersLimit() > 0:
            wvars["usersLimit"] = regForm.getUsersLimit()
        wvars["contactInfo"] = ""
        if regForm.getContactInfo().strip() != "":
            wvars["contactInfo"] = regForm.getContactInfo()

        if self._registrant:
            wvars["payment_info"] = self._getPaymentInfo()
            wvars["payment_enabled"] = payment_event_settings.get(self._conf, 'enabled')
            wvars["payment_conditions"] = payment_event_settings.get(self._conf, 'conditions')
            wvars["payment_done"] = self._registrant.getPayed()
            wvars["registration_info"] = self._getFormSections()
            if self._registrant.getRegistrationDate() is not None:
                wvars["registration_date"] = self._registrant.getAdjustedRegistrationDate().strftime('%d %b %Y')

        return wvars


class WPRegistrationFormDisplay(conferences.WPConferenceDefaultDisplayBase):

    navigationEntry = navigation.NERegistrationFormDisplay

    def getJSFiles(self):
        return conferences.WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._includeJSPackage('Management') + \
            self._includeJSPackage('regform')

    def _getBody(self, params):
        wc = WConfRegistrationFormDisplay(self._conf, self._rh._getUser())
        return wc.getHTML(params)

    def _defineSectionMenu(self):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

    def getCSSFiles(self):
        return conferences.WPConferenceDefaultDisplayBase.getCSSFiles(self) + \
            self._asset_env['registrationform_sass'].urls()


class WConfRegistrationFormDisplay(WConfDisplayBodyBase):

    _linkname = 'registration'

    def __init__(self, conf, user):
        self._currentUser = user
        self._conf = conf

    def _getTitle(self):
        title = WConfDisplayBodyBase._getTitle(self)
        return _('{}: New'.format(title))

    def getSections(self):
        return self._conf.getRegistrationForm().getSortedForms()

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        regForm = self._conf.getRegistrationForm()
        wvars["body_title"] = self._getTitle()
        wvars["title_regform"] = regForm.getTitle()
        wvars["currency"] = payment_event_settings.get(self._conf, 'currency')
        if wvars.get('manager'):
            wvars['postURL'] = quoteattr(url_for('event_mgmt.confModifRegistrants-newRegistrant-save', self._conf))
        else:
            wvars["postURL"] = quoteattr(str(urlHandlers.UHConfRegistrationFormCreation.getURL(self._conf)))
        wvars["conf"] = self._conf
        wvars['sections'] = fossilize(section for section in self.getSections() if section.isEnabled())
        return wvars


class WConfRegistrationFormPreview(WConfRegistrationFormDisplay):

    def getVars(self):
        wvars = WConfRegistrationFormDisplay.getVars(self)
        wvars["sections"] = fossilize(WConfRegistrationFormDisplay.getSections(self))
        return wvars

    def getHTML(self):
        return WConfRegistrationFormDisplay.getHTML(self)


class WPRegFormInactive(conferences.WPConferenceDefaultDisplayBase):

    def _getBody(self, params):
        wc = WConfRegFormDeactivated(self._conf)
        return wc.getHTML()

    def _defineSectionMenu(self):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)


class WConfRegFormDeactivated(WConfDisplayBodyBase):

    _linkname = 'registration'

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        return wvars


class WPRegistrationFormModify(conferences.WPConferenceDefaultDisplayBase):
    navigationEntry = navigation.NERegistrationFormModify

    def getJSFiles(self):
        return conferences.WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._includeJSPackage('regform')

    def _getBody(self, params):
        wc = WConfRegistrationFormModify(self._conf, self._rh._getUser())
        return wc.getHTML()

    def _defineSectionMenu(self):
        conferences.WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._regFormOpt)

    def getCSSFiles(self):
        return conferences.WPConferenceDefaultDisplayBase.getCSSFiles(self) + \
            self._asset_env['registrationform_sass'].urls()


class WConfRegistrationFormModify(WConfRegistrationFormDisplay):

    def _getTitle(self):
        title = WConfDisplayBodyBase._getTitle(self)
        return _('{}: Modify'.format(title))

    def getVars(self):
        wvars = WConfRegistrationFormDisplay.getVars(self)
        wvars["postURL"] = quoteattr(str(urlHandlers.UHConfRegistrationFormPerformModify.getURL(self._conf)))
        return wvars


class WPRegistrationFormConditions(WPBase):

    def __init__(self, rh, conf):
        WPBase.__init__(self, rh)
        self._conf = conf

    def _display(self, params):
        wc = WConfRegistrationFormConditions(self._conf)
        return wc.getHTML()


class WConfRegistrationFormConditions(wcomponents.WTemplated):

    def __init__(self, conf):
        self._conf = conf

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["conditions"] = payment_event_settings.get(self._conf, 'conditions')
        return wvars


class WFileInputField(wcomponents.WTemplated):

    def __init__(self, field, item, default=None):
        self._field = field
        self._item = item
        self._default = default

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["field"] = self._field

        htmlName = self._field.getHTMLName()
        value = self._default

        if self._item is not None:
            value = self._item.getValue() if self._item.getValue() else None
            htmlName = self._item.getHTMLName()

        wvars["value"] = value
        wvars["htmlName"] = htmlName
        return wvars
