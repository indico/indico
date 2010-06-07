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

import math
from datetime import timedelta
import MaKaC.webinterface.pages.registrationForm as registrationForm
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.common.filters as filters
from MaKaC.webinterface import wcomponents
from xml.sax.saxutils import quoteattr
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase
from MaKaC.common import Config
from MaKaC.webinterface.common.countries import CountryHolder
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.webinterface.common.registrantNotificator import EmailNotificator
from MaKaC import registration
from conferences import WConfModifBadgePDFOptions
from MaKaC.i18n import _
from xml.sax.saxutils import escape
import string

# ----------------- MANAGEMENT AREA ---------------------------
class WPConfModifRegistrantListBase( registrationForm.WPConfModifRegFormBase ):

    def _setActiveTab( self ):
        self._tabRegistrants.setActive()

class WPConfModifRegistrantList( WPConfModifRegistrantListBase ):
    def __init__( self, rh, conference, filterUsed = False ):
        WPConfModifRegistrantListBase.__init__(self, rh, conference)
        self._filterUsed = filterUsed


    def _getTabContent( self, params ):
        filterCrit=params.get("filterCrit",None)
        sortingCrit=params.get("sortingCrit",None)
        display = params.get("display",None)
        order = params.get("order",None)
        sessionFilterName=params.get("sessionFilterName", "session")
        websession = self._rh._getSession()

        wc = WConfModifRegistrants(self._conf,filterCrit,sortingCrit,display, websession, order, sessionFilterName, self._filterUsed)
        return wc.getHTML()

