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

import math
from datetime import timedelta
import MaKaC.webinterface.pages.registrationForm as registrationForm
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.common.filters as filters
from MaKaC.webinterface.pages.conferences import WConfDisplayBodyBase
from MaKaC.webinterface import wcomponents
from xml.sax.saxutils import quoteattr
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase
from indico.core.config import Config
from MaKaC.webinterface.common.countries import CountryHolder
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.webinterface.common.registrantNotificator import EmailNotificator
from MaKaC import registration
from conferences import WConfModifBadgePDFOptions
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from indico.util. date_time import format_datetime
from indico.web.flask.util import url_for
from xml.sax.saxutils import escape
import string


# ----------------- MANAGEMENT AREA ---------------------------
class WPConfModifRegistrantListBase(registrationForm.WPConfModifRegFormBase):

    def _setActiveTab(self):
        self._tabRegistrants.setActive()


class WPConfModifRegistrantList(WPConfModifRegistrantListBase):
    def __init__(self, rh, conference, filterUsed=False):
        WPConfModifRegistrantListBase.__init__(self, rh, conference)
        self._filterUsed = filterUsed

    def _getTabContent(self, params):
        filterCrit = params.get("filterCrit", None)
        sortingCrit = params.get("sortingCrit", None)
        display = params.get("display", None)
        order = params.get("order", None)
        sessionFilterName = params.get("sessionFilterName", "session")

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
        if not requestParams.has_key('disp'):
            urlParams['disp'] = display
        urlParams.update(filterParams)
        filterUrl = self._rh._uh.getURL(None, **urlParams)

        wc = WConfModifRegistrants(self._conf, filterCrit, sortingCrit, display, filterUrl, order, sessionFilterName,
                                   self._filterUsed)
        return wc.getHTML()


