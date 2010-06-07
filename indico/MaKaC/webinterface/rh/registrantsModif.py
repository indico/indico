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

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.registrants as registrants
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.rh.conferenceModif as conferenceModif
import MaKaC.webinterface.mail as mail
from MaKaC.PDFinterface.conference import RegistrantsListToPDF
from MaKaC.export.excel import RegistrantsListToExcel
from MaKaC.common import filters
import MaKaC.webinterface.common.regFilters as regFilters
from MaKaC.common import Config
from MaKaC.errors import FormValuesError
from MaKaC.common import utils
from MaKaC.registration import SocialEvent, MiscellaneousInfoGroup
from MaKaC.webinterface.common import registrantNotificator
from MaKaC.errors import MaKaCError
from MaKaC import epayment
from MaKaC.i18n import _
import MaKaC.webinterface.pages.registrationForm as registrationForm
from MaKaC.webinterface.rh import registrationFormModif

class RHRegistrantListModifBase( registrationFormModif.RHRegistrationFormModifBase ):
    pass

class RHRegistrantListMenuClose(RHRegistrantListModifBase):

    def _checkParams( self, params ):
        RHRegistrantListModifBase._checkParams( self, params )
        self._currentURL = params.get("currentURL","")

    def _process( self ):
        websession = self._getSession()
        websession.setVar("RegistrantListMenuStatus", "close")
        self._redirect(self._currentURL)


class RHRegistrantListMenuOpen(RHRegistrantListModifBase):

    def _checkParams( self, params ):
        RHRegistrantListModifBase._checkParams( self, params )
        self._currentURL = params.get("currentURL","")

    def _process( self ):
        websession = self._getSession()
        websession.setVar("RegistrantListMenuStatus", "open")
        self._redirect(self._currentURL)