class WConfModifRegistrants( wcomponents.WTemplated ):

    def __init__( self, conference,filterCrit, sortingCrit, display, websession, order="down", sessionFilterName="session", filterUsed = False ):

        self._conf = conference
        self._filterCrit=filterCrit
        self._sortingCrit=sortingCrit
        self._order = order
        self._sessionFilterName = sessionFilterName
        self._display = display
        self._filterUsed = filterUsed
        self._setDispOpts()
        self._setStatusesOpts()

    def _setStatusesOpts(self):
        """
        """
        self._statuses = {}
        for st in self._conf.getRegistrationForm().getStatusesList():
            self._statuses[st.getId()] = st.getStatusValues()

    def _setDispOpts(self):
        """
            Dictionary with the available options you can choose for the display.
            Within the dictionary we store the "ids" of the options.
        """
        self._dispopts = {"PersonalData":[ "Id", "LastName", "FirstName", "Email", "Position", "Institution","Phone","City","Country","Address","isPayed","idpayment","amountToPay"]}
        self._dispopts["statuses"]=[]
        for st in self._conf.getRegistrationForm().getStatusesList():
            self._dispopts["statuses"].append("s-%s"%st.getId())
        #if self._conf.getRegistrationForm().getAccommodationForm().isEnabled():
        self._dispopts["Accommodation"]=["Accommodation", "ArrivalDate","DepartureDate"]
        #if self._conf.getRegistrationForm().getSocialEventForm().isEnabled():
        self._dispopts["SocialEvents"] = ["SocialEvents"]
        #if self._conf.getRegistrationForm().getSessionsForm().isEnabled():
        self._dispopts["Sessions"] = ["Sessions"]
        #if self._conf.getRegistrationForm().getReasonParticipationForm().isEnabled():
        self._dispopts["ReasonParticipation"]=["ReasonParticipation"]
        self._dispopts["more"]=["RegistrationDate"]
        for sect in self._conf.getRegistrationForm().getGeneralSectionFormsList():
            self._dispopts[sect.getId()]=[]

            for fld in sect.getSortedFields():
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
            columns ={"PersonalData":"Personal Data","Id":"Id", "Email": "Email", "Position":"Position", "Institution":"Institution","Phone":"Phone","City":"City",\
                      "Country":"Country", "Address":"Address", "ArrivalDate": "Arrival Date", "DepartureDate": "Departure Date", \
                      "RegistrationDate": "Registration date (%s)"%self._conf.getTimezone()}

            tit=self._conf.getRegistrationForm().getSessionsForm().getTitle()
            if not self._conf.getRegistrationForm().getSessionsForm().isEnabled():
                tit='%s <span style="color:red;font-size: 75%%">(disabled)</span>'%tit
            columns["Sessions"]=tit
            tit=self._conf.getRegistrationForm().getAccommodationForm().getTitle()
            if not self._conf.getRegistrationForm().getAccommodationForm().isEnabled():
                tit='%s <span style="color:red;font-size: 75%%">(disabled)</span>'%tit
            columns["Accommodation"]=tit
            tit=self._conf.getRegistrationForm().getSocialEventForm().getTitle()
            if not self._conf.getRegistrationForm().getSocialEventForm().isEnabled():
                tit='%s <span style="color:red;font-size: 75%%">(disabled)</span>'%tit
            columns["SocialEvents"]=tit
            tit=self._conf.getRegistrationForm().getReasonParticipationForm().getTitle()
            if not self._conf.getRegistrationForm().getReasonParticipationForm().isEnabled():
                tit='%s <span style="color:red;font-size: 75%%">(disabled)</span>'%tit
            columns["ReasonParticipation"]=tit
            columns["more"]="General info"
            columns["statuses"]="Statuses"
            columns["isPayed"]="Paid"
            columns["idpayment"]="Payment ID"
            columns["amountToPay"]="Amount"
            columns["LastName"]="Last name"
            columns["FirstName"]="First name"

            for st in self._conf.getRegistrationForm().getStatusesList():
                columns["s-%s"%st.getId()]=st.getCaption()
            for sect in self._conf.getRegistrationForm().getGeneralSectionFormsList():
                tit=sect.getTitle()
                if not sect.isEnabled():
                    tit='%s <span style="color:red;font-size: 75%%">(disabled)</span>'%tit
                columns[sect.getId()]=tit
                ############
                # jmf-start
                #for fld in sect.getFields():
                #    columns["%s-%s"%(sect.getId(),fld.getId())]=fld.getCaption()
                for fld in sect.getSortedFields():
                    columns["%s-%s"%(sect.getId(),fld.getId())]=fld.getCaption()
                # jmf-end
                ############
            self._columns=columns
        return self._columns

    def _getDisplay(self):
        """
            These are the 'display' options selected by the user. In case no options were selected we add some of them by default.
        """
        display=self._display[:]

        if display == []:
            display=["Email", "Institution","Phone","City","Country"]
            if self._conf.hasEnabledSection("epay"):
                display.extend(["isPayed","idpayment","amountToPay"])
        return display

    def _getURL( self ):
        #builds the URL to the contribution list page
        #   preserving the current filter and sorting status in the websesion
        url = urlHandlers.UHConfModifRegistrantList.getURL(self._conf)

        return url

    def _getStatusesHTML(self):
        self._statusesObjects = {}
        for st in self._conf.getRegistrationForm().getStatusesList():
            self._statusesObjects[st.getId()] = st
        return WRegistrantsFilterStatuses(self._statuses, self._filterCrit, self._statusesObjects).getHTML()

    def _getDispHTML(self):
        """
        Filtering criteria: table with all the options for the columns we need to display.
        """
        res=["""<table width="100%%" cellpadding="0" cellspacing="0" valign="top">"""]
        columns=self._getColumnTitlesDict()
        checked = " checked"
        display=self._getDisplay()
        counter=0
        # sorting dispopts by
        auxdict={}
        for key in self._dispopts.keys():
            if not auxdict.has_key(len(self._dispopts[key])):
                auxdict[len(self._dispopts[key])]=[]
            auxdict[len(self._dispopts[key])].append(key)
        auxlens=auxdict.keys()
        auxlens.sort()
        auxlens.reverse()
        dispoptssortedkeys=[]
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
                checked =""
                if keyfld in display:
                    checked=" checked"
                res.append("""<tr><td align="left" valign="top"><input type="checkbox" name="disp" value="%s"%s></td><td width="100%%" align="left" valign="top">%s</td></tr>"""%(keyfld,checked,columns[keyfld].replace('<span style="color:red;font-size: 75%">(disabled)</span>','')))
                res.append("""</table>""")
            res.append("""</td>""")
            if counter==2:
                counter=0
                res.append("""</tr>""")

            else:
                counter+=1
        if counter in [1,2]:
            res.append("""<td colspan="2" style="border-bottom:1px solid lightgrey; width:100%%">&nbsp;</td>""")
        res.append("""</table>""")
        return "".join(res)


    def _getRegColumnHTML(self, sortingField):
        """
        Titles for the columns of the list.
        """
        resgroups={}
        columns=self._getColumnTitlesDict()
        currentSorting=""
        if sortingField is not None:
            currentSorting=sortingField.getSpecialId()
        currentSortingHTML = ""
        display=self._getDisplay()
        resgroups["PersonalData"]=[]
        if "Id" in display:
            url=self._getURL()
            url.addParam("sortBy","Id")
            idImg=""
            if currentSorting == "Id":
                currentSortingHTML = """<input type="hidden" name="sortBy" value="Id">"""
                if self._order == "down":
                    idImg = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                    url.addParam("order","up")
                elif self._order == "up":
                    idImg = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                    url.addParam("order","down")
            idSortingURL=quoteattr("%s#results"%str(url))
            resgroups["PersonalData"]=[ _("""<td nowrap class="titleCellFormat" style="border-left:5px solid #FFFFFF;border-bottom: 1px solid #888;">%s<a href=%s> _("Id")</a></td>""")%(idImg, idSortingURL)]

        url=self._getURL()
        url.addParam("sortBy","Name")
        nameImg=""
        if currentSorting == "Name":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="Name">"""
            if self._order == "down":
                nameImg = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                nameImg = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        nameSortingURL=quoteattr("%s#results"%str(url))

        resgroups["PersonalData"].append( _("""<td nowrap class="titleCellFormat" style="border-left:5px solid #FFFFFF;border-bottom: 1px solid #888;">%s<a href=%s> _("Name")</a></td>""")%(nameImg, nameSortingURL))
        if "Id" in display:
            pdil=["Id", "Name"]
        else:
            pdil=["Name"]
        self._groupsorder={"PersonalData":pdil}#list used to display the info of the registrants in the same order
        for key in display:
            if key == "Id" or not columns.has_key(key):
                continue
            url=self._getURL()
            url.addParam("sortBy",key)
            img=""
            if currentSorting == key:
                currentSortingHTML = """<input type="hidden" name="sortBy" value="%s">"""%key
                if self._order == "down":
                    img = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                    url.addParam("order","up")
                elif self._order == "up":
                    img = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                    url.addParam("order","down")
            sortingURL=quoteattr("%s#results"%str(url))
            kg=self._getKeyDispOpts(key)
            if not resgroups.has_key(kg):
                self._groupsorder[kg]=[]
                resgroups[kg]=[]
            self._groupsorder[kg].append(key)
            resgroups[kg].append("""<td class="titleCellFormat" style="border-left:5px solid #FFFFFF;border-bottom: 1px solid #888;">%s<a href=%s>%s</a></td>"""%(img, sortingURL, self.htmlText(columns[key].replace('<span style="color:red;font-size: 75%">(disabled)</span>',''))))
        fields=["""
                <tr>
                    <td align="right" nowrap></td>"""]
        # First we want to display the personal data...
        groupkey="PersonalData"
        fields += resgroups[groupkey]
        del resgroups[groupkey]
        #...and them all the other info:
        for groupkey in resgroups.keys():
            fields += resgroups[groupkey]
        fields.append("""
                        </tr>
                        """)
        return "<tr><td colspan=4 style='padding: 5px 0px 10px;' nowrap>Select: <a style='color: #0B63A5;' alt='Select all' onclick='javascript:selectAll()'> All</a>, <a style='color: #0B63A5;' alt='Unselect all' onclick='javascript:deselectAll()'>None</a></td></tr>%s"%("\r\n".join(fields))


    def _getRegistrantsHTML( self, reg ):
        url = urlHandlers.UHRegistrantModification.getURL(reg)
        fullName = reg.getFullName()
        regdict={}
        regdict["FirstName"]=reg.getFirstName()
        regdict["LastName"]=reg.getSurName()
        regdict["Institution"]=reg.getInstitution()
        regdict["Position"] = reg.getPosition()
        regdict["Phone"]=reg.getPhone()
        regdict["City"]= reg.getCity()
        regdict["Country"]=CountryHolder().getCountryById(reg.getCountry())
        regdict["Address"] = reg.getAddress()
        regdict["Email"]=reg.getEmail()
        regdict["isPayed"]=reg.isPayedText()
        regdict["idpayment"]=reg.getIdPay()
        regdict["amountToPay"]="%.2f %s"%(reg.getTotal(), reg.getConference().getRegistrationForm().getCurrency())
        regdict["Accommodation"]=""
        regdict["DepartureDate"]=""
        regdict["ArrivalDate"]=""
        if reg.getAccommodation() is not None:
            if reg.getAccommodation().getAccommodationType() is not None:
                regdict["Accommodation"]= reg.getAccommodation().getAccommodationType().getCaption()
            if reg.getAccommodation().getDepartureDate() is not None:
                regdict["DepartureDate"]=reg.getAccommodation().getDepartureDate().strftime("%d-%B-%Y")
            if reg.getAccommodation().getArrivalDate() is not None:
                regdict["ArrivalDate"]=reg.getAccommodation().getArrivalDate().strftime("%d-%B-%Y")

        events = reg.getSocialEvents()
        items =[]
        for item in events:
            items.append("%s (%s)"%(item.getCaption(), item.getNoPlaces()))
        regdict["SocialEvents"] = "<br>".join(items)

        regdict["ReasonParticipation"]=reg.getReasonParticipation() or ""

        regdict["RegistrationDate"]=  _("""--  _("date unknown")--""")
        if reg.getRegistrationDate() is not None:
            regdict["RegistrationDate"]=reg.getAdjustedRegistrationDate().strftime("%d-%B-%Y %H:%M")

        sessions = reg.getSessionList()
        sesslist =[]
        for sess in sessions:
            sesslist.append(sess.getTitle())
        regdict["Sessions"] ="<br>".join(sesslist)

        for strf in self._conf.getRegistrationForm().getStatusesList():
            cap=  _("""<span style="white-space:nowrap">--  _("not set") --</span>""")
            st=reg.getStatusById(strf.getId())
            if st.getStatusValue() is not None:
                cap=st.getStatusValue().getCaption()
            regdict["s-%s"%st.getId()]=cap

        for group in reg.getMiscellaneousGroupList():
                regdict[group.getId()]=group.getTitle()
                for fld in group.getResponseItemList():
                    regdict["%s-%s"%(group.getId(),fld.getId())]=fld.getValue()

        res =[]
        res.append("""<td valign="top" align="right" width="3%%"><input onchange="javascript:isSelected('registrant%s')" type="checkbox" name="registrant" value="%s"></td>
                    """%(reg.getId(),self.htmlText(reg.getId())))
        if "Id" in self._groupsorder["PersonalData"]:
            res.append("""<td valign="top" nowrap class="CRLabstractLeftDataCell">%s</td>
                          <td valign="top" nowrap class="CRLabstractDataCell"><a href=%s>%s</a></td>
                       """%(reg.getId(), quoteattr(str(url)), self.htmlText(fullName)))
        else:
            res.append("""<td valign="top" nowrap class="CRLabstractDataCell"><a href=%s>%s</a></td>
                    """%(quoteattr(str(url)), self.htmlText(fullName)))
        # Fisrtly the "PersonalData"
        for key in self._groupsorder["PersonalData"]:
            if key == "Name" or key == "Id":
                continue
            v = "&nbsp;"
            if regdict.has_key(key) and regdict[key].strip() != "":
                v = regdict[key]
            res.append( """<td valign="top"  class="CRLabstractDataCell">%s</td>"""%v)
        for groupkey in self._groupsorder.keys():
            if groupkey == "PersonalData":
                continue
            for key in  self._groupsorder[groupkey]:
                v = "&nbsp;"
                if regdict.has_key(key) and str(regdict[key]).strip() != "":
                    v = regdict[key]
                res.append( """<td valign="top"  class="CRLabstractDataCell">%s</td>"""%v)
        html = """
            <tr id="registrant%s" style="background-color: transparent;" onmouseout="javascript:onMouseOut('registrant%s')" onmouseover="javascript:onMouseOver('registrant%s')">
                %s
            </tr>
                """%(reg.getId(),reg.getId(),reg.getId(), "".join(res))
        return html

    def _getDisplayOptionsHTML(self):
        html=[]
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
                html.append("""<input type="hidden" name="disp" value="%s">"""%(d))
        html.append("""<input type="hidden" name="sortBy" value="%s">"""%(self._sortingCrit.getField().getId()))
        return "".join(html)

    def _getOpenMenuURL(self):
        url = urlHandlers.UHConfModifRegistrantsOpenMenu.getURL(self._conf)
        url.addParam("currentURL", self._getURL())
        return url

    def _getCloseMenuURL(self):
        url = urlHandlers.UHConfModifRegistrantsCloseMenu.getURL(self._conf)
        url.addParam("currentURL", self._getURL())
        return url

    def _getFilterMenu(self):

        regForm = self._conf.getRegistrationForm()

        options = [
            ('accomm', regForm.getAccommodationForm()),
            ('event', regForm.getSocialEventForm()),
            (self._sessionFilterName, regForm.getSessionsForm())
            ]

        extraInfo = ""
        if self._conf.getRegistrationForm().getStatusesList():
            extraInfo = _("""<table align="center" cellspacing="0" width="100%%">
                                <tr>
                                    <td align="left" class="titleCellFormat" style="border-bottom: 1px solid #888; padding-right:10px">  _("Statuses") <img src=%s border="0" alt="Select all" onclick="javascript:selectStatuses()"><img src=%s border="0" alt="Unselect all" onclick="javascript:unselectStatuses()"></td>
                                </tr>
                                <tr>
                                    <td valign="top">%s</td>
                                </tr>
                            </table>
                        """)%(quoteattr(Config.getInstance().getSystemIconURL("checkAll")),quoteattr(Config.getInstance().getSystemIconURL("uncheckAll")),self._getStatusesHTML())

        p = WFilterCriteriaRegistrants(options, self._filterCrit, extraInfo)

        return p.getHTML()

    def _getDisplayMenu(self):
        menu =  _("""<div class="CRLDiv" style="display: none;" id="displayMenu"><table width="95%%" align="center" border="0">
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

    def getVars( self ):

        vars = wcomponents.WTemplated.getVars( self )

        sortingField = self._sortingCrit.getField()

        vars["filterPostURL"]=quoteattr("%s#results"%str(urlHandlers.UHConfModifRegistrantList.getURL(self._conf)))
        l=[]
        cl = self._conf.getRegistrantsList(True)
        f = filters.SimpleFilter(self._filterCrit,self._sortingCrit)
        regl=[]
        eventItems = self._conf.getRegistrationForm().getSocialEventForm().getSocialEventList()
        vars["eve"]=""
        vars["columns"]=self._getRegColumnHTML(sortingField)
        for reg in f.apply(cl):
            l.append(self._getRegistrantsHTML(reg))
            regl.append(reg.getId())

        if self._order =="up":
            l.reverse()
            regl.reverse()
        vars["registrants"] = "".join(l)
        vars["filteredNumberRegistrants"]=str(len(l))
        vars["totalNumberRegistrants"]=str(len(cl))
        vars["filterUsed"] = self._filterUsed


        vars["actionPostURL"]=quoteattr(str(urlHandlers.UHConfModifRegistrantListAction.getURL(self._conf)))

        if l == []:
            vars ["reglist"]=""
        else:
            vars ["reglist"]=",".join(regl)
        vars["emailIconURL"]="""<input type="image" name="email" src=%s border="0">"""%quoteattr(str(Config.getInstance().getSystemIconURL("envelope")))
        vars["printIconURL"]="""<input type="image" name="pdf" src=%s border="0">"""%quoteattr(str(Config.getInstance().getSystemIconURL("pdf")))
        vars["infoIconURL"]="""<input type="image" name="info" src=%s border="0">"""%quoteattr(str(Config.getInstance().getSystemIconURL("info")))
        vars["excelIconURL"]="""<input type="image" name="excel" src=%s border="0">"""%quoteattr(str(Config.getInstance().getSystemIconURL("excel")))
        vars["pdfUrl"] = quoteattr(str(Config.getInstance().getSystemIconURL("pdf")))
        vars["excelUrl"] = quoteattr(str(Config.getInstance().getSystemIconURL("excel")))
        vars ["disp"]= self._getDispHTML()
        tit=self._conf.getRegistrationForm().getAccommodationForm().getTitle()
        if not self._conf.getRegistrationForm().getAccommodationForm().isEnabled():
            tit='%s <span style="color:red;font-size: 75%%">(disabled)</span>'%tit
        vars ["accomtitle"]=tit
        tit=self._conf.getRegistrationForm().getSessionsForm().getTitle()
        if not self._conf.getRegistrationForm().getSessionsForm().isEnabled():
            tit='%s <span style="color:red;font-size: 75%%">(disabled)</span>'%tit
        vars["sesstitle"]=tit
        tit=self._conf.getRegistrationForm().getSocialEventForm().getTitle()
        if not self._conf.getRegistrationForm().getSocialEventForm().isEnabled():
            tit='%s <span style="color:red;font-size: 75%%">(disabled)</span>'%tit
        vars["eventtitle"]=tit
        vars["displayOptions"]=self._getDisplayOptionsHTML()
        vars["sortingOptions"]="""<input type="hidden" name="sortBy" value="%s">
                                  <input type="hidden" name="order" value="%s">"""%(self._sortingCrit.getField().getId(), self._order)
        vars["closeMenuURL"] = self._getCloseMenuURL()
        vars["closeMenuImg"] = quoteattr(Config.getInstance().getSystemIconURL("openMenu"))
        vars["openMenuURL"] = self._getOpenMenuURL()
        vars["openMenuImg"] = quoteattr(Config.getInstance().getSystemIconURL("closeMenu"))

        vars["checkAcco"] = """<img src=%s border="0" alt="Select all" onclick="javascript:selectAcco()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckAcco"] = """<img src=%s border="0" alt="Unselect all" onclick="javascript:unselectAcco()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))
        vars["checkEvent"] = """<img src=%s border="0" alt="Select all" onclick="javascript:selectEvent()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckEvent"] = """<img src=%s border="0" alt="Unselect all" onclick="javascript:unselectEvent()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))
        vars["checkSession"] = """<img src=%s border="0" alt="Select all" onclick="javascript:selectSession()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckSession"] = """<img src=%s border="0" alt="Unselect all" onclick="javascript:unselectSession()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))
        vars["checkDisplay"] = """<img src=%s border="0" alt="Select all" onclick="javascript:selectDisplay()">"""%quoteattr(Config.getInstance().getSystemIconURL("checkAll"))
        vars["uncheckDisplay"] = """<img src=%s border="0" alt="Unselect all" onclick="javascript:unselectDisplay()">"""%quoteattr(Config.getInstance().getSystemIconURL("uncheckAll"))
        vars["displayMenu"] = self._getDisplayMenu()%vars
        vars["filterMenu"] = self._getFilterMenu()

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

        # TODO: remove when we have a better template system
        return page.getHTML().replace('%','%%')

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
        vars["from"]=  _("""<center>  _("No preview avaible") </center>""")
        vars["subject"]=  _("""<center>  _("No preview avaible") </center>""")
        vars["body"]=  _("""<center> _("No preview avaible") </center>""")
        vars["to"]=  _("""<center> _("No preview avaible") </center>""")
        vars["cc"]=  _("""<center> _("No preview avaible") </center>""")
        if registrant != None:
            notif=EmailNotificator().apply(registrant,{"subject":subject, "body":body, "from":fromAddr, "to":[registrant.getEmail()], "cc": [cc]})
            vars["from"]=notif.getFromAddr()
            vars["to"]=notif.getToList()
            vars["subject"]=notif.getSubject()
            vars["body"] = notif.getBody()
            vars["cc"] = notif.getCCList()
        vars["params"]=[]
        for regId in regsIds:
            vars["params"].append("""<input type="hidden" name="regsIds" value="%s">"""%(regId))
        vars["params"].append("""<input type="hidden" name="from" value=%s>"""%(quoteattr(fromAddr)))
        vars["params"].append("""<input type="hidden" name="subject" value=%s>"""%(quoteattr(subject)))
        vars["params"].append("""<input type="hidden" name="body" value=%s>"""%(quoteattr(body)))
        vars["params"].append("""<input type="hidden" name="cc" value=%s>"""%(quoteattr(cc)))
        vars["params"]="".join(vars["params"])
        vars["postURL"]=urlHandlers.UHRegistrantsSendEmail.getURL(self._conf)
        return vars