class WConfModifRegistrants(wcomponents.WTemplated):
    def __init__(self, conference, filterCrit, sortingCrit, display, filterUrl, order="down",
                 sessionFilterName="session", filterUsed=False):

        self._conf = conference
        self._filterCrit = filterCrit
        self._sortingCrit = sortingCrit
        self._order = order
        self._sessionFilterName = sessionFilterName
        self._filterUrl = filterUrl
        self._display = display
        self._filterUsed = filterUsed
        self._setDispOpts()
        self._setStatusesOpts()

    def _setStatusesOpts(self):
        """
        """
        self._statuses = {}
        for st in self._conf.getRegistrationForm().getStatusesList(False):
            self._statuses[st.getId()] = st.getStatusValues()

    def _setDispOpts(self):
        """
            Dictionary with the available options you can choose for the display.
            Within the dictionary we store the "ids" of the options.
        """
        self._dispopts = {"PersonalData":[ "Id", "LastName", "FirstName", "Email", "Position", "Institution","Phone","City","Country","Address","isPayed","idpayment","amountToPay"]}
        self._dispopts["statuses"]=[]
        for st in self._conf.getRegistrationForm().getStatusesList(False):
            self._dispopts["statuses"].append("s-%s"%st.getId())
        #if self._conf.getRegistrationForm().getAccommodationForm().isEnabled():
        self._dispopts["Accommodation"]=["Accommodation", "ArrivalDate","DepartureDate"]
        #if self._conf.getRegistrationForm().getSocialEventForm().isEnabled():
        self._dispopts["SocialEvents"] = ["SocialEvents"]
        #if self._conf.getRegistrationForm().getSessionsForm().isEnabled():
        self._dispopts["Sessions"] = ["Sessions"]
        #if self._conf.getRegistrationForm().getReasonParticipationForm().isEnabled():
        self._dispopts["ReasonParticipation"]=["ReasonParticipation"]
        if self._conf.getRegistrationForm().getETicket().isEnabled():
            self._dispopts["eTicket"] = ["checkedIn", "checkInDate"]
        self._dispopts["more"]=["RegistrationDate"]
        for sect in self._conf.getRegistrationForm().getGeneralSectionFormsList():
            self._dispopts[sect.getId()]=[]

            for fld in sect.getSortedFields():
                if not fld.getPDField():
                    self._dispopts[sect.getId()].append("%s-%s"%(sect.getId(),fld.getId()))

    def _getKeyDispOpts(self, value):
        """
        Returns the key which contains the done value.
        """
        for key in self._dispopts.keys():
            if value in self._dispopts[key]:
                return key
        return None

    def _getColumnTitlesDict(self):
        """
            Dictionary with the translation from "ids" to "name to display" for each of the options you can choose for the display.
            This method complements the method "_setDispOpts" in which we get a dictonary with "ids".
        """
        try:
            if self._columns:
                pass
        except AttributeError:
            columns = {"PersonalData": _("Personal Data"),
                       "Id": _("Id"),
                       "statuses": _("Statuses"),
                       "LastName": _("Surname"),
                       "FirstName": _("First name"),
                       "Email": _("Email"),
                       "Position": _("Position"),
                       "Institution": _("Institution"),
                       "Phone": _("Phone"),
                       "City": _("City"),
                       "Country": _("Country"),
                       "Address": _("Address"),
                       "ArrivalDate": _("Arrival Date"),
                       "DepartureDate": _("Departure Date"),
                       "amountToPay": _("Amount"),
                       "idpayment": _("Payment ID"),
                       "isPayed": _("Paid"),
                       "eTicket": _("e-ticket"),
                       "checkedIn": _("Checked in"),
                       "checkInDate": _("Check in Date"),
                       "more": _("General info"),
                       "RegistrationDate": i18nformat(
                           """_("Registration date") (%s)""") % self._conf.getTimezone()
                       }

            tit = self._conf.getRegistrationForm().getSessionsForm().getTitle()
            if not self._conf.getRegistrationForm().getSessionsForm().isEnabled():
                tit = '%s <span style="color:red;font-size: 75%%">(disabled)</span>' % tit
            columns["Sessions"] = tit
            tit = self._conf.getRegistrationForm().getAccommodationForm().getTitle()
            if not self._conf.getRegistrationForm().getAccommodationForm().isEnabled():
                tit = '%s <span style="color:red;font-size: 75%%">(disabled)</span>' % tit
            columns["Accommodation"] = tit
            tit = self._conf.getRegistrationForm().getSocialEventForm().getTitle()
            if not self._conf.getRegistrationForm().getSocialEventForm().isEnabled():
                tit = '%s <span style="color:red;font-size: 75%%">(disabled)</span>' % tit
            columns["SocialEvents"] = tit
            tit = self._conf.getRegistrationForm().getReasonParticipationForm().getTitle()
            if not self._conf.getRegistrationForm().getReasonParticipationForm().isEnabled():
                tit = '%s <span style="color:red;font-size: 75%%">(disabled)</span>' % tit
            columns["ReasonParticipation"] = tit

            for st in self._conf.getRegistrationForm().getStatusesList(False):
                columns["s-%s" % st.getId()] = st.getCaption()
            for sect in self._conf.getRegistrationForm().getGeneralSectionFormsList():
                tit = sect.getTitle()
                if not sect.isEnabled():
                    tit = '%s <span style="color:red;font-size: 75%%">(disabled)</span>' % tit
                columns[sect.getId()] = tit
                ############
                # jmf-start
                #for fld in sect.getFields():
                #    columns["%s-%s"%(sect.getId(),fld.getId())]=fld.getCaption()
                for fld in sect.getSortedFields():
                    if not fld.getPDField():
                        columns["%s-%s" % (sect.getId(), fld.getId())] = fld.getCaption()
                # jmf-end
                ############
            self._columns = columns
        return self._columns

    def _getDisplay(self):
        """
            These are the 'display' options selected by the user. In case no options were selected we add some of them by default.
        """
        display = self._display[:]

        if display == []:
            display = ["Email", "Institution", "Phone", "City", "Country"]
            if self._conf.getModPay().isActivated():
                display.extend(["isPayed", "idpayment", "amountToPay"])
        return display

    def _getURL(self):
        #builds the URL to the contribution list page
        #   preserving the current filter and sorting status in the websesion
        url = urlHandlers.UHConfModifRegistrantList.getURL(self._conf)

        return url

    def _getStatusesHTML(self):
        self._statusesObjects = {}
        for st in self._conf.getRegistrationForm().getStatusesList(False):
            self._statusesObjects[st.getId()] = st
        return WRegistrantsFilterStatuses(self._statuses, self._filterCrit, self._statusesObjects).getHTML()

    def _getDispHTML(self):
        """
        Filtering criteria: table with all the options for the columns we need to display.
        """
        res = ["""<table width="100%%" cellpadding="0" cellspacing="0" valign="top">"""]
        columns = self._getColumnTitlesDict()
        checked = " checked"
        display = self._getDisplay()
        counter = 0
        # sorting dispopts by
        auxdict = {}
        for key in self._dispopts.keys():
            if not auxdict.has_key(len(self._dispopts[key])):
                auxdict[len(self._dispopts[key])] = []
            auxdict[len(self._dispopts[key])].append(key)
        auxlens = auxdict.keys()
        auxlens.sort()
        auxlens.reverse()
        dispoptssortedkeys = []
        for l in auxlens:
            for k in auxdict[l]:
                dispoptssortedkeys.append(k)
        #---end sorting
        for key in dispoptssortedkeys:
            if self._dispopts[key] == []:
                continue
            if counter == 0:
                res.append("""<tr>""")
            res.append("""<td style="border-bottom:1px solid lightgrey; width:33%%" valign="top" align="left"><span style="color:black"><b>%s</b></span><br>"""%(columns[key]))
            for keyfld in self._dispopts[key]:
                res.append("""<table width="100%%" cellpadding="0" cellspacing="0" valign="top">""")
                checked = ""
                if keyfld in display:
                    checked = " checked"
                res.append("""<tr><td align="left" valign="top"><input type="checkbox" name="disp" value="%s"%s></td><td width="100%%" align="left" valign="top">%s</td></tr>"""%(keyfld,checked,columns[keyfld].replace('<span style="color:red;font-size: 75%">(disabled)</span>','')))
                res.append("""</table>""")
            res.append("""</td>""")
            if counter == 2:
                counter = 0
                res.append("""</tr>""")

            else:
                counter += 1
        if counter in [1, 2]:
            res.append("""<td colspan="2" style="border-bottom:1px solid lightgrey; width:100%%">&nbsp;</td>""")
        res.append("""</table>""")
        return "".join(res)

    def _getRegColumnHTML(self, sortingField):
        """
        Titles for the columns of the list.
        """
        resgroups = {}
        columns = self._getColumnTitlesDict()
        currentSorting = ""
        if sortingField is not None:
            currentSorting = sortingField.getSpecialId()
        currentSortingHTML = ""
        display = self._getDisplay()
        resgroups["PersonalData"] = []
        if "Id" in display:
            url = self._getURL()
            url.addParam("sortBy", "Id")
            idImg = ""
            if currentSorting == "Id":
                currentSortingHTML = """<input type="hidden" name="sortBy" value="Id">"""
                if self._order == "down":
                    idImg = """<img src=%s alt="down">""" % (quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                    url.addParam("order", "up")
                elif self._order == "up":
                    idImg = """<img src=%s alt="up">""" % (quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                    url.addParam("order", "down")
            idSortingURL = quoteattr("%s#results" % str(url))
            resgroups["PersonalData"] = [i18nformat("""<td nowrap class="titleCellFormat" style="border-left:5px solid #FFFFFF;border-bottom: 1px solid #888;">%s<a href=%s> _("Id")</a></td>""") % (idImg, idSortingURL)]

        url = self._getURL()
        url.addParam("sortBy", "Name")
        nameImg = ""
        if currentSorting == "Name":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="Name">"""
            if self._order == "down":
                nameImg = """<img src=%s alt="down">""" % (quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order", "up")
            elif self._order == "up":
                nameImg = """<img src=%s alt="up">""" % (quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order", "down")
        nameSortingURL = quoteattr("%s#results" % str(url))

        resgroups["PersonalData"].append(i18nformat("""<td nowrap class="titleCellFormat" style="border-left:5px solid #FFFFFF;border-bottom: 1px solid #888;">%s<a href=%s> _("Name")</a></td>""") % (nameImg, nameSortingURL))
        if "Id" in display:
            pdil = ["Id", "Name"]
        else:
            pdil = ["Name"]
        self._groupsorder = {"PersonalData": pdil}  # list used to display the info of the registrants in the same order
        for key in display:
            if key == "Id" or not columns.has_key(key):
                continue
            url = self._getURL()
            url.addParam("sortBy", key)
            img = ""
            if currentSorting == key:
                currentSortingHTML = """<input type="hidden" name="sortBy" value="%s">""" % key
                if self._order == "down":
                    img = """<img src=%s alt="down">""" % (quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                    url.addParam("order", "up")
                elif self._order == "up":
                    img = """<img src=%s alt="up">""" % (quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                    url.addParam("order", "down")
            sortingURL = quoteattr("%s#results" % str(url))
            kg = self._getKeyDispOpts(key)
            if not resgroups.has_key(kg):
                self._groupsorder[kg] = []
                resgroups[kg] = []
            self._groupsorder[kg].append(key)
            resgroups[kg].append("""<td class="titleCellFormat" style="border-left:5px solid #FFFFFF;border-bottom: 1px solid #888;">%s<a href=%s>%s</a></td>"""%(img, sortingURL, self.htmlText(columns[key].replace('<span style="color:red;font-size: 75%">(disabled)</span>',''))))
        fields = ["""
                <tr>
                    <td align="right" nowrap></td>"""]
        # First we want to display the personal data...
        groupkey = "PersonalData"
        fields += resgroups[groupkey]
        del resgroups[groupkey]
        #...and them all the other info:
        for groupkey in resgroups.keys():
            fields += resgroups[groupkey]
        fields.append("""
                        </tr>
                        """)
        return "\r\n".join(fields)

    def _getDisplayOptionsHTML(self):
        html = []
        if self._display == []:
            html.append("""<input type="hidden" name="disp" value="Email">""")
            html.append("""<input type="hidden" name="disp" value="Institution">""")
            html.append("""<input type="hidden" name="disp" value="Phone">""")
            html.append("""<input type="hidden" name="disp" value="City">""")
            html.append("""<input type="hidden" name="disp" value="Country">""")
            html.append("""<input type="hidden" name="disp" value="isPayed">""")
            html.append("""<input type="hidden" name="disp" value="idpayment">""")
            html.append("""<input type="hidden" name="disp" value="amountToPay">""")
        else:
            for d in self._display:
                html.append("""<input type="hidden" name="disp" value="%s">""" % (d))
        html.append("""<input type="hidden" name="sortBy" value="%s">""" % (self._sortingCrit.getField().getId()))
        return "".join(html)

    def _getFilterMenu(self):

        regForm = self._conf.getRegistrationForm()

        options = [
            ('accomm', regForm.getAccommodationForm()),
            ('event', regForm.getSocialEventForm()),
            (self._sessionFilterName, regForm.getSessionsForm())
        ]

        extraInfo = ""
        if self._conf.getRegistrationForm().getStatusesList(False):
            extraInfo = i18nformat("""<table align="center" cellspacing="0" width="100%%">
                                <tr>
                                    <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #888; padding-right:10px">  _("Statuses") <img src=%s border="0" alt="Select all" onclick="javascript:selectStatuses()"><img src=%s border="0" alt="Unselect all" onclick="javascript:unselectStatuses()"></td>
                                </tr>
                                <tr>
                                    <td valign="top">%s</td>
                                </tr>
                            </table>
                        """) % (quoteattr(Config.getInstance().getSystemIconURL("checkAll")),quoteattr(Config.getInstance().getSystemIconURL("uncheckAll")), self._getStatusesHTML())

        p = WFilterCriteriaRegistrants(options, self._filterCrit, extraInfo)

        return p.getHTML()

    def _getDisplayMenu(self):
        menu = i18nformat("""<div class="CRLDiv" style="display: none;" id="displayMenu"><table width="95%%" align="center" border="0">
        <tr>
            <td>
                <table width="100%%">
                    <tr>
                        <td>

                        </td>
                    </tr>
                    <tr>
                        <td>
                            <table align="center" cellspacing="0" width="100%%">
                                <tr>
                                    <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #888; padding-right:10px" nowrap> <a onclick="selectDisplay()">_("Select all")</a> | <a onclick="unselectDisplay()">_("Unselect all")</a> </td>
                                </tr>
                                <tr>
                                    <td valign="top">%(disp)s</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td align="center"><input type="submit" class="btn" name="OK" value=  _("apply filter")></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table></div>""")
        return menu

    def getVars(self):

        vars = wcomponents.WTemplated.getVars(self)

        vars["conferenceId"] = self._conf.getId()
        vars["filterUrl"] = str(self._filterUrl)

        sortingField = self._sortingCrit.getField()
        vars["filterPostURL"] = quoteattr("%s#results" % str(urlHandlers.UHConfModifRegistrantList.getURL(self._conf)))
        cl = self._conf.getRegistrantsList(False)
        f = filters.SimpleFilter(self._filterCrit, self._sortingCrit)
        vars["eve"] = ""
        vars["columns"] = self._getRegColumnHTML(sortingField)
        filtered = f.apply(cl)

        regl = [reg.getId() for reg in filtered]
        if self._order == "up":
            filtered.reverse()
            regl.reverse()

        vars["registrants"] = zip(filtered, (registration.RegistrantMapping(reg) for reg in filtered))

        vars["filteredNumberRegistrants"] = str(len(filtered))
        vars["totalNumberRegistrants"] = str(len(cl))
        vars["filterUsed"] = self._filterUsed

        vars["actionPostURL"] = quoteattr(str(urlHandlers.UHConfModifRegistrantListAction.getURL(self._conf)))
        vars["reglist"] = ",".join(regl)

        vars["emailIconURL"] = """<input type="image" name="email" src=%s border="0">""" % quoteattr(str(Config.getInstance().getSystemIconURL("envelope")))
        vars["infoIconURL"] = """<input type="image" name="info" src=%s border="0">""" % quoteattr(str(Config.getInstance().getSystemIconURL("info")))
        vars["excelIconURL"] = quoteattr(str(Config.getInstance().getSystemIconURL("excel")))
        vars["pdfIconURL"] = quoteattr(str(Config.getInstance().getSystemIconURL("pdf")))
        vars["excelUrl"] = quoteattr(str(Config.getInstance().getSystemIconURL("excel")))

        vars["disp"] = self._getDispHTML()
        tit = self._conf.getRegistrationForm().getAccommodationForm().getTitle()
        if not self._conf.getRegistrationForm().getAccommodationForm().isEnabled():
            tit = '%s <span style="color:red;font-size: 75%%">(disabled)</span>' % tit
        vars["accomtitle"] = tit
        tit = self._conf.getRegistrationForm().getSessionsForm().getTitle()
        if not self._conf.getRegistrationForm().getSessionsForm().isEnabled():
            tit = '%s <span style="color:red;font-size: 75%%">(disabled)</span>' % tit
        vars["sesstitle"] = tit
        tit = self._conf.getRegistrationForm().getSocialEventForm().getTitle()
        if not self._conf.getRegistrationForm().getSocialEventForm().isEnabled():
            tit = '%s <span style="color:red;font-size: 75%%">(disabled)</span>' % tit
        vars["eventtitle"] = tit
        vars["displayOptions"] = self._getDisplayOptionsHTML()
        vars["sortingOptions"] = """<input type="hidden" name="sortBy" value="%s">
                                  <input type="hidden" name="order" value="%s">""" % (self._sortingCrit.getField().getId(), self._order)

        vars["checkAcco"] = """<img src=%s border="0" alt="Select all" onclick="javascript:selectAcco()">""" % quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckAcco"] = """<img src=%s border="0" alt="Unselect all" onclick="javascript:unselectAcco()">""" % quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))
        vars["checkEvent"] = """<img src=%s border="0" alt="Select all" onclick="javascript:selectEvent()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckEvent"] = """<img src=%s border="0" alt="Unselect all" onclick="javascript:unselectEvent()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))
        vars["checkSession"] = """<img src=%s border="0" alt="Select all" onclick="javascript:selectSession()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckSession"] = """<img src=%s border="0" alt="Unselect all" onclick="javascript:unselectSession()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))
        vars["checkDisplay"] = """<img src=%s border="0" alt="Select all" onclick="javascript:selectDisplay()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckDisplay"] = """<img src=%s border="0" alt="Unselect all" onclick="javascript:unselectDisplay()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))
        vars["displayMenu"] = self._getDisplayMenu()%vars
        vars["filterMenu"] = self._getFilterMenu()
        vars["groups_order"] = self._groupsorder
        vars["eTicketEnabled"] = self._conf.getRegistrationForm().getETicket().isEnabled()

        return vars

class WRegistrantsFilterStatuses (wcomponents.WTemplated):

    def __init__(self, statuses, filter, statusObjects):
        wcomponents.WTemplated.__init__(self)
        self._statuses = statuses
        self._filterCrit = filter
        self._statusObjects = statusObjects

    def getVars(self):

        vars = wcomponents.WTemplated.getVars( self )
        vars["statuses"] = self._statuses
        vars["filter"] = self._filterCrit
        vars["showNoAnswer"] = self._filterCrit.getField("statuses").getShowNoValue()
        vars["statusObjects"] = self._statusObjects

        return vars

class WFilterCriteriaRegistrants(wcomponents.WFilterCriteria):
    """
    Draws the options for a filter criteria object
    This means rendering the actual table that contains
    all the HTML for the several criteria
    """

    def __init__(self, options, filterCrit, extraInfo=""):
        wcomponents.WFilterCriteria.__init__(self, options, filterCrit, extraInfo)

    def _drawFieldOptions(self, formName, form):

        # since sessions have a special extra checkbox ("only by first choice"),
        # we need to use a different template

        if formName in ['session', 'sessionfirstpriority']:
            page = WFilterSessionCriterionOptions(formName, form, self._filterCrit)
        else:
            page = WFilterCriterionOptions(formName, form, self._filterCrit)

        return page.getHTML()

class WFilterCriterionOptions(wcomponents.WTemplated):
    """
    Draws the list of options (and checkboxes) for a specific filter criterion,
    with all the checkboxes (properly checked if necessary)
    """

    def __init__(self, formName, formData, filterCrit):
        self._formName = formName
        self._formData = formData
        self._filterCrit = filterCrit

    def getVars(self):
        parentVars = wcomponents.WTemplated.getVars( self )
        parentVars["critFormName"] = self._formName
        parentVars["htmlFormName"] = self._formName
        parentVars["form"] = self._formData
        parentVars["filterCrit"] = self._filterCrit

        return parentVars

class WFilterSessionCriterionOptions(WFilterCriterionOptions):
    """
    Sub-class for the session "criterion", since it requires an
    extra checkbox.
    """

    def getVars(self):
        parentVars = WFilterCriterionOptions.getVars( self )
        parentVars["htmlFormName"] = "session"

        return parentVars


class WRegSentMail  (wcomponents.WTemplated):
    def __init__(self,conf):
        self._conf = conf

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["BackURL"]=urlHandlers.UHConfModifRegistrantList.getURL(self._conf)
        return vars


class WPSentEmail( WPConfModifRegistrantListBase ):
    def _getTabContent(self,params):
        wc = WRegSentMail(self._conf)
        return wc.getHTML()


class WRegPreviewMail(wcomponents.WTemplated):
    def __init__(self,conf, params):
        self._conf = conf
        self._params=params

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        fromAddr=self._params.get("from","")
        cc=self._params.get("cc","")
        subject=self._params.get("subject","")
        body=self._params.get("body","")
        regsIds=self._params.get("regsIds",[])
        if type(regsIds) != list:
            regsIds=[regsIds]
        registrant=None
        if len(regsIds)>0:
            registrant=self._conf.getRegistrantById(regsIds[0])
        vars["From"]=  i18nformat("""<center>  _("No preview avaible") </center>""")
        vars["subject"]=  i18nformat("""<center>  _("No preview avaible") </center>""")
        vars["body"]=  i18nformat("""<center> _("No preview avaible") </center>""")
        vars["to"]=  i18nformat("""<center> _("No preview avaible") </center>""")
        vars["cc"]=  i18nformat("""<center> _("No preview avaible") </center>""")
        if registrant != None:
            notif=EmailNotificator().apply(registrant,{"subject":subject, "body":body, "from":fromAddr, "to":[registrant.getEmail()], "cc": [cc]})
            vars["From"]=notif.getFromAddr()
            vars["to"]=notif.getToList()
            vars["subject"]=notif.getSubject()
            vars["body"] = notif.getBody()
            vars["cc"] = notif.getCCList()
        vars["params"]=[]
        for regId in regsIds:
            vars["params"].append("""<input type="hidden" name="regsIds" value="%s">"""%(regId))
            vars["params"].append("""<input type="hidden" name="registrant" value="%s">"""%(regId))
        vars["params"].append("""<input type="hidden" name="from" value=%s>"""%(quoteattr(fromAddr)))
        vars["params"].append("""<input type="hidden" name="subject" value=%s>"""%(quoteattr(subject)))
        vars["params"].append("""<input type="hidden" name="body" value=%s>"""%(quoteattr(body)))
        vars["params"].append("""<input type="hidden" name="cc" value=%s>"""%(quoteattr(cc)))
        vars["params"]="".join(vars["params"])
        vars["postURL"]=urlHandlers.UHRegistrantsSendEmail.getURL(self._conf)
        vars["backURL"]=urlHandlers.UHConfModifRegistrantListAction.getURL(self._conf)
        return vars


class WPPreviewEmail( WPConfModifRegistrantListBase ):

    def __init__(self, rh, conf, params):
        WPConfModifRegistrantListBase.__init__(self, rh, conf)
        self._params = params

    def _getTabContent(self,params):
        wc = WRegPreviewMail(self._conf, self._params)
        return wc.getHTML()


class WEmailToRegistrants(wcomponents.WTemplated):
    def __init__(self, conf, user, reglist, fromA, cc, subject, body):
        self._conf = conf
        self._from = fromA
        self._cc = cc
        self._subject = subject
        self._body = body
        try:
            self._fromemail = self._from or user.getEmail()
        except:
            self._fromemail = ""
        self._regList = reglist

    def _getAvailableTagsHTML(self):
        res=[]
        for var in EmailNotificator.getVarList():
            res.append("""
                    <tr>
                            <td width="100%%" nowrap class="blacktext" style="padding-left:10px;padding-right:5px;">%s</td>
                            <td>%s</td>
                    </tr>"""%(self.htmlText(var.getLabel()),self.htmlText(var.getDescription())))
        return "".join(res)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        toEmails=[]
        toIds=[]
        for regId in self._regList:
            reg=self._conf.getRegistrantById(regId)
            if  reg!=None:
                toEmails.append(reg.getEmail())
                toIds.append("""<input type="hidden" name="regsIds" value="%s">"""%reg.getId())
        vars["From"] = self._fromemail
        vars["cc"] = self._cc
        vars["toEmails"]= ", ".join(toEmails)
        if vars["toEmails"] == "":
            vars["toEmails"] = "No registrants have been selected"
        vars["toIds"]= "".join(toIds)
        vars["postURL"]=urlHandlers.UHRegistrantsSendEmail.getURL(self._conf)
        vars["subject"] = self._subject
        vars["body"] = self._body
        vars["vars"]=self._getAvailableTagsHTML()
        return vars


class WPRegistrantModifRemoveConfirmation(WPConfModifRegistrantListBase):

    def __init__(self,rh, conf, registrantList):
        WPConfModifRegistrantListBase.__init__(self,rh,conf)
        self._regList = registrantList

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        regs = ''.join(list("<li>{0}</li>".format(
                    self._conf.getRegistrantById(reg).getFullName()) for reg in self._regList))

        msg = {
            'challenge': _("Are you sure you want to delete the following registrants?"),
            'target': "<ul>{0}</ul>".format(regs),
            'subtext': _("Please note you will permanently lose all the information about them")
            }

        url = urlHandlers.UHConfModifRegistrantPerformRemove.getURL(self._conf)
        return wc.getHTML(
            msg, url, {
                "registrants":self._regList
                })


class WPEMail ( WPConfModifRegistrantListBase ):
    def __init__(self, rh, conf, reglist, fromA, cc, subject, body):
        WPConfModifRegistrantListBase.__init__(self, rh, conf)
        self._regList = reglist
        self._from = fromA
        self._cc = cc
        self._subject = subject
        self._body = body

    def _getTabContent(self,params):
        wc = WEmailToRegistrants(self._conf, self._getAW().getUser(), self._regList, self._from, self._cc, self._subject, self._body)
        return wc.getHTML()

class WConfModifRegistrantsInfo(wcomponents.WTemplated):

    def __init__(self,conf,reglist):
        self._conf = conf
        self._reglist = reglist

    def _getAccommodationTypesInfoHTML(self):
        accoDict = {}
        for acco in self._conf.getRegistrationForm().getAccommodationForm().getAccommodationTypesList():
            if acco is not None:
                accoDict[acco]=0
        total = 0
        for reg in self._reglist:
            acco = reg.getAccommodation().getAccommodationType()
            if acco is not None:
                if accoDict.has_key(acco):
                    accoDict[acco] += 1
                else:
                    accoDict[acco] = 1
                total += 1
        html = []
        for acco in accoDict.keys():
            html.append("""
                <tr>
                    <td nowrap>%s</td>
                    <td>&nbsp;&nbsp;&nbsp;</td>
                    <td width="100%%" align="left"><b>%s</b></td>
                </tr>
                """%(acco.getCaption(), accoDict[acco]))
        html.sort()
        return "".join(html), total

    def _getSocialEventsInfoHTML(self):
        seCounter = {}
        seObj = {}
        for se in self._conf.getRegistrationForm().getSocialEventForm().getSocialEventList():
            if se is not None:
                seCounter[se.getId()]=0
                seObj[se.getId()]=se
        total = 0
        for reg in self._reglist:
            for se in reg.getSocialEvents():
                if se is not None:
                    if seCounter.has_key(se.getId()):
                        seCounter[se.getId()] += se.getNoPlaces()
                    else:
                        seCounter[se.getId()] = se.getNoPlaces()
                        seObj[se.getId()]=se
                    total += se.getNoPlaces()
        html = []
        for se in seCounter.keys():
            html.append("""
                <tr>
                    <td nowrap>%s</td>
                    <td>&nbsp;&nbsp;&nbsp;</td>
                    <td width="100%%" align="left"><b>%s</b></td>
                </tr>
                """%(seObj[se].getCaption(), seCounter[se]))
        html.sort()
        return "".join(html), total

    def _getSessionsInfoHTML(self):
        sesCounter = {}
        sesObj = {}
        for ses in self._conf.getRegistrationForm().getSessionsForm().getSessionList():
            if ses is not None:
                sesCounter[ses.getId()]=0
                sesObj[ses.getId()]=ses
        total = 0
        for reg in self._reglist:
            for ses in reg.getSessionList():
                if ses is not None:
                    if sesCounter.has_key(ses.getId()):
                        sesCounter[ses.getId()] += 1
                    else:
                        sesCounter[ses.getId()] = 1
                        sesObj[ses.getId()]=ses
                    total += 1
        html = []
        for ses in sesCounter.keys():
            html.append("""
                <tr>
                    <td nowrap>%s</td>
                    <td>&nbsp;&nbsp;&nbsp;</td>
                    <td width="100%%" align="left"><b>%s</b></td>
                </tr>
                """%(sesObj[ses].getTitle(), sesCounter[ses]))
        html.sort()
        return "".join(html), total

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["accommodationTypes"], vars["numAccoTypes"] = self._getAccommodationTypesInfoHTML()
        vars["socialEvents"], vars["numSocialEvents"] = self._getSocialEventsInfoHTML()
        vars["sessions"], vars["numSessions"] = self._getSessionsInfoHTML()
        vars["accoCaption"] = self._conf.getRegistrationForm().getAccommodationForm().getTitle()
        vars["socialEventsCaption"] = self._conf.getRegistrationForm().getSocialEventForm().getTitle()
        vars["sessionsCaption"] = self._conf.getRegistrationForm().getSessionsForm().getTitle()
        vars["backURL"]=quoteattr(str(urlHandlers.UHConfModifRegistrantList.getURL(self._conf)))
        return vars

class WPRegistrantsInfo ( WPConfModifRegistrantListBase ):

    def _getTabContent(self,params):
        reglist = params["reglist"]
        wc = WConfModifRegistrantsInfo(self._conf, reglist)
        return wc.getHTML()


class WPRegistrantBase( WPConferenceModifBase ):

    def __init__( self, rh, registrant ):
        self._registrant = self._target = registrant
        WPConferenceModifBase.__init__( self, rh, self._registrant.getConference() )


class WPRegistrantModifBase( WPRegistrantBase ):

    def _getNavigationDrawer(self):
        pars = {"target": self._conf, "isModif": True}
        return wcomponents.WNavigationDrawer( pars, bgColor = "white" )

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab("main", _("Main"),
                                             url_for("event_mgmt.confModifRegistrants-modification",
                                                     self._target))
        self._tabETicket = self._tabCtrl.newTab("eticket", _("e-ticket"),
                                                url_for("event_mgmt.confModifRegistrants-modification-eticket",
                                                        self._target))
        self._setActiveTab()
        self._setupTabCtrl()

        if not self._conf.getRegistrationForm().getETicket().isEnabled():
            self._tabETicket.disable()

    def _setActiveTab( self ):
        pass

    def _setupTabCtrl(self):
        pass

    def getCSSFiles(self):
        return WPRegistrantBase.getCSSFiles(self) + \
            self._asset_env['registrationform_sass'].urls()

    def _setActiveSideMenuItem(self):
        self._regFormMenuItem.setActive(True)

    def _getPageContent( self, params ):
        self._createTabCtrl()
        banner = wcomponents.WRegFormBannerModif(self._target).getHTML()
        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner+html

    def _getTabContent( self, params ):
        return  _("nothing")


class WPRegistrantModifETicket(WPRegistrantModifBase):

    def _setActiveTab(self):
        self._tabETicket.setActive()

    def _getTabContent(self, params):
        wc = WRegistrantModifETicket(self._registrant)
        return wc.getHTML()


class WRegistrantModifETicket(wcomponents.WTemplated):

    def __init__(self, registrant):
        self._registrant = registrant
        self._conf = self._registrant.getConference()

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["checkInUrl"] = url_for("event_mgmt.confModifRegistrants-modification-eticket-checkin",
                             self._registrant)
        vars["eTicketUrl"] = url_for("event.e-ticket-pdf",
                                     self._registrant,
                                     authkey=self._registrant.getRandomId())
        vars["isCheckedIn"] = self._registrant.isCheckedIn()
        checkInDate = self._registrant.getAdjustedCheckInDate()
        if checkInDate:
            vars["checkInDate"] = format_datetime(checkInDate)

        return vars


class WPRegistrantModifMain( WPRegistrantModifBase ):

    def _setActiveTab( self ):
        self._tabMain.setActive()


class WPRegistrantModification( WPRegistrantModifMain ):

    def _getTabContent( self, params ):
        wc = WRegistrantModifMain(self._registrant)
        return wc.getHTML()

class WRegistrantModifMain( wcomponents.WTemplated ):

    def __init__( self, registrant ):
        self._registrant = registrant
        self._conf = self._registrant.getConference()


    def _getTransactionHTML(self):
        if self._registrant.getPayed():
            total=0
            html=[]
            currency = ""
            html.append( i18nformat("""
                        <tr>
                        <tr><td colspan="4" class="title"><b> _("details") </b></td></tr>
                        <tr>
                            <td style="color:black"><b> _("Quantity") </b></td>
                            <td style="color:black"><b> _("Item") </b></td>
                            <td style="color:black"><b> _("Unit Price") </b></td>
                            <td style="color:black"><b> _("Cost") </b></td>
                            <td></td>
                        </tr>
                    """))
            for gsf in self._registrant.getMiscellaneousGroupList():
                regForm = self._conf.getRegistrationForm()
                miscGroup=self._registrant.getMiscellaneousGroupById(gsf.getId())

                if miscGroup is not None:
                    for miscItem in miscGroup.getResponseItemList():
                        _billlable=False
                        price=0.0
                        quantity=0
                        caption=miscItem.getCaption()
                        currency=miscItem.getCurrency()
                        v= i18nformat("""--  _("no value selected") --""")
                        if miscItem is not None:
                            v=miscItem.getValue()
                            if miscItem.isBillable():
                                _billlable=miscItem.isBillable()
                                caption=miscItem.getValue()
                                price=string.atof(miscItem.getPrice())
                                quantity=miscItem.getQuantity()
                                total+=price*quantity

                        gs = miscGroup.getGeneralSection()
                        disSect = ""
                        if not regForm.hasGeneralSectionForm(gs):
                            disSect = """ <span style="color:red">(disabled or removed)</span>"""
                        if(quantity>0):
                            html.append("""
                                    <tr>
                                       <td ><b>%i</b></td>
                                       <td>%s:%s</td>
                                       <td align="right"nowrap >%s</td>
                                       <td align="right"nowrap >%s&nbsp;&nbsp;%s</td>
                                       <td>%s</td>
                                    </tr>
                                    """%(quantity,gsf.getTitle(),caption,price,price*quantity,currency,disSect) )
            for bf in self._registrant.getBilledForms():
                for item in bf.getBilledItems():
                    caption = item.getCaption()
                    currency = item.getCurrency()
                    price = item.getPrice()
                    quantity = item.getQuantity()
                    total += price*quantity
                    if quantity > 0:
                        html.append("""
                                <tr>
                                   <td><b>%i</b></td>
                                   <td>%s</td>
                                   <td align="right" style="padding-right:10px" nowrap >%s</td>
                                   <td align="right"nowrap >%s&nbsp;&nbsp;%s</td>
                                   <td></td>
                                </tr>
                                """%(quantity, caption, price, price*quantity, currency))
            html.append( i18nformat("""
                        <tr>&nbsp;</tr>
                        <tr>
                           <td ><b> _("TOTAL") </b></td>
                           <td></td>
                           <td></td>
                           <td align="right"nowrap>%s&nbsp;&nbsp;%s</td>
                        </tr>
                        """)%(total,currency))
            transHTML = ""
            if self._registrant.getTransactionInfo():
                transHTML = self._registrant.getTransactionInfo().getTransactionHTML()
            return  i18nformat("""<form action=%s method="POST">
                            <tr>
                              <td class="dataCaptionTD"><span class="dataCaptionFormat">  _("Amount")</span></td>
                              <td bgcolor="white" class="blacktext">%s</td>
                              <td valign="bottom"><input type="submit" name="Payment" value="_("modify")"></td>
                            </tr>
                            <tr>
                              <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Payment")</span></td>
                              <td bgcolor="white" class="blacktext">%s</td>
                              <td valign="bottom"></td>
                            </tr>
                              <td class="dataCaptionTD"></td>
                              <td bgcolor="white" class="blacktext"><table>%s</table></td>
                              <td valign="bottom"></td>
                            </tr>
                            <tr>
                              <td colspan="3" class="horizontalLine">&nbsp;</td>
                            </tr>
                     </form>
                 """)%(quoteattr(str(urlHandlers.UHConfModifRegistrantTransactionModify.getURL(self._registrant))), "%.2f %s"%(self._registrant.getTotal(), self._registrant.getConference().getRegistrationForm().getCurrency()), transHTML,"".join(html))
        elif self._registrant.doPay():
            urlEpayment=""
            if self._registrant.getConference().getModPay().isActivated() and self._registrant.doPay():
                urlEpayment = """<br/><br/><i>Direct access link for epayment:</i><br/><small>%s</small>"""%escape(str(urlHandlers.UHConfRegistrationFormCreationDone.getURL(self._registrant)))
            return i18nformat(""" <form action=%s method="POST">
                            <tr>
                              <td class="dataCaptionTD"><span class="dataCaptionFormat">_("Amount")</span></td>
                              <td bgcolor="white" class="blacktext">%s</td>
                            </tr>
                            <tr>
                              <td class="dataCaptionTD"><span class="dataCaptionFormat">_("Payment")</span></td>
                              <td bgcolor="white" class="blacktext">%s%s</td>
                              <td valign="bottom"><input type="submit" name="Payment" value="_("modify")" class="btn"></td>
                            </tr>
                            <tr>
                              <td colspan="3" class="horizontalLine">&nbsp;</td>
                            </tr>
                            </form>
                            """)%(quoteattr(str(urlHandlers.UHConfModifRegistrantTransactionModify.getURL(self._registrant))), "%.2f %s"%(self._registrant.getTotal(), self._registrant.getConference().getRegistrationForm().getCurrency()),"unpaid",urlEpayment)
        else :
            return  i18nformat(""" <form action="" method="POST">
                            <tr>
                              <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Payment")</span></td>
                              <td bgcolor="white" class="blacktext">%s</td>
                              <td valign="bottom"></td>
                            </tr>
                            <tr>
                              <td colspan="3" class="horizontalLine">&nbsp;</td>
                            </tr>
                            </form>
                            """)%(" --- ")


    def _getSessionsHTML(self):
        regForm = self._conf.getRegistrationForm()
        sessions = self._registrant.getSessionList()
        if regForm.getSessionsForm().isEnabled():
            if regForm.getSessionsForm().getType() == "2priorities":
                session1 =  i18nformat("""<font color=\"red\">--  _("not selected") --</font>""")
                session2 =  i18nformat("""--  _("not selected") --""")
                if len(sessions) > 0:
                    session1 = sessions[0].getTitle()
                    if sessions[0].isCancelled():
                        session1 =  i18nformat("""%s <font color=\"red\">( _("cancelled") )""")%session1
                if len(sessions) > 1:
                    session2 = sessions[1].getTitle()
                    if sessions[1].isCancelled():
                        session2 =  i18nformat("""%s <font color=\"red\"> ( _("cancelled") )""")%session2
                text=  i18nformat("""
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
                return  i18nformat("""
                        <form action=%s method="POST">
                        <tr>
                          <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Sessions")</span></td>
                          <td bgcolor="white" class="blacktext">%s</td>
                          <td valign="bottom"><input type="submit" class="btn" name="sesmod" value="_("modify")"></td>
                        </tr>
                        <tr>
                          <td colspan="3" class="horizontalLine">&nbsp;</td>
                        </tr>
                        </form>
                        """)%(quoteattr(str(urlHandlers.UHConfModifRegistrantSessionModify.getURL(self._registrant))), text)
            if regForm.getSessionsForm().getType() == "all":
                sessionList =  i18nformat("""<font color=\"red\">--_("not selected")--</font>""")
                if len(sessions) > 0:
                    sessionList=["<ul>"]
                    for ses in sessions:
                        sesText = "<li>%s</li>"%ses.getTitle()
                        if ses.isCancelled():
                            sesText =  i18nformat("""<li>%s <font color=\"red\"> ( _("cancelled") )</font></li>""")%ses.getTitle()
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
                return  i18nformat("""
                        <form action=%s method="POST">
                        <tr>
                          <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Sessions")</span></td>
                          <td bgcolor="white" class="blacktext">%s</td>
                          <td valign="bottom"><input type="submit" class="btn" name="sesmod" value="_("modify")"></td>
                        </tr>
                        <tr>
                          <td colspan="3" class="horizontalLine">&nbsp;</td>
                        </tr>
                        </form>
                        """)%(quoteattr(str(urlHandlers.UHConfModifRegistrantSessionModify.getURL(self._registrant))), text)
        return ""

    def _getAccommodationHTML(self):
        regForm = self._conf.getRegistrationForm()
        if regForm.getAccommodationForm().isEnabled():
            accommodation = self._registrant.getAccommodation()
            accoType =   i18nformat("""<font color=\"red\">--_("not selected")--</font>""")
            cancelled = ""
            if accommodation is not None and accommodation.getAccommodationType() is not None:
                accoType = accommodation.getAccommodationType().getCaption()
                if accommodation.getAccommodationType().isCancelled():
                    cancelled =  i18nformat("""<font color=\"red\"> _("(disabled)")</font>""")
            arrivalDate =  i18nformat("""<font color=\"red\">--_("not selected")--</font>""")
            if accommodation is not None and accommodation.getArrivalDate() is not None:
                arrivalDate = accommodation.getArrivalDate().strftime("%d-%B-%Y")
            departureDate =  i18nformat("""<font color=\"red\">--_("not selected")--</font>""")
            if accommodation is not None and accommodation.getDepartureDate() is not None:
                departureDate = accommodation.getDepartureDate().strftime("%d-%B-%Y")
            text =  i18nformat("""
                        <table>
                          <tr>
                            <td align="right"><b> _("Arrival date"):</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b> _("Departure date"):</b></td>
                            <td align="left">%s</td>
                          </tr>
                          <tr>
                            <td align="right"><b> _("Accommodation type"):</b></td>
                            <td align="left">%s %s</td>
                          </tr>
                        </table>
                        """)%(arrivalDate, departureDate, \
                                accoType, cancelled)
            return  i18nformat("""
                    <form action=%s method="POST">
                    <tr>
                      <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Accommodation")</span></td>
                      <td bgcolor="white" class="blacktext">%s</td>
                      <td valign="bottom"><input type="submit" class="btn" name="acomod" value="_("modify")"></td>
                    </tr>
                    <tr>
                      <td colspan="3" class="horizontalLine">&nbsp;</td>
                    </tr>
                    </form>
                    """)%(quoteattr(str(urlHandlers.UHConfModifRegistrantAccoModify.getURL(self._registrant))), text)
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
                    cancelled =  i18nformat("""<font color=\"red\"> ( _("cancelled") )</font>""")
                    if se.getCancelledReason().strip():
                        cancelled =  i18nformat("""<font color=\"red\">( _("cancelled"): %s)</font>""")%se.getCancelledReason().strip()
                r.append( i18nformat("""
                            <tr>
                              <td align="left">%s <b>[%s _("place(s) needed")]</b> %s</td>
                            </tr>
                         """)%(se.getCaption(), se.getNoPlaces(), cancelled))
            if r == []:
                text = i18nformat("""--_("no social events selected")--""")
            else:
                text = """
                        <table>
                          %s
                        </table>
                        """%("".join(r))
            text = i18nformat("""
                    <form action=%s method="POST">
                    <tr>
                      <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Social events")</span></td>
                      <td bgcolor="white" class="blacktext">%s</td>
                      <td valign="bottom"><input type="submit" class="btn" name="socmod" value="_("modify")"></td>
                    </tr>
                    <tr>
                      <td colspan="3" class="horizontalLine">&nbsp;</td>
                    </tr>
                    </form>
                    """)%(quoteattr(str(urlHandlers.UHConfModifRegistrantSocialEventsModify.getURL(self._registrant))), text)
        return text

    def _getReasonParticipationHTML(self):
        regForm = self._conf.getRegistrationForm()
        if regForm.getReasonParticipationForm().isEnabled():
            return i18nformat("""
                    <form action=%s method="POST">
                    <tr>
                      <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Reason for participation") </span></td>
                      <td bgcolor="white" class="blacktext">%s</td>
                      <td valign="bottom"><input type="submit" class="btn" name="reamod" value="_("modify")"></td>
                    </tr>
                    <tr>
                      <td colspan="3" class="horizontalLine">&nbsp;</td>
                    </tr>
                    </form>
                    """)%(quoteattr(str(urlHandlers.UHConfModifRegistrantReasonPartModify.getURL(self._registrant))), self.htmlText( self._registrant.getReasonParticipation() ))
        return ""

    def _getItemValueDisplay(self, responseItem):
        value = responseItem.getValue()
        try:
            return responseItem.getGeneralField().getInput().getValueDisplay(value)
        except:
            return value

    def _getMiscInfoItemsHTML(self, gsf):
        miscGroup=self._registrant.getMiscellaneousGroupById(gsf.getId())
        html=["""<table>"""]
        #########
        #jmf start
        #for f in gsf.getFields():
        for f in gsf.getSortedFields():
        #jmf end
        #########
            miscItem=None
            if miscGroup is not None:
                miscItem=miscGroup.getResponseItemById(f.getId())
            v= i18nformat("""--_("no value selected")--""")
            if miscItem is not None:
                v = self._getItemValueDisplay(miscItem)
            html.append("""
                    <tr>
                       <td align="left" style="max-width: 25%%" valign="top"><b>%s:</b></td>
                       <td align="left" valign="top">%s</td>
                    </tr>
                    """%(f.getCaption(), v))
        if miscGroup is not None:
            for miscItem in miscGroup.getResponseItemList():
                    f=gsf.getFieldById(miscItem.getId())
                    if f is None:
                        html.append( _("""
                                    <tr>
                                       <td align="left" style="max-width: 25%%"><b>%s:</b></td>
                                       <td align="left">%s <font color="red">(cancelled)</font></td>
                                    </tr>
                                    """) %(miscItem.getCaption(), self._getItemValueDisplay(miscItem)) )
        if len(html)==1:
            html.append( i18nformat("""
                        <tr><td><font color="black"><i> --_("No fields")--</i></font></td></tr>
                        """))
        html.append("</table>")
        return "".join(html)

    def _getMiscellaneousInfoHTML(self, gsf):
        regForm = self._conf.getRegistrationForm()
        html=[]
        url=urlHandlers.UHConfModifRegistrantMiscInfoModify.getURL(self._registrant)
        url.addParam("miscInfoId", gsf.getId())
        html.append( i18nformat("""
            <form action=%s method="POST">
            <tr>
              <td class="dataCaptionTD" valign="top"><span class="dataCaptionFormat">%s</span></td>
              <td bgcolor="white" class="blacktext" valign="top">%s</td>
              <td valign="bottom"><input type="submit" class="btn" name="" value="_("modify")"></td>
            </tr>
            <tr>
              <td colspan="3" class="horizontalLine">&nbsp;</td>
            </tr>
            </form>
            """)%(quoteattr(str(url)), gsf.getTitle(), self._getMiscInfoItemsHTML(gsf) ) )
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
        return ''.join(x.encode('utf-8') if isinstance(x, unicode) else x for x in sects)

    def _getStatusesHTML(self):
        regForm = self._conf.getRegistrationForm()
        url=urlHandlers.UHConfModifRegistrantStatusesModify.getURL(self._registrant)
        if regForm.getStatusesList() == []:
            return ""
        html=["""<table>"""]
        for st in regForm.getStatusesList():
            rst=self._registrant.getStatusById(st.getId())
            vcap=" -- no value --"
            if rst.getStatusValue() is not None:
                vcap=rst.getStatusValue().getCaption()
            html.append("""
                        <tr>
                            <td align="left"><b>%s</b>: %s</td>
                        </tr>
                        """%(rst.getCaption(), vcap))
        html.append("""</table>""")
        html=[ i18nformat("""
                    <form action=%s method="POST">
                    <tr>
                      <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Statuses")</span></td>
                      <td bgcolor="white" class="blacktext">%s</td>
                      <td valign="bottom"><input type="submit" class="btn" name="" value="_("modify")"></td>
                    </tr>
                    <tr>
                      <td colspan="3" class="horizontalLine">&nbsp;</td>
                    </tr>
                    </form>
                    """)%(quoteattr(str(url)), "".join(html) ) ]
        return "".join(html)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["id"] = self._registrant.getId()
        vars["title"] = self.htmlText( self._registrant.getTitle() )
        vars["familyName"] = self.htmlText( self._registrant.getFamilyName() )
        vars["firstName"] = self.htmlText( self._registrant.getFirstName() )
        vars["position"] = self.htmlText( self._registrant.getPosition() )
        vars["institution"] = self.htmlText( self._registrant.getInstitution() )
        vars["address"] = self.htmlText( self._registrant.getAddress() )
        vars["city"] = self.htmlText( self._registrant.getCity() )
        vars["country"] = self.htmlText( CountryHolder().getCountryById(self._registrant.getCountry()) )
        vars["phone"] = self.htmlText( self._registrant.getPhone() )
        vars["fax"] = self.htmlText( self._registrant.getFax() )
        vars["email"] = self.htmlText( self._registrant.getEmail() )
        vars["personalHomepage"] = self.htmlText( self._registrant.getPersonalHomepage() )
        vars["registrationDate"] = i18nformat("""--_("date unknown")--""")
        if self._registrant.getRegistrationDate() is not None:
            vars["registrationDate"] = "%s (%s)"%(self._registrant.getAdjustedRegistrationDate().strftime("%d-%B-%Y %H:%M"), self._conf.getTimezone())
        vars["sections"] = self._getFormSections()
        vars["statuses"]=self._getStatusesHTML()

        vars["transaction"]=self._getTransactionHTML()
        return vars