class RHRegistrantListModif( RHRegistrantListModifBase ):
    """
    Registrant List - management area
    Handles filtering and display of different columns
    """

    _uh = urlHandlers.UHConfModifRegistrantList

    def _resetFilters( self, sessionData ):
        """
        Brings the filter data to a consistent state (websession),
        marking everything as "checked"
        """

        regForm = self._conf.getRegistrationForm()
        accommTypes = regForm.getAccommodationForm().getAccommodationTypesList()
        sessionData["accomm"] = map(lambda accom: accom.getId(),
                                    accommTypes)

        lstatuses = []
        for st in regForm.getStatusesList():
            lstatuses.append(st.getCaption() + st.getId() + "-NoValue")
            for stInt in st.getStatusValues():
                lstatuses.append(st.getCaption() + st.getId() + "-" +
                                 st.getStatusValues()[stInt].getCaption())
        sessionData["statuses"] = lstatuses

        sessTypes = regForm.getSessionsForm().getSessionList()
        sessionData["session"] = map(lambda session: session.getId(), sessTypes)

        socialEvents = regForm.getSocialEventForm().getSocialEventList()
        sessionData["event"] = map(lambda event: event.getId(), socialEvents)

        # By default, check '--none--'
        sessionData["accommShowNoValue"] = True
        sessionData["sessionShowNoValue"] = True
        sessionData["eventShowNoValue"] = True

        return sessionData

    def _updateFilters( self, sessionData, params ):
        """
        Updates the filter parameters in the websession with those
        coming from the HTTP request
        """

        sessionData['event'] = []
        sessionData['accomm'] = []
        sessionData['statuses'] = []

        sessionData.update(params)
        sessionData['session'] = utils.normalizeToList(params.get('session',[]))

        # update these elements in the session so that the parameters that are
        # passed are always taken into account (sessionData.update is not
        # enough, since the elements that are ommitted in params would just be
        # ignored

        sessionData['accommShowNoValue'] = params.has_key('accommShowNoValue')
        sessionData['eventShowNoValue'] = params.has_key('eventShowNoValue')
        sessionData['sessionShowNoValue'] = params.has_key('sessionShowNoValue')
        sessionData['firstChoice'] = params.has_key("firstChoice")

        return sessionData

    def _buildFilteringCriteria(self, sessionData):
        """
        Creates the Filtering Criteria object, without changing the existing
        session data (sessionData is cloned, not directly changed)
        """
        sessionCopy = sessionData.copy()

        # filtering criteria needs a proper "filter name"
        del sessionCopy['session']
        sessionCopy[self._sessionFilterName] = sessionData['session']

        # Build the filtering criteria
        filterCrit = regFilters.RegFilterCrit(self._conf, sessionCopy)

        filterCrit.getField("accomm").setShowNoValue(
            sessionCopy.get("accommShowNoValue") )
        filterCrit.getField(self._sessionFilterName).setShowNoValue(
            sessionCopy.get("sessionShowNoValue") )
        filterCrit.getField("event").setShowNoValue(
            sessionCopy.get("eventShowNoValue") )

        return filterCrit

    def _checkAction( self, params, filtersActive, sessionData, operation ):
        """
        Decides what to do with the request parameters, depending
        on the type of operation that is requested
        """

        # user chose to reset the filters
        if operation ==  'resetFilters':
            self._filterUsed = False
            sessionData = self._resetFilters(sessionData)

        # user set the filters
        elif operation ==  'setFilters':
            self._filterUsed = True
            sessionData = self._updateFilters(sessionData, params)

        # user has changed the display options
        elif operation == 'setDisplay':
            self._filterUsed = filtersActive
            sessionData['disp'] = params.get('disp',[])

        # session is empty (first time)
        elif not filtersActive:
            self._filterUsed = False
            sessionData = self._resetFilters(sessionData)
        else:
            self._filterUsed = True

        # preserve the order and sortBy parameters, whatever happens
        sessionData['order'] = params.get('order', 'down')
        sessionData['sortBy'] = params.get('sortBy', 'Name')

        return sessionData

    def _checkParams( self, params ):
        """
        Main parameter checking routine
        """

        RHRegistrantListModifBase._checkParams(self, params)

        operationType = params.get('operationType')

        # session data
        websession = self._getSession()
        sessionData = websession.getVar("registrantsFilterAndSortingConf%s"%self._conf.getId())

        # check if there is information already
        # set in the session variables
        if sessionData:
            # work on a copy
            sessionData = sessionData.copy()
            filtersActive =  sessionData['filtersActive']
        else:
            # set a default, empty dict
            sessionData = {}
            filtersActive = False

        if params.has_key("resetFilters"):
            operation =  'resetFilters'
        elif operationType ==  'filter':
            operation =  'setFilters'
        elif operationType ==  'display':
            operation =  'setDisplay'
        else:
            operation = None

        # the filter name will be different, depending
        # on whether only  the first choice for the session
        # is taken into account

        if params.has_key("firstChoice"):
            self._sessionFilterName="sessionfirstpriority"
        else:
            self._sessionFilterName="session"

        sessionData = self._checkAction(params, filtersActive, sessionData, operation)

        # Maintain the state abotu filter usage
        sessionData['filtersActive'] = self._filterUsed;

        # Save the web session
        websession.setVar("registrantsFilterAndSortingConf%s"%self._conf.getId(), sessionData)

        self._filterCrit = self._buildFilteringCriteria(sessionData)

        self._sortingCrit = regFilters.SortingCriteria( [sessionData.get( "sortBy", "Name" ).strip()] )

        self._order = sessionData.get("order","down")

        self._display = utils.normalizeToList(sessionData.get("disp",[]))


    def _process( self ):
        p = registrants.WPConfModifRegistrantList( self, self._conf, self._filterUsed )
        return p.display(filterCrit = self._filterCrit, sortingCrit=self._sortingCrit, display = self._display, sessionFilterName = self._sessionFilterName, order=self._order )