class WPPreviewEmail( WPConfModifRegistrantListBase ):

    def __init__(self, rh, conf, params):
        WPConfModifRegistrantListBase.__init__(self, rh, conf)
        self._params = params

    def _getTabContent(self,params):
        wc = WRegPreviewMail(self._conf, self._params)
        return wc.getHTML()


class WEmailToRegistrants(wcomponents.WTemplated):
    def __init__(self,conf,user,reglist):
        self._conf = conf
        try:
            self._fromemail = user.getEmail()
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
        vars["from"] = self._fromemail
        vars["cc"] = ""
        vars["toEmails"]= ", ".join(toEmails)
        if vars["toEmails"] == "":
            vars["toEmails"] = "No registrants have been selected"
        vars["toIds"]= "".join(toIds)
        vars["postURL"]=urlHandlers.UHRegistrantsSendEmail.getURL(self._conf)
        vars["subject"]=""
        vars["body"]=""
        vars["vars"]=self._getAvailableTagsHTML()
        return vars

class WPRegistrantModifRemoveConfirmation(WPConfModifRegistrantListBase):

    def __init__(self,rh, conf, registrantList):
        WPConfModifRegistrantListBase.__init__(self,rh,conf)
        self._regList = registrantList

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        regs=[]
        for reg in self._regList:
            regs.append("<li><i>%s</i></li>"%self._conf.getRegistrantById(reg).getFullName())
        msg=  _("""  _("Are you sure you want to delete the following registrants")?:<br><ul>%s</ul>
        <font color="red"> _("(note you will permanently lose all the information about the registrants)")</font><br>""")%("".join(regs))
        url=urlHandlers.UHConfModifRegistrantPerformRemove.getURL(self._conf)
        return wc.getHTML(msg,url,{"registrants":self._regList})