class WConfModifRegistrantSessionsBase(wcomponents.WTemplated):

    def __init__(self, registrant):
        self._registrant = registrant
        self._conf = self._registrant.getConference()
        self._sessionForm = self._conf.getRegistrationForm().getSessionsForm()

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self._sessionForm.getTitle()
        return vars

class WConfModifRegistrantSessions2PrioritiesModify(WConfModifRegistrantSessionsBase):

    def _getSessionsHTML(self, selectName, sessionValue):
        selected = ""
        if sessionValue is None:
            selected = "selected"
        html = [ i18nformat("""<select name="%s">
                        <option value="nosession" %s>--_("None selected")--</option>""")%(selectName, selected)]
        for ses in self._sessionForm.getSessionList(True):
            selected = ""
            if (ses and sessionValue) and ses.getId() == sessionValue.getId():
                selected = "selected"
            html.append("""
                    <option value="%s" %s>%s</option>
                    """%(ses.getId(), selected, ses.getTitle()) )
        html = """%s</select>"""%("".join(html))
        return html

    def getVars(self):
        vars = WConfModifRegistrantSessionsBase.getVars( self )
        ses1 = None
        if len(self._registrant.getSessionList())>0:
            ses1 = self._registrant.getSessionList()[0]
        vars ["sessions1"] = self._getSessionsHTML("session1", ses1)
        ses2 = None
        if len(self._registrant.getSessionList())>1:
            ses2 = self._registrant.getSessionList()[1]
        vars["sessions2"] = self._getSessionsHTML("session2", ses2)
        return vars