class RHRegistrantListModifAction( RHRegistrantListModifBase ):
    def _checkParams( self, params ):
        RHRegistrantListModifBase._checkParams(self, params)
        self._selectedRegistrants = self._normaliseListParam(params.get("registrant",[]))
        self._addNew = params.has_key("newRegistrant")
        self._remove = params.has_key("removeRegistrants")
        self._email = params.has_key("email.x")
        self._emailSelected = params.has_key("emailSelected")
        self._pdf = params.has_key("pdf.x")
        self._info = params.has_key("info.x")
        self._excel = params.has_key("excel.x")
        self._reglist = params.get("reglist","").split(",")
        self._display = self._normaliseListParam(params.get("disp",[]))
        self._printBadgesSelected = params.has_key("printBadgesSelected")

    def _process( self ):
        if self._addNew:
            self._redirect(RHRegistrantNewForm._uh.getURL(self._conf))
        elif self._remove:
            if len(self._selectedRegistrants)>0:
                wp = registrants.WPRegistrantModifRemoveConfirmation(self, self._conf, self._selectedRegistrants)
                return wp.display()
            else:
                self._redirect(urlHandlers.UHConfModifRegistrantList.getURL(self._conf))
        elif self._email:
            r = RHRegistrantListEmail(self, self._conf,self._reglist)
            return r.email()
        elif self._emailSelected:
            if len(self._selectedRegistrants)>0:
                r = RHRegistrantListEmail(self, self._conf,self._selectedRegistrants)
                return r.email()
            else:
                self._redirect(urlHandlers.UHConfModifRegistrantList.getURL(self._conf))
        elif self._pdf:
            regs =[]
            for reg in self._selectedRegistrants:
                if self._conf.getRegistrantById(reg) !=None:
                    regs.append(self._conf.getRegistrantById(reg))
            r = RHRegistrantListPDF(self,self._conf,regs, self._display)
            return r.pdf()
        elif self._info:
            regs =[]
            for reg in self._selectedRegistrants:
                if self._conf.getRegistrantById(reg) !=None:
                    regs.append(self._conf.getRegistrantById(reg))
            r = RHRegistrantsInfo(self,self._conf,regs)
            return r.info()
        elif self._excel:
            regs =[]
            for reg in self._selectedRegistrants:
                if self._conf.getRegistrantById(reg) !=None:
                    regs.append(self._conf.getRegistrantById(reg))
            r = RHRegistrantListExcel(self,self._conf,regs, self._display)
            return r.excel()
        elif self._printBadgesSelected:
            if len(self._selectedRegistrants) > 0:
                wp = registrants.WPRegistrantModifPrintBadges(self, self._conf, self._selectedRegistrants)
                return wp.display()
            else:
                self._redirect(urlHandlers.UHConfModifRegistrantList.getURL(self._conf))
        else:
            self._redirect(urlHandlers.UHConfModifRegistrantList.getURL(self._conf))

class RHRegistrantNewForm(RHRegistrantListModifBase):
    _uh = urlHandlers.Derive(RHRegistrantListModif, "newRegistrant")

    def _checkParams(self, params):
        RHRegistrantListModifBase._checkParams(self, params)

    def _process(self):
        p = registrationForm.WPRegistrationFormDisplay(self, self._conf)
        return p.display()

class RHRegistrantListRemove(RHRegistrantListModifBase):

    def _checkParams( self, params ):
        RHRegistrantListModifBase._checkParams(self, params)
        self._selectedRegistrants = self._normaliseListParam(params.get("registrants",[]))
        self._cancel=params.has_key("cancel")

    def _process(self):
        if not self._cancel:
            for reg in self._selectedRegistrants:
                self._conf.removeRegistrant(reg)
        self._redirect(urlHandlers.UHConfModifRegistrantList.getURL(self._conf))

class RHRegistrantsInfo:

    def __init__( self, rh, conf, reglist ):
        self._conf = conf
        self._list = reglist
        self._rh = rh

    def info(self):
        p=registrants.WPRegistrantsInfo(self._rh, self._conf)
        return p.display(reglist=self._list)

class RHRegistrantListPDF:
    def __init__( self, rh,conf,reglist, disp ):
        self._conf = conf
        self._list = reglist
        self._rh = rh
        self._display = disp


    def pdf( self ):
        filename = "RegistrantsList.pdf"
        pdf = RegistrantsListToPDF(self._conf,list=self._list, display=self._display)
        data = pdf.getPDFBin()
        self._rh._req.set_content_length(len(data))
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._rh._req.content_type = """%s"""%(mimetype)
        self._rh._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data

class RHRegistrantListExcel:
    def __init__( self, rh,conf,reglist, disp ):
        self._conf = conf
        self._list = reglist
        self._rh = rh
        self._display = disp

    def excel( self ):
        filename = "RegistrantsList.csv"
        excel = RegistrantsListToExcel(self._conf,list=self._list, display=self._display)
        data = excel.getExcelFile()
        self._rh._req.set_content_length(len(data))
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "CSV" )
        self._rh._req.content_type = """%s"""%(mimetype)
        self._rh._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data