class WPEMail ( WPConfModifRegistrantListBase ):
    def __init__(self, rh, conf, reglist):
        WPConfModifRegistrantListBase.__init__(self, rh, conf)
        self._regList = reglist

    def _getTabContent(self,params):
        wc = WEmailToRegistrants(self._conf, self._getAW().getUser(), self._regList)
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
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHRegistrantModification.getURL( self._target ) )
        self._setActiveTab()
        self._setupTabCtrl()

    def _setActiveTab( self ):
        pass

    def _setupTabCtrl(self):
        pass

    def _setActiveSideMenuItem(self):
        self._regFormMenuItem.setActive(True)

    def _getPageContent( self, params ):
        self._createTabCtrl()
        banner = wcomponents.WRegFormBannerModif(self._target).getHTML()
        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner+html

    def _getTabContent( self, params ):
        return  _("nothing")

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
            html.append( _("""
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
                        v= _("""--  _("no value selected") --""")
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
            html.append( _("""
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
            return  _("""<form action=%s method="POST">
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
            if self._registrant.getConference().hasEnabledSection("epay") and self._registrant.getConference().getModPay().isActivated() and self._registrant.doPay():
                urlEpayment = """<br/><br/><i>Direct access link for epayment:</i><br/><small>%s</small>"""%escape(str(urlHandlers.UHConfRegistrationFormCreationDone.getURL(self._registrant)))
            return _(""" <form action=%s method="POST">
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
            return  _(""" <form action="" method="POST">
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
                session1 =  _("""<font color=\"red\">--  _("not selected") --</font>""")
                session2 =  _("""--  _("not selected") --""")
                if len(sessions) > 0:
                    session1 = sessions[0].getTitle()
                    if sessions[0].isCancelled():
                        session1 =  _("""%s <font color=\"red\">( _("cancelled") )""")%session1
                if len(sessions) > 1:
                    session2 = sessions[1].getTitle()
                    if sessions[1].isCancelled():
                        session2 =  _("""%s <font color=\"red\"> ( _("cancelled") )""")%session2
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
                sessionList =  _("""<font color=\"red\">--_("not selected")--</font>""")
                if len(sessions) > 0:
                    sessionList=["<ul>"]
                    for ses in sessions:
                        sesText = "<li>%s</li>"%ses.getTitle()
                        if ses.isCancelled():
                            sesText =  _("""<li>%s <font color=\"red\"> ( _("cancelled") )</font></li>""")%ses.getTitle()
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
            accoType =   _("""<font color=\"red\">--_("not selected")--</font>""")
            cancelled = ""
            if accommodation is not None and accommodation.getAccommodationType() is not None:
                accoType = accommodation.getAccommodationType().getCaption()
                if accommodation.getAccommodationType().isCancelled():
                    cancelled =  _("""<font color=\"red\"> _("(disabled)")</font>""")
            arrivalDate =  _("""<font color=\"red\">--_("not selected")--</font>""")
            if accommodation is not None and accommodation.getArrivalDate() is not None:
                arrivalDate = accommodation.getArrivalDate().strftime("%d-%B-%Y")
            departureDate =  _("""<font color=\"red\">--_("not selected")--</font>""")
            if accommodation is not None and accommodation.getDepartureDate() is not None:
                departureDate = accommodation.getDepartureDate().strftime("%d-%B-%Y")
            text =  _("""
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
            return  _("""
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
                    cancelled =  _("""<font color=\"red\"> ( _("cancelled") )</font>""")
                    if se.getCancelledReason().strip():
                        cancelled =  _("""<font color=\"red\">( _("cancelled"): %s)</font>""")%se.getCancelledReason().strip()
                r.append( _("""
                            <tr>
                              <td align="left">%s <b>[%s _("place(s) needed")]</b> %s</td>
                            </tr>
                         """)%(se.getCaption(), se.getNoPlaces(), cancelled))
            if r == []:
                text = _("""--_("no social events selected")--""")
            else:
                text = """
                        <table>
                          %s
                        </table>
                        """%("".join(r))
            text = _("""
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
            return _("""
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
            v= _("""--_("no value selected")--""")
            if miscItem is not None:
                v=miscItem.getValue()
            html.append("""
                    <tr>
                       <td align="left" style="max-width: 25%%" valign="top"><b>%s:</b></td>
                       <td align="left" valign="top">%s</td>
                    </tr>
                    <tr><td>&nbsp;</td></tr>
                    """%(f.getCaption(), v) )
        if miscGroup is not None:
            for miscItem in miscGroup.getResponseItemList():
                    f=gsf.getFieldById(miscItem.getId())
                    if f is None:
                        html.append( _("""
                                    <tr>
                                       <td align="left" style="max-width: 25%%"><b>%s:</b></td>
                                       <td align="left">%s <font color="red">(cancelled)</font></td>
                                    </tr>
                                    <tr><td>&nbsp;</td></tr>
                                    """) %(miscItem.getCaption(), miscItem.getValue()) )
        if len(html)==1:
            html.append( _("""
                        <tr><td><font color="black"><i> --_("No fields")--</i></font></td></tr>
                        """))
        html.append("</table>")
        return "".join(html)

    def _getMiscellaneousInfoHTML(self, gsf):
        regForm = self._conf.getRegistrationForm()
        html=[]
        url=urlHandlers.UHConfModifRegistrantMiscInfoModify.getURL(self._registrant)
        url.addParam("miscInfoId", gsf.getId())
        html.append( _("""
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
        return "".join(sects)

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
        html=[ _("""
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
        vars["registrationDate"] = _("""--_("date unknown")--""")
        if self._registrant.getRegistrationDate() is not None:
            vars["registrationDate"] = "%s (%s)"%(self._registrant.getAdjustedRegistrationDate().strftime("%d-%B-%Y %H:%M"), self._conf.getTimezone())
        vars["dataModificationURL"] = quoteattr(str(urlHandlers.UHRegistrantDataModification.getURL(self._registrant)))
        vars["sections"] = self._getFormSections()
        vars["statuses"]=self._getStatusesHTML()

        vars["transaction"]=self._getTransactionHTML()
        return vars

class WPRegistrantDataModification( WPRegistrantModifMain ):

    def _getTabContent( self, params ):
        wc = WRegistrantDataModification(self._registrant)
        return wc.getHTML()

class WRegistrantDataModification( wcomponents.WTemplated ):

    def __init__( self, registrant ):
        self._registrant = registrant
        self._conf = self._registrant.getConference()

    def _getItemHTML(self, item, value):
        inputHTML = ""
        if item.getInput() == "list":
            if item.getId() == "title":
                for title in TitlesRegistry().getList():
                    selected = ""
                    if value == title:
                        selected = "selected"
                    inputHTML += """<option value="%s" %s>%s</option>"""%(title, selected, title)
                inputHTML = """<select name="%s">%s</select>"""%(item.getId(), inputHTML)
            elif item.getId() == "country":
                for ck in CountryHolder().getCountrySortedKeys():
                    selected = ""
                    if value == ck:
                        selected = "selected"
                    inputHTML += """<option value="%s" %s>%s</option>"""%(ck, selected, CountryHolder().getCountryById(ck))
                inputHTML = """<select name="%s">%s</select>"""%(item.getId(), inputHTML)
        else:
            input = item.getInput()
            if item.getId() == "email":
                input = "text"
            inputHTML = """<input type="%s" name="%s" size="40" value="%s">"""%(input, item.getId(), value)
        mandatory="&nbsp; &nbsp;"
        if item.isMandatory():
            mandatory = """<font color="red">* </font>"""
        html = """
                <tr>
                    <td nowrap class="titleCellTD">%s<span class="titleCellFormat">%s</span></td>
                    <td width="100%%" align="left" bgcolor="white" class="blacktext">%s</td>
                </tr>
                """%(mandatory, item.getName(), inputHTML)
        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        personalData = self._conf.getRegistrationForm().getPersonalData()
        data = []
        sortedKeys = personalData.getSortedKeys()
        formValues = personalData.getValuesFromRegistrant(self._registrant)
        for key in sortedKeys:
            item = personalData.getDataItem(key)
            data.append(self._getItemHTML(item, formValues.get(item.getId(), "")))
        vars["data"] = "".join(data)
        vars["postURL"] = quoteattr(str(urlHandlers.UHRegistrantPerformDataModification.getURL(self._registrant)))
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
        html = [ _("""<select name="%s">
                        <option value="nosession" %s>--_("None selected")--</option>""")%(selectName, selected)]
        for ses in self._sessionForm.getSessionList(True):
            selected = ""
            if ses == sessionValue:
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
        tmp=  _("""<select name="isPayed"><option value="yes" %s> _("yes")</option><option value="no" %s> _("no")</option></select>""")%(checkedYes, checkedNo)
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

    def _getSessionsHTML(self):
        html=[]
        for session in self._registrant.getRegistrationForm().getSessionsForm().getSessionList():
            selected=""
            if session in self._registrant.getSessionList():
                selected=" checked"
            html.append("""<input type="checkbox" name="sessions" value="%s"%s>%s"""%(session.getId(), selected, session.getTitle()) )
        return "<br>".join(html)

    def getVars(self):
        vars = WConfModifRegistrantSessionsBase.getVars( self )
        vars ["sessions"] = self._getSessionsHTML()
        return vars

class WConfModifRegistrantAccommodationModify(wcomponents.WTemplated):

    def __init__(self, registrant):
        self._registrant = registrant
        self._conf = self._registrant.getConference()
        self._accommodation = self._conf.getRegistrationForm().getAccommodationForm()

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
        html = ["""
                <select name="%s">
                <option value="nodate" %s>-- select a date --</option>
                """%(name, selected)]
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
        for type in self._accommodation.getAccommodationTypesList():
            if not type.isCancelled():
                selected = ""
                if currentAccoType == type:
                    selected = "checked=\"checked\""
                html.append("""<tr>
                                    <td align="left" style="padding-left:10px"><input type="radio" name="accommodationType" value="%s" %s>%s</td>
                                </tr>
                            """%(type.getId(), selected, type.getCaption() ) )
            else:
                html.append( _("""<tr>
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
        if acco is not None:
            currentArrivalDate = acco.getArrivalDate()
            currentDepartureDate = acco.getDepartureDate()
            currentAccoType = acco.getAccommodationType()
        vars["title"] = self._accommodation.getTitle()
        vars["arrivalDate"] = self._getDatesHTML("arrivalDate", currentArrivalDate)
        vars["departureDate"] = self._getDatesHTML("departureDate", currentDepartureDate)
        vars["accommodationTypes"] = self._getAccommodationTypesHTML(currentAccoType)
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

    def _getSocialEventsHTML(self, socialEvents=[]):
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

                html.append("""<tr>
                                    <td align="left" nowrap style="padding-left:10px"><input type="checkbox" name="socialEvents" value="%s" %s>%s&nbsp;&nbsp;
                                    </td>
                                    <td width="100%%" align="left">
                                    <select name="places-%s">
                                       %s
                                    </select>
                                    </td>
                                </tr>
                            """%(se.getId(), checked, se.getCaption(), se.getId(), "".join(optList) ) )
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
        vars["socialEvents"] = self._getSocialEventsHTML(regSocialEvents)
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
        # jmf-start
        ############
            v=""
            miscItem = None
            if self._miscGroup.getResponseItemById(f.getId()) is not None:
                miscItem=self._miscGroup.getResponseItemById(f.getId())
                v=miscItem.getValue()
                price=v=miscItem.getPrice()
            html.append("""
                        <tr>
                          <td>
                             %s
                          </td>
                        </tr>
                        """%(f.getInput().getModifHTML(miscItem, self._registrant)) )
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
        html.insert(1, _("""
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

class WConfRegistrantsList( wcomponents.WTemplated ):

    def __init__( self, conference, filterCrit, sortingCrit, order, sessionFilterName ):
        self._conf = conference
        self._regForm = self._conf.getRegistrationForm()
        self._filterCrit=filterCrit
        self._sortingCrit=sortingCrit
        self._order=order
        self._sessionFilterName=sessionFilterName

    def _getURL( self ):
        #builds the URL to the contribution list page
        #   preserving the current filter and sorting status
        url = urlHandlers.UHConfRegistrantsList.getURL(self._conf)
#        if self._filterCrit.getField("accomm"):
#            url.addParam("accomm",self._filterCrit.getField("accomm").getValues())
#            if self._filterCrit.getField("accomm").getShowNoValue():
#                url.addParam("accommShowNoValue","1")
#
        if self._filterCrit.getField(self._sessionFilterName):
            url.addParam("session",self._filterCrit.getField(self._sessionFilterName).getValues())
            if self._filterCrit.getField(self._sessionFilterName).getShowNoValue():
                url.addParam("sessionShowNoValue","1")

        if self._sessionFilterName == "sessionfirstpriority":
            url.addParam("firstChoice", "1")
#
#        if self._filterCrit.getField("event"):
#            url.addParam("event",self._filterCrit.getField("event").getValues())
#            if self._filterCrit.getField("event").getShowNoValue():
#                url.addParam("eventShowNoValue","1")
#
        if self._sortingCrit.getField():
            url.addParam("sortBy",self._sortingCrit.getField().getId())
            url.addParam("order","down")

#        url.addParam("disp",self._getDisplay())

        return url

    def _getRegistrantsHTML( self, reg ):
        fullName = reg.getFullName()
        institution = ""
        if self._regForm.getPersonalData().getDataItem("institution").isEnabled():
            institution = """<td valign="top" class="abstractDataCell">%s</td>"""%(self.htmlText(reg.getInstitution()) or "&nbsp;")
        position = ""
        if self._regForm.getPersonalData().getDataItem("position").isEnabled():
            position = """<td valign="top" class="abstractDataCell">%s</td>"""%(self.htmlText(reg.getPosition()) or "&nbsp;")
        city = ""
        if self._regForm.getPersonalData().getDataItem("city").isEnabled():
            city = """<td valign="top" class="abstractDataCell">%s</td>"""%(self.htmlText(reg.getCity()) or "&nbsp;")
        country = ""
        if self._regForm.getPersonalData().getDataItem("country").isEnabled():
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
                <td valign="top" nowrap class="abstractLeftDataCell">%s</td>
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
        sessform =self._regForm.getSessionsForm()
        sesstypes = sessform.getSessionList()
        checked=""
        if self._filterCrit.getField(self._sessionFilterName).getShowNoValue():
            checked=" checked"
        res=[ _("""<input type="checkbox" name="sessionShowNoValue" value="--none--"%s> --_("not specified")--""")%checked]
        for sess in sesstypes:
            checked=""
            if sess.getId() in self._filterCrit.getField(self._sessionFilterName).getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="session" value=%s%s>%s"""%(quoteattr(str(sess.getId())),checked,self.htmlText(sess.getTitle())))
        if sessform.getType() == "2priorities":
            checked=""
            if self._sessionFilterName == "sessionfirstpriority":
                checked=" checked"
            res.append( _("""<b>------</b><br><input type="checkbox" name="firstChoice" value="firstChoice"%s><i> _("Only by first choice") </i>""")%checked)
        return "<br>".join(res)

    def _getFilterOptionsHTML(self, currentSortingHTML):
        filterPostURL=quoteattr("%s#results"%str(urlHandlers.UHConfRegistrantsList.getURL(self._conf)))
        return _("""<tr>
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
                """)%(filterPostURL, currentSortingHTML, self._getSessHTML())

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["regForm"]= self._regForm
        l=[]
        lr=self._conf.getRegistrantsList(True)
        f = filters.SimpleFilter(self._filterCrit,self._sortingCrit)
        for rp in f.apply(lr):
            l.append(self._getRegistrantsHTML(rp))
        if self._order =="up":
            l.reverse()
        vars["registrants"] = "".join(l)
        vars["numRegistrants"]=str(len(l))

        # Head Table Titles
        currentSorting=""
        if self._sortingCrit.getField() is not None:
            currentSorting=self._sortingCrit.getField().getSpecialId()

        currentSortingHTML = ""
        # --- Name
        url=self._getURL()
        url.addParam("sortBy","Name")
        nameImg=""
        vars["imgNameTitle"]=""
        if currentSorting == "Name":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="Name">"""
            if self._order == "down":
                vars["imgNameTitle"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["imgNameTitle"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["urlNameTitle"]=quoteattr("%s#results"%str(url))

        # --- Institution
        url=self._getURL()
        url.addParam("sortBy","Institution")
        nameImg=""
        vars["imgInstitutionTitle"]=""
        if currentSorting == "Institution":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="Institution">"""
            if self._order == "down":
                vars["imgInstitutionTitle"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["imgInstitutionTitle"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["urlInstitutionTitle"]=quoteattr("%s#results"%str(url))

        # --- Position
        url=self._getURL()
        url.addParam("sortBy","Position")
        nameImg=""
        vars["imgPositionTitle"]=""
        if currentSorting == "Position":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="Position">"""
            if self._order == "down":
                vars["imgPositionTitle"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["imgPositionTitle"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["urlPositionTitle"]=quoteattr("%s#results"%str(url))

        # --- City
        url=self._getURL()
        url.addParam("sortBy","City")
        nameImg=""
        vars["imgCityTitle"]=""
        if currentSorting == "City":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="City">"""
            if self._order == "down":
                vars["imgCityTitle"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["imgCityTitle"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["urlCityTitle"]=quoteattr("%s#results"%str(url))


        # --- Country
        url=self._getURL()
        url.addParam("sortBy","Country")
        nameImg=""
        vars["imgCountryTitle"]=""
        if currentSorting == "Country":
            currentSortingHTML = """<input type="hidden" name="sortBy" value="Country">"""
            if self._order == "down":
                vars["imgCountryTitle"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["imgCountryTitle"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["urlCountryTitle"]=quoteattr("%s#results"%str(url))

        # --- Sessions

        vars["sessionsTitle"] = ""

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
            vars["sessionsTitle"] = """<td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%s<a href=%s>%s</a></td>"""%(imgSessionTitle, urlSessionTitle, self._conf.getRegistrationForm().getSessionsForm().getTitle())

        # --- Filter Options
        vars["filterOptions"]=""
        if self._regForm.getSessionsForm().isEnabled():
            vars["filterOptions"]=self._getFilterOptionsHTML(currentSortingHTML)
        return vars
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