class WPRegistrantTransactionModify( WPRegistrantModifMain ):

    def _getTabContent( self, params ):
        wc = WConfModifRegistrantTransactionModify(self._registrant)
        p={"postURL":quoteattr(str(urlHandlers.UHConfModifRegistrantTransactionPeformModify.getURL(self._registrant)))}
        return wc.getHTML(p)

class WConfModifRegistrantTransactionModify(WConfModifRegistrantSessionsBase):

    def _getTransactionHTML(self):
        transaction = self._registrant.getTransactionInfo()
        tmp=""
        checkedYes=""
        checkedNo=""
        if (transaction is None):
            checkedNo="selected"
        elif (transaction is None or transaction.isChangeable()):
            checkedYes="selected"
        tmp=  i18nformat("""<select name="isPayed"><option value="yes" %s> _("yes")</option><option value="no" %s> _("no")</option></select>""")%(checkedYes, checkedNo)
        return tmp

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars ["transation"] = self._getTransactionHTML()
        vars ["price"] = self._registrant.getTotal()
        vars ["Currency"] = self._registrant.getRegistrationForm().getCurrency()
        return vars

class WPRegistrantSessionModify( WPRegistrantModifMain ):

    def _getTabContent( self, params ):
        if self._registrant.getRegistrationForm().getSessionsForm().getType()=="all":
            wc = WConfModifRegistrantSessionsAllModify(self._registrant)
        else:
            wc = WConfModifRegistrantSessions2PrioritiesModify(self._registrant)
        p={"postURL":quoteattr(str(urlHandlers.UHConfModifRegistrantSessionPeformModify.getURL(self._registrant)))}
        return wc.getHTML(p)