class RHRegistrantListEmail:
    def __init__(self, rh, conf, reglist):
        self._conf = conf
        self._regList = reglist
        self._rh = rh

    def email(self):
        p=registrants.WPEMail(self._rh, self._conf, self._regList)
        return p.display()

class RHRegistrantModifBase( conferenceModif.RHConferenceModifBase ):

    def _checkProtection( self ):
        conferenceModif.RHConferenceModifBase._checkProtection(self)
        if not self._conf.hasEnabledSection("regForm"):
            raise MaKaCError( _("The registrants' management was disabled by the conference managers"))

    def _checkParams( self, params ):
        conferenceModif.RHConferenceModifBase._checkParams(self, params)
        self._registrant = self._conf.getRegistrantById(params.get("registrantId",""))

class RHRegistrantModification( RHRegistrantModifBase ):

    def _process( self ):
        p = registrants.WPRegistrantModification( self, self._registrant )
        return p.display()

class RHRegistrantDataModification( RHRegistrantModifBase ):

    def _process( self ):
        p = registrants.WPRegistrantDataModification( self, self._registrant )
        return p.display()

class RHRegistrantSendEmail( RHRegistrantModifBase ):

    def _checkParams(self, params):
        RHRegistrantModifBase._checkParams( self, params )
        self._regsIds = self._normaliseListParam(params.get("regsIds",[]))
        self._cancel=params.has_key("cancel")
        self._send = params.has_key("OK")
        self._preview = params.has_key("preview")
        if not self._cancel:
            if params.get("from","") == "":
                raise FormValuesError("Please write from address")
            if params.get("subject","") == "":
                raise FormValuesError("Please write any subject for the email")
            if params.get("body","") == "":
                raise FormValuesError("Please write any body for the email")
            self._p={}
            self._p["subject"]=params["subject"]
            self._p["from"]=params["from"]
            self._p["body"]=params["body"]
            self._p["cc"]=[params.get("cc", "")]

    def _process(self):
        if self._send:
            for regId in self._regsIds:
                reg=self._conf.getRegistrantById(regId)
                if  reg!=None:
                    self._p['to']=[reg.getEmail()]
                    self._p['conf'] = self._conf
                    registrantNotificator.EmailNotificator().notify(reg, self._p)
            p = registrants.WPSentEmail(self, self._target)
            return p.display()
        elif self._preview:
            p = registrants.WPPreviewEmail(self, self._target, self._getRequestParams())
            return p.display()
        else:
            self._redirect(urlHandlers.UHConfModifRegistrantList.getURL(self._conf))


class RHRegistrantPerformDataModification( RHRegistrantModifBase ):

    def _checkParams( self, params ):
        RHRegistrantModifBase._checkParams(self, params)
        self._regForm = self._conf.getRegistrationForm()
        pd = self._regForm.getPersonalData()
        keys = pd.getMandatoryItems()
        for key in keys:
            if key not in params.keys() or params.get(key,"").strip() == "":
                raise FormValuesError("The field \"%s\" is mandatory and you must fill it in order to modify the registrant"%(pd.getData()[key].getName()))
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if not self._cancel:
            if self._conf.hasRegistrantByEmail(self._getRequestParams().get("email",""), self._registrant):
                raise FormValuesError("There is already a user with the email \"%s\". Please choose another one"%self._getRequestParams().get("email","--no email--"))
            self._registrant.setPersonalData(self._getRequestParams())
        self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))


class RHRegistrantSessionModify( RHRegistrantModifBase ):

    def _checkParams( self, params ):
        RHRegistrantModifBase._checkParams(self, params)
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if not self._conf.getRegistrationForm().getSessionsForm().isEnabled():
            self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))
        else:
            p = registrants.WPRegistrantSessionModify(self, self._registrant)
            return p.display()

class RHRegistrantTransactionModify( RHRegistrantModifBase ):

    def _checkParams( self, params ):
        RHRegistrantModifBase._checkParams(self, params)
        self._cancel = params.has_key("cancel")

    def _process( self ):

        if not self._conf.getRegistrationForm().isActivated():
            self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))
        else:
            p = registrants.WPRegistrantTransactionModify(self, self._registrant)
            return p.display()