class WConfModifRegistrantSessionsAllModify(WConfModifRegistrantSessionsBase):

    def _getSessionsHTML(self, alreadyPaid):
        html=[]
        registeredSessions = [ses.getRegSession() for ses in self._registrant.getSessionList()]
        for session in self._registrant.getRegistrationForm().getSessionsForm().getSessionList():
            selected=""
            if session in registeredSessions:
                selected=" checked"
            disabled = ""
            if alreadyPaid and session.isBillable():
                disabled = " disabled"
            price = ""
            if session.isBillable() and self._sessionForm.getType() != "2priorities":
                price = " [%s %s]" % (session.getPrice(), self._conf.getRegistrationForm().getCurrency())
            html.append("""<input type="checkbox" name="sessions" value="%s"%s%s>%s%s"""%(session.getId(), selected, disabled, session.getTitle(), price) )
        return "<br>".join(html)

    def getVars(self):
        vars = WConfModifRegistrantSessionsBase.getVars( self )
        vars ["sessions"] = self._getSessionsHTML(self._registrant.getPayed())
        return vars

class WConfModifRegistrantAccommodationModify(wcomponents.WTemplated):

    def __init__(self, registrant):
        self._registrant = registrant
        self._conf = self._registrant.getConference()
        self._accommodation = self._conf.getRegistrationForm().getAccommodationForm()

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
        html = ["""
                <select name="%s"%s>
                <option value="nodate" %s>-- select a date --</option>
                """%(name, disabled, selected)]
        for date in dates:
            selected = ""
            if currentDate is not None and currentDate.strftime("%d-%B-%Y") == date.strftime("%d-%B-%Y"):
                selected = "selected"
            html.append("""
                        <option value=%s %s>%s</option>
                        """%(quoteattr(str(date.strftime("%d-%m-%Y"))), selected, date.strftime("%d-%B-%Y")))
        html.append("</select>")
        return "".join(html)

    def _getAccommodationTypesHTML(self, currentAccoType, alreadyPaid):
        html=[]
        for type in self._accommodation.getAccommodationTypesList():
            if not type.isCancelled():
                selected = ""
                disabled = ""
                if currentAccoType == type:
                    selected = "checked=\"checked\""
                if alreadyPaid and (type.isBillable() or (currentAccoType and currentAccoType.isBillable())):
                    disabled = ' disabled="disabled"'
                priceCol = ""
                if type.isBillable():
                    priceCol = """<td align="right">%s %s per night</td>""" % (type.getPrice(), type.getRegistrationForm().getCurrency())
                html.append("""<tr>
                                    <td align="left" style="padding-left:10px"><input type="radio" name="accommodation_type" value="%s" %s%s>%s</td>
                                    %s
                                </tr>
                            """%(type.getId(), selected, disabled, type.getCaption(), priceCol ) )
            else:
                html.append( i18nformat("""<tr>
                                 <td align="left" style="padding-left:10px">&nbsp;&nbsp;&nbsp;<b>-</b> %s <font color="red">( _("not available at present") )</font></td>
                               </tr>
                            """)%(type.getCaption() ) )
        if currentAccoType is not None and currentAccoType.isCancelled() and currentAccoType not in self._accommodation.getAccommodationTypesList():
            html.append("""<tr>
                                <td align="left" style="padding-left:10px">&nbsp;&nbsp;&nbsp;<b>-</b> %s <font color="red">( _("not available at present") )</font></td>
                            </tr>
                        """%(currentAccoType.getCaption() ) )
        return "".join(html)


    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        acco = self._registrant.getAccommodation()
        currentArrivalDate = None
        currentDepartureDate = None
        currentAccoType = None
        alreadyPaid = self._registrant.getPayed()
        if acco is not None:
            currentArrivalDate = acco.getArrivalDate()
            currentDepartureDate = acco.getDepartureDate()
            currentAccoType = acco.getAccommodationType()
            alreadyPaidAcco = alreadyPaid and acco.isBillable()
        vars["title"] = self._accommodation.getTitle()
        vars["arrivalDate"] = self._getDatesHTML("arrivalDate", currentArrivalDate, alreadyPaid=alreadyPaidAcco)
        vars["departureDate"] = self._getDatesHTML("departureDate", currentDepartureDate, alreadyPaid=alreadyPaidAcco)
        vars["accommodationTypes"] = self._getAccommodationTypesHTML(currentAccoType, alreadyPaid)
        return vars

class WPRegistrantAccommodationModify( WPRegistrantModifMain ):

    def _getTabContent( self, params ):
        wc = WConfModifRegistrantAccommodationModify(self._registrant)
        p={"postURL":quoteattr(str(urlHandlers.UHConfModifRegistrantAccoPeformModify.getURL(self._registrant)))}
        return wc.getHTML(p)

class WConfModifRegistrantSocialEventsModify(wcomponents.WTemplated):

    def __init__(self, registrant):
        self._registrant = registrant
        self._conf = self._registrant.getConference()
        self._socialEvents = self._conf.getRegistrationForm().getSocialEventForm()

    def _getSocialEventsHTML(self, socialEvents=[], alreadyPaid=False):
        html=[]
        for se in self._socialEvents.getSocialEventList():
            if not se.isCancelled():
                checked = ""
                for ser in socialEvents:
                    if se == ser.getSocialEventItem():
                        se = ser
                        checked = "checked=\"checked\""
                        break
                optList = []
                for i in range(1, 10):
                    selected = ""
                    if isinstance(se, registration.SocialEvent) and i == se.getNoPlaces():
                        selected = " selected"
                    optList.append("""<option value="%s"%s>%s"""%(i, selected, i))

                priceCol = ""
                disabled = ""
                if se.isBillable():
                    perPlace = ""
                    if se.isPricePerPlace():
                        perPlace = '&nbsp;<acronym title="" onmouseover="IndicoUI.Widgets.Generic.tooltip(this, event, \'per place\')">pp</acronym>'
                    priceCol = """<td align="left" nowrap>%s&nbsp;%s%s</td>""" % (se.getPrice(), self._conf.getRegistrationForm().getCurrency(), perPlace)
                    if alreadyPaid:
                        disabled = ' disabled="disabled"'

                html.append("""<tr>
                                    <td align="left" nowrap style="padding-left:10px"><input type="checkbox" name="socialEvents" value="%s" %s%s>%s&nbsp;&nbsp;
                                    </td>
                                    <td align="left" nowrap>
                                    <select name="places-%s"%s>
                                       %s
                                    </select>
                                    </td>
                                    %s
                                </tr>
                            """%(se.getId(), checked, disabled, se.getCaption(), se.getId(), disabled, "".join(optList), priceCol ) )
            else:
                cancelledReason = "(cancelled)"
                if se.getCancelledReason().strip():
                    cancelledReason = "(cancelled: %s)"%se.getCancelledReason().strip()
                html.append("""<tr>
                                        <td align="left" colspan="2" nowrap style="padding-left:10px">&nbsp;&nbsp;&nbsp;<b>-</b> %s <font color="red">%s</font></td>
                                    </tr>
                                """%(se.getCaption(), cancelledReason ) )
        for se in socialEvents:
            if se.isCancelled and se.getSocialEventItem() not in self._socialEvents.getSocialEventList():
                cancelledReason = "cancelled"
                if se.getCancelledReason().strip():
                    cancelledReason = "(cancelled: %s)"%se.getCancelledReason().strip()
                html.append("""<tr>
                                    <td align="left" colspan="2" nowrap style="padding-left:10px">&nbsp;&nbsp;&nbsp;<b>-</b> %s <font color="red">%s</font></td>
                                </tr>
                            """%(se.getCaption(), cancelledReason ) )
        return "".join(html)


    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        regSocialEvents = self._registrant.getSocialEvents()
        vars["title"] = self._socialEvents.getTitle()
        vars["socialEvents"] = self._getSocialEventsHTML(regSocialEvents, self._registrant.getPayed())
        return vars