class RHRegistrantTransactionPerformModify( RHRegistrantModifBase ):
    _uh = urlHandlers.UHRegistrantModification

    def _checkParams( self, params ):
        RHRegistrantModifBase._checkParams(self, params)
        self._cancel = params.has_key("cancel")
        self._isPayed = params["isPayed"]
#        if not self._cancel:
#            self._regForm = self._conf.getRegistrationForm()
#            sessionForm = self._regForm.getSessionsForm()
#            if not sessionForm.isEnabled():
#                self._cancel = True
#                return
#            self._sessions = sessionForm.getSessionsFromParams(params)

    def _process( self ):
        if not self._cancel:
            if self._isPayed == "yes":
                self._registrant.setPayed(True)
                d={}
                d["OrderTotal"]=self._registrant.getTotal()
                d["Currency"]=self._registrant.getRegistrationForm().getCurrency()
                tr=epayment.TransactionPayLaterMod(d)
                self._registrant.setTransactionInfo(tr)
            else :self._registrant.setTransactionInfo(None)
            #self._registrant.setSessions(self._sessions)
        self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))


class RHRegistrantSessionPerformModify( RHRegistrantModifBase ):
    _uh = urlHandlers.UHRegistrantModification

    def _checkParams( self, params ):
        RHRegistrantModifBase._checkParams(self, params)
        self._cancel = params.has_key("cancel")
        if not self._cancel:
            self._regForm = self._conf.getRegistrationForm()
            sessionForm = self._regForm.getSessionsForm()
            if not sessionForm.isEnabled():
                self._cancel = True
                return
            self._sessions = sessionForm.getSessionsFromParams(params)

    def _process( self ):
        if not self._cancel:
            self._registrant.setSessions(self._sessions)
        self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))

class RHRegistrantAccommodationModify( RHRegistrantModifBase ):

    def _process( self ):
        if not self._conf.getRegistrationForm().getAccommodationForm().isEnabled():
            self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))
        else:
            p = registrants.WPRegistrantAccommodationModify(self, self._registrant)
            return p.display()

class RHRegistrantAccommodationPerformModify( RHRegistrantModifBase ):
    _uh = urlHandlers.UHRegistrantModification

    def _checkParams( self, params ):
        RHRegistrantModifBase._checkParams(self, params)
        self._cancel = params.has_key("cancel")
        if not self._cancel:
            self._regForm = self._conf.getRegistrationForm()
            if not self._regForm.getAccommodationForm().isEnabled():
                self._cancel = True
                return
            self._arrivalDate = params.get("arrivalDate",None)
            self._departureDate = params.get("departureDate",None)
            if self._arrivalDate is not None and self._departureDate is not None:
                self._arrivalDate = utils.stringToDate(self._arrivalDate)
                self._departureDate = utils.stringToDate(self._departureDate)
                if self._arrivalDate > self._departureDate:
                    raise FormValuesError("Arrival date has to be earlier than departure date")
            self._accoType = self._regForm.getAccommodationForm().getAccommodationTypeById(params.get("accommodationType", ""))
            if self._regForm.getAccommodationForm().getAccommodationTypesList() !=[] and self._accoType is None:
                raise FormValuesError("It is mandatory to choose an accommodation in order to register")

    def _process( self ):
        if not self._cancel:
            self._registrant.getAccommodation().setArrivalDate(self._arrivalDate)
            self._registrant.getAccommodation().setDepartureDate(self._departureDate)
            if self._regForm.getAccommodationForm().getAccommodationTypesList() !=[]:
                self._registrant.getAccommodation().setAccommodationType(self._accoType)
        self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))

class RHRegistrantSocialEventsModify( RHRegistrantModifBase ):

    def _process( self ):
        if not self._conf.getRegistrationForm().getSocialEventForm().isEnabled():
            self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))
        else:
            p = registrants.WPRegistrantSocialEventsModify(self, self._registrant)
            return p.display()