class WPRegistrantSocialEventsModify( WPRegistrantModifMain ):

    def _getTabContent( self, params ):
        wc = WConfModifRegistrantSocialEventsModify(self._registrant)
        p={"postURL":quoteattr(str(urlHandlers.UHConfModifRegistrantSocialEventsPeformModify.getURL(self._registrant)))}
        return wc.getHTML(p)

class WConfModifRegistrantReasonParticipationModify(wcomponents.WTemplated):

    def __init__(self, registrant):
        self._registrant = registrant
        self._conf = self._registrant.getConference()
        self._reasonParticipation = self._conf.getRegistrationForm().getReasonParticipationForm()


    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self._reasonParticipation.getTitle()
        vars["reasonParticipation"] = self._registrant.getReasonParticipation()
        return vars

class WPRegistrantReasonParticipationModify( WPRegistrantModifMain ):

    def _getTabContent( self, params ):
        wc = WConfModifRegistrantReasonParticipationModify(self._registrant)
        p={"postURL":quoteattr(str(urlHandlers.UHConfModifRegistrantReasonPartPeformModify.getURL(self._registrant)))}
        return wc.getHTML(p)

class WConfModifRegistrantMiscInfoModify(wcomponents.WTemplated):

    def __init__(self, miscGroup):
        self._miscGroup = miscGroup
        self._registrant = self._miscGroup.getRegistrant()
        self._conf = self._registrant.getConference()

    def _getFieldsHTML(self):
        html=[]
        ############
        # jmf-start
        #for f in self._miscGroup.getGeneralSection().getFields():
        for f in self._miscGroup.getGeneralSection().getSortedFields():
            if f.isDisabled():
                continue
        # jmf-start
        ############
            v=""
            miscItem = None
            if self._miscGroup.getResponseItemById(f.getId()) is not None:
                miscItem=self._miscGroup.getResponseItemById(f.getId())
                v=miscItem.getValue()
                price=v=miscItem.getPrice()
            columCaption = colspan = ""
            labelCol = f.getInput().getModifLabelCol()
            if labelCol:
                columCaption = """<td nowrap="nowrap" valign="top">%s</td>
                            <td valign="top" style="width:10px;">%s</td>""" % (labelCol,
                                                                               f.getInput().getMandatoryCol(miscItem))
            else:
                colspan = "colspan='3'"

            html.append("""
                        <tr>
                          %s
                          <td %s>
                             %s
                          </td>
                        </tr>
                        """%(columCaption, colspan, f.getInput().getModifHTML(miscItem, self._registrant)) )
        return "".join(html)


    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self._miscGroup.getTitle()
        vars["fields"] = self._getFieldsHTML()
        return vars

class WPRegistrantMiscInfoModify( WPRegistrantModifMain ):

    def __init__( self, rh, miscGroup ):
        WPRegistrantModifMain.__init__( self, rh, miscGroup.getRegistrant() )
        self._miscGroup=miscGroup

    def _getTabContent( self, params ):
        wc = WConfModifRegistrantMiscInfoModify(self._miscGroup)
        p={"postURL":quoteattr(str(urlHandlers.UHConfModifRegistrantMiscInfoPerformModify.getURL(self._miscGroup)))}
        return wc.getHTML(p)

class WConfModifRegistrantStatusesModify(wcomponents.WTemplated):

    def __init__(self, reg):
        self._conf = reg.getConference()
        self._registrant = reg

    def _getStatusHTML(self, st):
        html=["""<table>"""]
        rst=self._registrant.getStatusById(st.getId())
        somechecked=False
        for v in st.getStatusValuesList():
            checked=""
            if rst.getStatusValue() is not None and v.getId() == rst.getStatusValue().getId():
                somechecked=True
                checked=" checked"
            html.append("""
                        <tr><td><input type="radio" name="statuses-%s" value="%s"%s>%s</td></tr>
                        """%(st.getId(), v.getId(), checked, v.getCaption()))
        checked=""
        if not somechecked:
            checked=" checked"
        html.insert(1, i18nformat("""
                        <tr><td><input type="radio" name="statuses-%s" value="novalue"%s>--_("no value")--</td></tr>
                        """)%(st.getId(), checked))
        html.append("""</table>""")
        return "".join(html)


    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        html=["""<table border="0" cellpadding="0" cellspacing="0" valign="top">"""]
        for st in self._conf.getRegistrationForm().getStatusesList():
            html.append("""
                        <tr>
                          <td align="right" valign="top" style="border-bottom:1px solid #777777"><b>%s:</b> </td>
                          <td align="left" valign="top" style="border-bottom:1px solid #777777">%s</td>
                        </tr>
                        """%(st.getCaption(), self._getStatusHTML(st)))
        html.append("""</table>""")
        vars["statuses"]="".join(html)
        return vars

class WPRegistrantStatusesModify( WPRegistrantModifMain ):

    def _getTabContent( self, params ):
        wc = WConfModifRegistrantStatusesModify(self._registrant)
        p={"postURL":quoteattr(str(urlHandlers.UHConfModifRegistrantStatusesPerformModify.getURL(self._registrant)))}
        return wc.getHTML(p)

# ----------------- DISPLAY AREA ---------------------------

class WPConfRegistrantsList( WPConferenceDefaultDisplayBase ):

    def _getBody( self, params ):
        sortingCrit=params.get("sortingCrit",None)
        filterCrit=params.get("filterCrit",None)
        sessionFilterName=params.get("sessionFilterName", "session")
        order = params.get("order",None)
        wc = WConfRegistrantsList( self._conf, filterCrit, sortingCrit, order, sessionFilterName)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._registrantsListOpt)


class WConfRegistrantsList(WConfDisplayBodyBase):

    _linkname = "registrants"

    def __init__(self, conference, filterCrit, sortingCrit, order, sessionFilterName):
        self._conf = conference
        self._regForm = self._conf.getRegistrationForm()
        self._filterCrit = filterCrit
        self._sortingCrit = sortingCrit
        self._order = order
        self._sessionFilterName = sessionFilterName

    def _getURL(self):
        #builds the URL to the contribution list page
        #   preserving the current filter and sorting status
        url = urlHandlers.UHConfRegistrantsList.getURL(self._conf)
#        if self._filterCrit.getField("accomm"):
#            url.addParam("accomm",self._filterCrit.getField("accomm").getValues())
#            if self._filterCrit.getField("accomm").getShowNoValue():
#                url.addParam("accommShowNoValue","1")
#
        if self._filterCrit.getField(self._sessionFilterName):
            url.addParam("session", self._filterCrit.getField(self._sessionFilterName).getValues())
            if self._filterCrit.getField(self._sessionFilterName).getShowNoValue():
                url.addParam("sessionShowNoValue", "1")

        if self._sessionFilterName == "sessionfirstpriority":
            url.addParam("firstChoice", "1")
#
#        if self._filterCrit.getField("event"):
#            url.addParam("event",self._filterCrit.getField("event").getValues())
#            if self._filterCrit.getField("event").getShowNoValue():
#                url.addParam("eventShowNoValue","1")
#
        if self._sortingCrit.getField():
            url.addParam("sortBy", self._sortingCrit.getField().getId())
            url.addParam("order", "down")