class RHRegistrantSocialEventsPerformModify( RHRegistrantModifBase ):
    _uh = urlHandlers.UHRegistrantModification

    def _checkParams( self, params ):
        RHRegistrantModifBase._checkParams(self, params)
        self._cancel = params.has_key("cancel")
        if not self._cancel:
            self._regForm = self._conf.getRegistrationForm()
            if not self._regForm.getSocialEventForm().isEnabled():
                self._cancel = True
            else:
                socialEventIds = self._normaliseListParam(params.get("socialEvents", []))
                self._socialEvents = []
                self._places = {}
                for id in socialEventIds:
                    self._socialEvents.append(self._regForm.getSocialEventForm().getSocialEventById(id))
                    self._places[id] = params.get("places-%s"%id, "1")

    def _process( self ):
        if not self._cancel:
            for seItem in self._registrant.getSocialEvents()[:]:
                self._registrant.removeSocialEventById(seItem.getId())

            l = []
            for seItem in self._socialEvents:
                newSE = SocialEvent(seItem, int(self._places[seItem.getId()]))
                self._registrant.addSocialEvent(newSE)
        self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))

class RHRegistrantReasonParticipationModify( RHRegistrantModifBase ):

    def _process( self ):
        if not self._conf.getRegistrationForm().getReasonParticipationForm().isEnabled():
            self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))
        else:
            p = registrants.WPRegistrantReasonParticipationModify(self, self._registrant)
            return p.display()

class RHRegistrantReasonParticipationPerformModify( RHRegistrantModifBase ):
    _uh = urlHandlers.UHRegistrantModification

    def _checkParams( self, params ):
        RHRegistrantModifBase._checkParams(self, params)
        self._cancel = params.has_key("cancel")
        if not self._cancel:
            self._regForm = self._conf.getRegistrationForm()
            if not self._regForm.getReasonParticipationForm().isEnabled():
                self._cancel = True
            else:
                self._reason = params.get("reason","")

    def _process( self ):
        if not self._cancel:
            self._registrant.setReasonParticipation(self._reason)
        self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))

class RHRegistrantMiscInfoModify( RHRegistrantModifBase ):

    def _checkParams( self, params ):
        RHRegistrantModifBase._checkParams(self, params)
        self._miscInfoId = params.get("miscInfoId","")
        self._miscInfo=self._registrant.getMiscellaneousGroupById(self._miscInfoId)

    def _process( self ):
        gsf=self._conf.getRegistrationForm().getGeneralSectionFormById(self._miscInfoId)
        if gsf is not None:
            if self._miscInfo is None:
                self._miscInfo=MiscellaneousInfoGroup(self._registrant, gsf)
                self._registrant.addMiscellaneousGroup(self._miscInfo)
            p = registrants.WPRegistrantMiscInfoModify(self, self._miscInfo)
            return p.display()
        self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))

class RHRegistrantMiscInfoPerformModify( RHRegistrantModifBase ):
    _uh = urlHandlers.UHRegistrantModification

    def _checkParams( self, params ):
        RHRegistrantModifBase._checkParams(self, params)
        self._cancel = params.has_key("cancel")
        miscInfoId = params.get("miscInfoId","")
        self._miscInfo=self._registrant.getMiscellaneousGroupById(miscInfoId)

    def _process( self ):
        if not self._cancel:
            params=self._getRequestParams()
            for f in self._miscInfo.getGeneralSection().getSortedFields():
                f.getInput().setResponseValue(self._miscInfo.getResponseItemById(f.getId()),params, self._registrant, self._miscInfo)
        self._registrant.updateTotal()
        self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))

class RHRegistrantStatusesModify( RHRegistrantModifBase ):

    def _process( self ):
        p = registrants.WPRegistrantStatusesModify(self, self._registrant)
        return p.display()

class RHRegistrantStatusesPerformModify( RHRegistrantModifBase ):
    _uh = urlHandlers.UHRegistrantModification

    def _checkParams( self, params ):
        RHRegistrantModifBase._checkParams(self, params)
        self._cancel = params.has_key("cancel")
        self._statuses={}
        for pkey in params.keys():
            if pkey.startswith("statuses-"):
                id=pkey.split("-")[1]
                self._statuses[id]=params.get(pkey)

    def _process( self ):
        if not self._cancel:
            for stkey in self._statuses.keys():
                st=self._conf.getRegistrationForm().getStatusById(stkey)
                if st is not None:
                    v=st.getStatusValueById(self._statuses[stkey])
                    rst=self._registrant.getStatusById(stkey)
                    rst.setStatusValue(v)
        self._redirect(urlHandlers.UHRegistrantModification.getURL(self._registrant))