#        url.addParam("disp",self._getDisplay())

        return url

    def _getRegistrantsHTML(self, reg):
        fullName = reg.getFullName()
        institution = ""
        if not self._regForm.getPersonalData().getField("institution").isDisabled():
            institution = """<td valign="top" class="abstractDataCell">%s</td>"""%(self.htmlText(reg.getInstitution()) or "&nbsp;")
        position = ""
        if not self._regForm.getPersonalData().getField("position").isDisabled():
            position = """<td valign="top" class="abstractDataCell">%s</td>"""%(self.htmlText(reg.getPosition()) or "&nbsp;")
        city = ""
        if not self._regForm.getPersonalData().getField("city").isDisabled():
            city = """<td valign="top" class="abstractDataCell">%s</td>"""%(self.htmlText(reg.getCity()) or "&nbsp;")
        country = ""
        if not self._regForm.getPersonalData().getField("country").isDisabled():
            country = """<td valign="top" class="abstractDataCell">%s</td>"""%(self.htmlText(CountryHolder().getCountryById(reg.getCountry())) or "&nbsp;")
        sessions=""
        if self._regForm.getSessionsForm().isEnabled():
            sessionList = []
            for ses in reg.getSessionList():
                sessionList.append(self.htmlText(ses.getCode()))
            sessions = "<br>".join(sessionList)
            sessions = """<td valign="top" class="abstractDataCell" nowrap>%s</td>"""%(sessions or "&nbsp;")
        html = """
            <tr>
                <td valign="top" nowrap class="abstractDataCell">%s</td>
                %s
                %s
                %s
                %s
                %s
            </tr>
                """%(self.htmlText(fullName),
                    institution,
                    position, city,
                    country,
                    sessions)
        return html

    def _getSessHTML(self):
        sessform = self._regForm.getSessionsForm()
        sesstypes = sessform.getSessionList()
        checked = ""
        if self._filterCrit.getField(self._sessionFilterName).getShowNoValue():
            checked = " checked"
        res = [i18nformat("""<input type="checkbox" name="sessionShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for sess in sesstypes:
            checked = ""
            if sess.getId() in self._filterCrit.getField(self._sessionFilterName).getValues():
                checked = " checked"
            res.append("""<input type="checkbox" name="session" value=%s%s>%s""" % (quoteattr(str(sess.getId())), checked, self.htmlText(sess.getTitle())))
        if sessform.getType() == "2priorities":
            checked = ""
            if self._sessionFilterName == "sessionfirstpriority":
                checked = " checked"
            res.append(i18nformat("""<b>------</b><br><input type="checkbox" name="firstChoice" value="firstChoice"%s><i> _("Only by first choice") </i>""") % checked)
        return "<br>".join(res)

    def _getFilterOptionsHTML(self, currentSortingHTML):
        filterPostURL = quoteattr("%s#results" % str(urlHandlers.UHConfRegistrantsList.getURL(self._conf)))
        return i18nformat("""<tr>
        <td width="100%%">
                    <br>
                    <form action=%s method="POST">
                        %s
                        <table width="100%%" align="center" border="0" style="border-left: 1px solid #777777;border-top: 1px solid #777777;">
                            <tr>
                                <td class="groupTitle" style="background:#E5E5E5; color:gray">&nbsp;&nbsp;&nbsp; _("Display options") </td>
                            </tr>
                            <tr>
                                <td>
                                    <table width="100%%">
                                        <tr>
                                            <td>
                                                <table align="center" cellspacing="10" width="100%%">
                                                    <tr>
                                                        <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> _("show sessions") </td>
                                                    </tr>
                                                    <tr>
                                                        <td valign="top" style="border-right:1px solid #777777;">%s</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="center" style="border-top:1px solid #777777;padding:10px"><input type="submit" class="btn" name="OK" value="_("apply filter")"></td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </form>
        </td>
            </tr>
                """) % (filterPostURL, currentSortingHTML, self._getSessHTML())

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["regForm"] = self._regForm
        l = []
        lr = self._conf.getRegistrantsList(True)
        f = filters.SimpleFilter(self._filterCrit, self._sortingCrit)
        for rp in f.apply(lr):
            l.append(self._getRegistrantsHTML(rp))
        if self._order == "up":
            l.reverse()
        wvars["registrants"] = "".join(l)
        wvars["numRegistrants"] = str(len(l))

        # Head Table Titles
        currentSorting=""
        if self._sortingCrit.getField() is not None:
            currentSorting=self._sortingCrit.getField().getSpecialId()

        currentSortingHTML = ""
        # --- Name
        url=self._getURL()
        url.addParam("sortBy","Name")
        nameImg=""
        wvars["imgNameTitle"]=""
        if currentSorting == "Name":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="Name">"""
            if self._order == "down":
                wvars["imgNameTitle"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                wvars["imgNameTitle"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        wvars["urlNameTitle"]=quoteattr("%s#results"%str(url))

        # --- Institution
        url=self._getURL()
        url.addParam("sortBy","Institution")
        nameImg=""
        wvars["imgInstitutionTitle"]=""
        if currentSorting == "Institution":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="Institution">"""
            if self._order == "down":
                wvars["imgInstitutionTitle"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                wvars["imgInstitutionTitle"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        wvars["urlInstitutionTitle"]=quoteattr("%s#results"%str(url))

        # --- Position
        url=self._getURL()
        url.addParam("sortBy","Position")
        nameImg=""
        wvars["imgPositionTitle"]=""
        if currentSorting == "Position":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="Position">"""
            if self._order == "down":
                wvars["imgPositionTitle"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                wvars["imgPositionTitle"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        wvars["urlPositionTitle"]=quoteattr("%s#results"%str(url))

        # --- City
        url=self._getURL()
        url.addParam("sortBy","City")
        nameImg=""
        wvars["imgCityTitle"]=""
        if currentSorting == "City":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="City">"""
            if self._order == "down":
                wvars["imgCityTitle"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                wvars["imgCityTitle"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        wvars["urlCityTitle"]=quoteattr("%s#results"%str(url))


        # --- Country
        url=self._getURL()
        url.addParam("sortBy","Country")
        nameImg=""
        wvars["imgCountryTitle"]=""
        if currentSorting == "Country":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="Country">"""
            if self._order == "down":
                wvars["imgCountryTitle"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                wvars["imgCountryTitle"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        wvars["urlCountryTitle"]=quoteattr("%s#results"%str(url))

        # --- Sessions

        wvars["sessionsTitle"] = ""

        if self._regForm.getSessionsForm().isEnabled():
            url=self._getURL()
            url.addParam("sortBy","Sessions")
            nameImg=""
            imgSessionTitle=""
            if currentSorting == "Sessions":
                currentSortingHTML = """<input type="hidden" name="sortBy" value="Sessions">"""
                if self._order == "down":
                    imgSessionTitle = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                    url.addParam("order","up")
                elif self._order == "up":
                    imgSessionTitle = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                    url.addParam("order","down")
            urlSessionTitle=quoteattr("%s#results"%str(url))
            wvars["sessionsTitle"] = """<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%s<a href=%s>%s</a></td>"""%(imgSessionTitle, urlSessionTitle, self._conf.getRegistrationForm().getSessionsForm().getTitle())

        # --- Filter Options
        wvars["filterOptions"]=""
        if self._regForm.getSessionsForm().isEnabled():
            wvars["filterOptions"]=self._getFilterOptionsHTML(currentSortingHTML)
        return wvars
#------------------------------------------------------------------------------------------------------------------------
"""
Badge Printing classes
"""
class WRegistrantModifPrintBadges( wcomponents.WTemplated ):

    def __init__( self, conference, selectedRegistrants, user=None ):
        self.__conf = conference
        self._user=user
        self.__selectedRegistrants = selectedRegistrants

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars['CreatePDFURL']=str(urlHandlers.UHConfModifBadgePrintingPDF.getURL(self.__conf))
        vars['registrantNamesList'] = "; ".join([self.__conf.getRegistrantById(id).getFullName() for id in self.__selectedRegistrants])
        vars['registrantList'] = ",".join(self.__selectedRegistrants)
        vars['badgeDesignURL'] = str(urlHandlers.UHConfModifBadgePrinting.getURL(self.__conf))

        templateListHTML = []
        first = True

        nTemplates = len(self.__conf.getBadgeTemplateManager().getTemplates())
        nColumns = 3
        nPerColumn = int(math.ceil(nTemplates / nColumns))

        n = 0
        templateListHTML.append("""              <tr>""")

        sortedTemplates = self.__conf.getBadgeTemplateManager().getTemplates().items()
        sortedTemplates.sort(lambda item1, item2: cmp(item1[1].getName(), item2[1].getName()))
        for templateId, template in sortedTemplates:

            templateListHTML.append("""                <td>""")

            radio = []
            radio.append("""                  <input type="radio" name="templateId" value='""")
            radio.append(str(templateId))
            radio.append("""' id='""")
            radio.append(str(templateId))
            radio.append("""'""")
            if first:
                first = False
                radio.append(""" CHECKED """)
            radio.append(""">""")
            templateListHTML.append("".join(radio))
            templateListHTML.append("".join (["""                  """,
                                              """<label for='""",
                                              str(templateId),
                                              """'>""",
                                              template.getName(),
                                              """</label>""",
                                              """&nbsp;&nbsp;&nbsp;"""]))

            templateListHTML.append("""                </td>""")

            n = n + 1
            if n == nPerColumn + 1:
                n = 0
                templateListHTML.append("""              </tr>""")
                templateListHTML.append("""              <tr>""")



        templateListHTML.append("""              </tr>""")
        vars["templateList"] = "\n".join(templateListHTML)

        wcPDFOptions = WConfModifBadgePDFOptions(self.__conf)
        vars['PDFOptions'] = wcPDFOptions.getHTML()

        return vars


class WPRegistrantModifPrintBadges( WPConfModifRegistrantListBase ):

    def __init__(self, rh, conf, selectedRegistrants):
        WPConfModifRegistrantListBase.__init__(self, rh, conf)
        self._selectedRegistrants = selectedRegistrants

    def _getTabContent( self, params ):
        wc = WRegistrantModifPrintBadges( self._conf, selectedRegistrants = self._selectedRegistrants )
        return wc.getHTML()
