# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

import os
import tempfile
from cStringIO import StringIO
from datetime import datetime,timedelta

from dateutil.relativedelta import relativedelta
from flask import session, request
from persistent.list import PersistentList
from pytz import timezone
from werkzeug.exceptions import Forbidden

from indico.core.config import Config
from indico.util import json
from indico.web.flask.util import send_file
from MaKaC.PDFinterface.conference import RegistrantsListToBadgesPDF, LectureToPosterPDF
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.errors import MaKaCError, FormValuesError
from MaKaC.i18n import _
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages import admins, conferences
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.webinterface.rh.categoryDisplay import UtilsConference
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase


class RHConferenceModifBase(RHConferenceBase, RHModificationBaseProtected):

    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)

    def _checkProtection(self):
        RHModificationBaseProtected._checkProtection(self)

    def _displayCustomPage(self, wf):
        return None

    def _displayDefaultPage(self):
        return None

    def _process(self):
        wf = self.getWebFactory()
        if wf is not None:
            res = self._displayCustomPage(wf)
            if res is not None:
                return res
        return self._displayDefaultPage()


class RHConferenceModification(RHConferenceModifBase):
    _uh = urlHandlers.UHConferenceModification

    def _process( self ):
        pars={}
        wf=self.getWebFactory()
        if wf is not None:
            pars["type"]=wf.getId()
        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display(**pars)
        else:
            p = conferences.WPConferenceModification( self, self._target )

            if wf is not None:
                p = wf.getConfModif(self, self._conf)
            return p.display(**pars)


class RHConfScreenDatesEdit(RHConferenceModifBase):
    _uh = urlHandlers.UHConfScreenDatesEdit

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams(self,params)
        self._action=""
        if params.has_key("CANCEL"):
            self._action="CANCEL"
        elif params.has_key("OK"):
            self._action="EDIT"
            self._sDate,self._eDate=None,None
            tz = self._target.getTimezone()
            if params.get("start_date","conference")=="own":
                try:
                    self._sDate=timezone(tz).localize(datetime(int(params["sYear"]),
                                    int(params["sMonth"]),
                                    int(params["sDay"]),
                                    int(params["sHour"]),
                                    int(params["sMin"]))).astimezone(timezone('UTC'))
                except ValueError:
                    raise MaKaCError( _("Please enter integers in all the start date fields"), _("Schedule"))
            if params.get("end_date","conference")=="own":
                try:
                    self._eDate=timezone(tz).localize(datetime(int(params["eYear"]),
                                    int(params["eMonth"]),
                                    int(params["eDay"]),
                                    int(params["eHour"]),
                                    int(params["eMin"]))).astimezone(timezone('UTC'))
                except ValueError:
                    raise MaKaCError( _("Please enter integers in all the end date fields"), _("Schedule"))

    def _process( self ):
        url=urlHandlers.UHConferenceModification.getURL(self._target)
        if self._action=="CANCEL":
            self._redirect(url)
            return
        elif self._action=="EDIT":
            self._target.setScreenStartDate(self._sDate)
            self._target.setScreenEndDate(self._eDate)
            self._redirect(url)
            return
        p = conferences.WPScreenDatesEdit(self, self._target)
        return p.display()


class RHConfDataModif(RHConferenceModifBase):
    _uh = urlHandlers.UHConfDataModif

    def _displayCustomPage(self, wf):
        return None

    def _displayDefaultPage(self):
        p = conferences.WPConfDataModif(self, self._target)
        pars = {}
        wf = self.getWebFactory()
        if wf is not None:
            pars["type"] = wf.getId()
        return p.display(**pars)


class RHConfPerformDataModif(RHConferenceModifBase):
    _uh = urlHandlers.UHConfPerformDataModif

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        if params.get("title", "").strip() =="" and not ("cancel" in params):
            raise FormValuesError("Please, provide a name for the event")
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if not self._cancel:
            params = dict(self._getRequestParams(), keywords=request.form.getlist('keywords'))
            UtilsConference.setValues(self._conf, params)
        self._redirect( urlHandlers.UHConferenceModification.getURL( self._conf) )


#######################################################################################

class RHConfClone( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfClone
    _allowClosed = True

    def _process( self ):
        p = conferences.WPConfClone( self, self._conf )
        wf=self.getWebFactory()
        if wf is not None:
            p = wf.getConfClone(self, self._conf)
        return p.display()


class RHConfPerformCloning(RHConferenceModifBase, object):
    """
    New version of clone functionality -
    fully replace the old one, based on three different actions,
    adds mechanism of selective cloning of materials and access
    privileges attached to an event
    """
    _uh = urlHandlers.UHConfPerformCloning
    _cloneType = "none"
    _allowClosed = True

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._date = datetime.today()
        self._cloneType = params.get("cloneType", None)
        if self._cloneType is None:
            raise FormValuesError( _("""Please choose a cloning interval for this event"""))
        elif self._cloneType == "once" :
            self._date = datetime( int(params["stdyo"]), \
                                int(params["stdmo"]), \
                                int(params["stddo"]), \
                                int(self._conf.getAdjustedStartDate().hour), \
                                int(self._conf.getAdjustedStartDate().minute) )
        elif self._cloneType == "intervals" :
            self._date = datetime( int(params["indyi"]), \
                                int(params["indmi"]), \
                                int(params["inddi"]), \
                                int(self._conf.getAdjustedStartDate().hour), \
                                int(self._conf.getAdjustedStartDate().minute) )
        elif self._cloneType == "days" :
            self._date = datetime( int(params["indyd"]), \
                                int(params["indmd"]), \
                                int(params["inddd"]), \
                                int(self._conf.getAdjustedStartDate().hour), \
                                int(self._conf.getAdjustedStartDate().minute) )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )

    def _process( self ):
        params = self._getRequestParams()
        paramNames = params.keys()
        #we notify the event in case any plugin wants to add their options
        if self._cancel:
            self._redirect( urlHandlers.UHConfClone.getURL( self._conf ) )
        elif self._confirm:
            if self._cloneType == "once" :
                newConf = self._conf.clone(self._date)
                self._redirect( urlHandlers.UHConferenceModification.getURL( newConf ) )
            elif self._cloneType == "intervals" :
                self._withIntervals()
            elif self._cloneType == "days" :
                self._days()
            else :
                self._redirect( urlHandlers.UHConfClone.getURL( self._conf ) )
        else:
            if self._cloneType == "once" :
                nbClones = 1
            elif self._cloneType == "intervals" :
                nbClones = self._withIntervals(0)
            elif self._cloneType == "days" :
                nbClones = self._days(0)
            return conferences.WPConfCloneConfirm( self, self._conf, nbClones ).display()

    def _withIntervals(self, confirmed=1):
        nbClones = 0
        params = self._getRequestParams()
        if params["freq"] == "day":
            inter = timedelta(int(params["period"]))
        elif params["freq"] == "week":
            inter = timedelta( 7*int(params["period"]))

        if params["intEndDateChoice"] == "until":
            date=self._date
            endDate = datetime(int(params["stdyi"]),int(params["stdmi"]),int(params["stddi"]), self._conf.getEndDate().hour,self._conf.getEndDate().minute)
            while date <= endDate:
                if confirmed:
                    self._conf.clone(date)
                nbClones += 1
                if params["freq"] == "day" or params["freq"] == "week":
                    date = date + inter
                elif params["freq"] == "month":
                    month = int(date.month) + int(params["period"])
                    year = int(date.year)
                    while month > 12:
                        month = month - 12
                        year = year + 1
                    date = datetime(year,month,int(date.day), int(date.hour), int(date.minute))
                elif params["freq"] == "year":
                    date = datetime(int(date.year)+int(params["period"]),int(date.month),int(date.day), int(date.hour), int(date.minute))

        elif params["intEndDateChoice"] == "ntimes":
            date = self._date
            i=0
            stop = int(params["numi"])
            while i < stop:
                i = i + 1
                if confirmed:
                    self._conf.clone(date)
                nbClones += 1
                if params["freq"] == "day" or params["freq"] == "week":
                    date = date + inter
                elif params["freq"] == "month":
                    month = int(date.month) + int(params["period"])
                    year = int(date.year)
                    while month > 12:
                        month = month - 12
                        year = year + 1
                    date = datetime(year,month,int(date.day), int(date.hour), int(date.minute))
                elif params["freq"] == "year":
                    date = datetime(int(date.year)+int(params["period"]),int(date.month),int(date.day), int(date.hour), int(date.minute))
        if confirmed:
            self._redirect(self._conf.as_event.category.url)
            return "done"
        else:
            return nbClones

    def _getFirstDay(self, date, day):
        """
        return the first day 'day' for the month of 'date'
        """
        td = datetime(int(date.year), int(date.month), 1, int(date.hour), int(date.minute))

        oneDay = timedelta(1)
        while 1:
            if td.weekday() == day:
                return td
            td = td + oneDay

    def _getOpenDay(self, date, day):
        """
        return the first open day for the month of 'date'
        """
        if day!="last": # last open day of the month
            td = datetime(int(date.year), int(date.month), int(date.day), int(date.hour), int(date.minute))
            if td.weekday() > 4:
                td = td + timedelta(7 - td.weekday())
            td += timedelta(int(day)-1)
        else:
            td = self._getLastDay(date, -1)
            if td.weekday() > 4:
                td = td - timedelta(td.weekday() - 4)
        return td

    def _getLastDay(self, date, day):
        """
        return the last day 'day' for the month of 'date'
        """
        td = datetime(int(date.year), int(date.month), 28, int(date.hour), int(date.minute))
        month=td.month
        while td.month == month:
            td += timedelta(1)
        td -= timedelta(1)
        if day==-1:
            return td
        else:
            while 1:
                if td.weekday() == day:
                    return td
                td = td - timedelta(1)

    def _days(self, confirmed=1):
        nbClones = 0
        params = self._getRequestParams()
        #search the first day of the month

        if params["day"] == "NOVAL":
            #self._endRequest()
            self.redirect( urlHandlers.UHConfClone.getURL( self._target ) )

        if params["daysEndDateChoice"] == "until":
            date = self._date

            endDate = datetime(int(params["stdyd"]),int(params["stdmd"]),int(params["stddd"]),self._conf.getEndDate().hour,self._conf.getEndDate().minute)

            if params["day"] == "OpenDay":
                rd = self._getOpenDay(date, params["order"])
            else:
                if params["order"] == "last":
                    rd = self._getLastDay(date, int(params["day"]))
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)
                else:
                    rd = self._getFirstDay(date, int(params["day"])) + timedelta((int(params["order"])-1)*7)
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)
            while date <= endDate:
                if params["day"] == "OpenDay":
                    od=self._getOpenDay(date,params["order"])
                    if od <= endDate:
                        if confirmed:
                            self._conf.clone(od)
                        nbClones += 1
                else:
                    if params["order"] == "last":
                        if self._getLastDay(date,int(params["day"])) <= endDate:
                            if confirmed:
                                self._conf.clone(self._getLastDay(date, int(params["day"])))
                            nbClones += 1
                    else:
                        new_date = (self._getFirstDay(date, int(params["day"])) +
                                    timedelta((int(params["order"]) - 1) * 7))
                        if new_date <= endDate:
                            if confirmed:
                                self._conf.clone(new_date)
                            nbClones += 1
                month = int(date.month) + int(params["monthPeriod"])
                year = int(date.year)
                while month > 12:
                    month = month - 12
                    year = year + 1
                date = datetime(year,month,1, int(date.hour), int(date.minute))

        elif params["daysEndDateChoice"] == "ntimes":

            date = self._date
            if params["day"] == "OpenDay":
                rd = self._getOpenDay(date,params["order"])
            else:
                if params["order"] == "last":
                    rd = self._getLastDay(date, int(params["day"]))
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)
                else:
                    rd = self._getFirstDay(date, int(params["day"])) + timedelta((int(params["order"])-1)*7)
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)

            i=0
            stop = int(params["numd"])
            while i < stop:
                i = i + 1
                if params["day"] == "OpenDay":
                    if confirmed:
                        self._conf.clone(self._getOpenDay(date, params["order"]))
                    nbClones += 1
                else:
                    if params["order"] == "last":
                        if confirmed:
                            self._conf.clone(self._getLastDay(date, int(params["day"])))
                        nbClones += 1
                    else:
                        if confirmed:
                            new_date = (self._getFirstDay(date, int(params["day"])) +
                                        timedelta((int(params["order"]) - 1) * 7))
                            self._conf.clone(new_date)
                        nbClones += 1
                month = int(date.month) + int(params["monthPeriod"])
                year = int(date.year)
                while month > 12:
                    month = month - 12
                    year = year + 1
                date = datetime(year,month,int(date.day), int(date.hour), int(date.minute))
        if confirmed:
            self._redirect(self._conf.as_event.category.url)
        else:
            return nbClones


# ============================================================================
# === Badges related =========================================================
# ============================================================================


class RHConfBadgeBase(RHConferenceModifBase):
    ROLE = 'registration'


"""
Badge Design and Printing classes
"""
class RHConfBadgePrinting(RHConfBadgeBase):
    """ This class corresponds to the screen where templates are
        listed and can be created, edited, deleted and tried.
        It always displays the list of templates; but we can
        arrive to this page in different scenarios:
        -A template has just been created (templateId = new template id, new = True). The template
        will be stored and the temporary backgrounds stored in the session object archived.
        -A template has been edited (templateId = existing template id, new = False or not set).
        The template will be updated and the temporary backgrounds stored in it, archived.
        -A template had been deleted (deleteTemplateId = id of the template to delete)
        -We were creating / editing a template but we pressed the "Cancel" button
        (templateId = id of the template that was being created / edited, Cancel = True).
        Temporary backgrounds (in the session object or in the template object) will be deleted.
    """

    def _checkParams(self, params):
        RHConfBadgeBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        self.__templateData = params.get("templateData",None)
        self.__deleteTemplateId = params.get("deleteTemplateId",None)
        self.__copyTemplateId = params.get("copyTemplateId",None)
        self.__new = params.get("new","False") == "True"
        self.__cancel = params.get("cancel","False") == "True"

    def _process(self):
        if self._target.isClosed():
            return conferences.WPConferenceModificationClosed(self, self._target).display()
        else:
            if self.__templateId and self.__templateData and not self.__deleteTemplateId:

                if self.__new:
                    self._target.getBadgeTemplateManager().storeTemplate(self.__templateId, self.__templateData)
                    key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    filePaths = session.get(key)
                    if filePaths:
                        cfg = Config.getInstance()
                        tempPath = cfg.getUploadedFilesSharedTempDir()
                        for filePath in filePaths:
                            self._target.getBadgeTemplateManager().getTemplateById(self.__templateId).addTempBackgroundFilePath(filePath)
                            self._tempFilesToDelete.append(os.path.join(tempPath, filePath))
                        self._target.getBadgeTemplateManager().getTemplateById(self.__templateId).archiveTempBackgrounds(self._conf)
                else:
                    self._target.getBadgeTemplateManager().storeTemplate(self.__templateId, self.__templateData)

            elif self.__deleteTemplateId:
                self._target.getBadgeTemplateManager().deleteTemplate(self.__deleteTemplateId)

            elif self.__copyTemplateId:
                self._target.getBadgeTemplateManager().copyTemplate(self.__copyTemplateId)
            elif self.__cancel:
                if self._target.getBadgeTemplateManager().hasTemplate(self.__templateId):
                    self._target.getBadgeTemplateManager().getTemplateById(self.__templateId).deleteTempBackgrounds()
                else:
                    key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    session.pop(key, None)

            if self._target.getId() == "default":
                p = admins.WPBadgeTemplates(self)
                url = urlHandlers.UHBadgeTemplates.getURL()
            else:
                p = conferences.WPConfModifBadgePrinting(self, self._target)
                url = urlHandlers.UHConfModifBadgePrinting.getURL(self._target)
            if request.method == 'POST':
                self._redirect(url)
            else:
                return p.display()


class RHConfBadgeDesign(RHConfBadgeBase):
    """ This class corresponds to the screen where templates are
        designed. We can arrive to this screen from different scenarios:
         -We are creating a new template (templateId = new template id, new = True)
         -We are editing an existing template (templateId = existing template id, new = False or not set)
    """

    def _checkParams(self, params):
        RHConfBadgeBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        new = params.get("new",'False')
        if new == 'False':
            self.__new = False
        else:
            self.__new = True
        self.__baseTemplate = params.get("baseTemplate",'blank')


    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
        else:
            p = conferences.WPConfModifBadgeDesign(self, self._target, self.__templateId, self.__new, self.__baseTemplate)
        return p.display()

class RHConfBadgePrintingPDF(RHConfBadgeBase):
    """ This class is used to print the PDF from a badge template.
        There are 2 scenarios:
         -We are printing badges for all registrants (registrantList = 'all' or not set).
         -We are printing badges just for some registrants (registrantList = list of id's of registrants)
    """

    def _checkParams(self, params):
        """ Default values (1.5, etc...) are CERN's defaults in cm.
            These default values also appear in ConfModifBadgePDFOptions.tpl
            marginTop: top margin
            marginBottom: bottom margin
            marginLeft: left margin
            marginRight: right margin
            marginColumns: margin between columns
            marginRows: margin between rows
            keepPDFOptions: tells if we should keep the other params for the next time
                            by storing them in the database (in the conference object)
        """
        RHConfBadgeBase._checkParams(self, params)

        self.__templateId = params.get("templateId",None)

        #we retrieve the present PDF options of the conference in order to use
        #its values in case of input error
        self.__PDFOptions = self._target.getBadgeTemplateManager().getPDFOptions()

        self.__keepPDFOptions = params.get("keepPDFOptions", False)
        #in case of input error, this will be set to False

        try:
            self.__marginTop = float(params.get("marginTop",''))
        except ValueError:
            self.__marginTop = self.__PDFOptions.getTopMargin()
            self.__keepPDFOptions = False

        try:
            self.__marginBottom = float(params.get("marginBottom",''))
        except ValueError:
            self.__marginBottom = self.__PDFOptions.getBottomMargin()
            self.__keepPDFOptions = False

        try:
            self.__marginLeft = float(params.get("marginLeft",''))
        except ValueError:
            self.__marginLeft = self.__PDFOptions.getLeftMargin()
            self.__keepPDFOptions = False

        try:
            self.__marginRight = float(params.get("marginRight",''))
        except ValueError:
            self.__marginRight = self.__PDFOptions.getRightMargin()
            self.__keepPDFOptions = False

        try:
            self.__marginColumns = float(params.get("marginColumns",''))
        except ValueError:
            self.__marginColumns = self.__PDFOptions.getMarginColumns()
            self.__keepPDFOptions = False

        try:
            self.__marginRows = float(params.get("marginRows",''))
        except ValueError:
            self.__marginRows = self.__PDFOptions.getMarginRows()
            self.__keepPDFOptions = False

        self.__pagesize = params.get("pagesize",'A4')

        self.__drawDashedRectangles = params.get("drawDashedRectangles", False) is not False
        self.__landscape = params.get('landscape') == '1'

        self.__registrantList = params.get("registrantList","all")
        if self.__registrantList != "all":
            self.__registrantList = self.__registrantList.split(',') if self.__registrantList else []


    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p
        else:
            if not self.__registrantList:
                return _("There are no registrations to print badges for.")
            elif self.__templateId is None:
                return _("There is no badge template selected for this conference.")

            if self.__keepPDFOptions:
                #we store the pdf options into the conference
                self.__PDFOptions.setTopMargin(self.__marginTop)
                self.__PDFOptions.setBottomMargin(self.__marginBottom)
                self.__PDFOptions.setLeftMargin(self.__marginLeft)
                self.__PDFOptions.setRightMargin(self.__marginRight)
                self.__PDFOptions.setMarginColumns(self.__marginColumns)
                self.__PDFOptions.setMarginRows(self.__marginRows)
                self.__PDFOptions.setPagesize(self.__pagesize)
                self.__PDFOptions.setDrawDashedRectangles(self.__drawDashedRectangles)
                self.__PDFOptions.setLandscape(self.__landscape)


            pdf = RegistrantsListToBadgesPDF(self._conf,
                                             self._conf.getBadgeTemplateManager().getTemplateById(self.__templateId),
                                             self.__marginTop,
                                             self.__marginBottom,
                                             self.__marginLeft,
                                             self.__marginRight,
                                             self.__marginColumns,
                                             self.__marginRows,
                                             self.__pagesize,
                                             self.__drawDashedRectangles,
                                             self.__registrantList,
                                             self.__landscape)
            return send_file('Badges.pdf', StringIO(pdf.getPDFBin()), 'PDF', inline=False)


class RHConfBadgeSaveTempBackground(RHConfBadgeBase):
    """ This class is used to save a background as a temporary file,
        before it is archived. Temporary backgrounds are archived
        after pressing the "save" button.
        The temporary background filepath can be stored in the session
        object (if we are creating a new template and it has not been stored yet)
        or in the corresponding template if we are editing a template.
    """

    def _checkProtection(self):
        if self._conf.id == 'default':
            if not session.user or not session.user.is_admin:
                raise Forbidden
        else:
            RHConfBadgeBase._checkProtection(self)

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesSharedTempDir()
        tempFileName = tempfile.mkstemp( suffix="IndicoBadgeBG.tmp", dir = tempPath )[1]
        return tempFileName

    def _saveFileToTemp(self, fs):
        fileName = self._getNewTempFile()
        fs.save(fileName)
        return os.path.split(fileName)[-1]

    def _checkParams(self, params):
        RHConfBadgeBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        try:
            self._tempFilePath = self._saveFileToTemp(params["file"])
        except AttributeError:
            self._tempFilePath = None

    def _process(self):
        if self._target.isClosed():
            return json.dumps({'status': 'error'}, textarea=True)
        else:
            if self._tempFilePath is not None:
                if self._conf.getBadgeTemplateManager().hasTemplate(self.__templateId):
                    backgroundId = self._conf.getBadgeTemplateManager().getTemplateById(self.__templateId).addTempBackgroundFilePath(self._tempFilePath)
                else:
                    key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    value = session.get(key)
                    if value is None:
                        tempFilePathList = PersistentList()
                        tempFilePathList.append(self._tempFilePath)
                        session[key] = tempFilePathList
                        backgroundId = 0
                    else:
                        value.append(self._tempFilePath)
                        backgroundId = len(value) - 1
                        session.modified = True

                return json.dumps({
                    'status': 'OK',
                    'id': backgroundId,
                    'url': str(urlHandlers.UHConfModifBadgeGetBackground.getURL(self._conf, self.__templateId, backgroundId))
                }, textarea=True)

class RHConfBadgeGetBackground(RHConfBadgeBase):
    """ Class used to obtain a background in order to display it
        on the Badge Design screen.
        The background can be obtained from the archived files
        or from the temporary files.
    """

    def _checkProtection(self):
        if self._conf.id == 'default':
            if not session.user or not session.user.is_admin:
                raise Forbidden
        else:
            RHConfBadgeBase._checkProtection(self)

    def _checkParams(self, params):
        RHConfBadgeBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        self.__backgroundId = int(params.get("backgroundId",None))
        self.__width = int(params.get("width","-1"))
        self.__height = int(params.get("height","-1"))

    def __imageBin(self, image):
        mimetype = image.getFileType() or 'application/octet-stream'
        return send_file(image.getFileName(), image.getFilePath(), mimetype)

    def __fileBin(self, filePath):
        return send_file('tempBackground', filePath, 'application/octet-stream')

    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p
        else:
            cfg = Config.getInstance()
            tempPath = cfg.getUploadedFilesSharedTempDir()
            if self._conf.getBadgeTemplateManager().hasTemplate(self.__templateId):
                isArchived, image = self._conf.getBadgeTemplateManager().getTemplateById(self.__templateId).getBackground(self.__backgroundId)
                if image is not None:
                    if isArchived:
                        return self.__imageBin(image)
                    else:
                        image = os.path.join(tempPath,image)
                        return self.__fileBin(image)

            else:
                key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                filePath = os.path.join(tempPath, session[key][int(self.__backgroundId)])
                return self.__fileBin(filePath)


# ============================================================================
# === Posters related ========================================================
# ============================================================================

##------------------------------------------------------------------------------------------------------------
"""
Poster Design and Printing classes
"""
class RHConfPosterPrinting(RHConferenceModifBase):
    """ This class corresponds to the screen where templates are
        listed and can be created, edited, deleted and tried.
        It always displays the list of templates; but we can
        arrive to this page in different scenarios:
        -A template has just been created (templateId = new template id, new = True). The template
        will be stored and the temporary backgrounds stored in the session object archived.
        -A template has been edited (templateId = existing template id, new = False or not set).
        The template will be updated and the temporary backgrounds stored in it, archived.
        -A template had been deleted (deleteTemplateId = id of the template to delete)
        -We were creating / editing a template but we pressed the "Cancel" button
        (templateId = id of the template that was being created / edited, Cancel = True).
        Temporary backgrounds (in the session object or in the template object) will be deleted.
    """

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        self.__templateData = params.get("templateData",None)
        self.__deleteTemplateId = params.get("deleteTemplateId",None)
        self.__copyTemplateId = params.get("copyTemplateId",None)
        self.__bgPosition = params.get("bgPosition",None)
        self.__new = params.get("new","False") == "True"
        self.__cancel = params.get("cancel","False") == "True"


    def _process(self):
        if self._target.isClosed():
            return conferences.WPConferenceModificationClosed(self, self._target).display()
        else:
            if self.__templateId and self.__templateData and not self.__deleteTemplateId:
                if self.__new:
                # template is new
                    self._target.getPosterTemplateManager().storeTemplate(self.__templateId, self.__templateData)
                    key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    filePaths = session.get(key)
                    if filePaths:
                        for filePath in filePaths:
                            self._target.getPosterTemplateManager().getTemplateById(self.__templateId).addTempBackgroundFilePath(filePath[0],filePath[1])
                        self._target.getPosterTemplateManager().getTemplateById(self.__templateId).archiveTempBackgrounds(self._conf)
                else:
                # template already exists
                    self._target.getPosterTemplateManager().storeTemplate(self.__templateId, self.__templateData)
            elif self.__deleteTemplateId:
                self._target.getPosterTemplateManager().deleteTemplate(self.__deleteTemplateId)
            elif self.__copyTemplateId:
                self._target.getPosterTemplateManager().copyTemplate(self.__copyTemplateId)
            elif self.__cancel:
                if self._target.getPosterTemplateManager().hasTemplate(self.__templateId):
                    self._target.getPosterTemplateManager().getTemplateById(self.__templateId).deleteTempBackgrounds()
                else:
                    fkey = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    session.pop(fkey, None)

            if self._target.getId() == "default":
                p = admins.WPPosterTemplates(self)
                url = urlHandlers.UHPosterTemplates.getURL()
            else:
                p = conferences.WPConfModifPosterPrinting(self, self._target)
                url = urlHandlers.UHConfModifPosterPrinting.getURL(self._target)
            if request.method == 'POST':
                self._redirect(url)
            else:
                return p.display()


class RHConfPosterDesign(RHConferenceModifBase):
    """ This class corresponds to the screen where templates are
        designed. We can arrive to this screen from different scenarios:
         -We are creating a new template (templateId = new template id, new = True)
         -We are editing an existing template (templateId = existing template id, new = False or not set)
    """

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        new = params.get("new",'False')
        if new == 'False':
            self.__new = False
        else:
            self.__new = True
        self.__baseTemplate = params.get("baseTemplate",'blank')

    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
        else:
            if (self._target.getId() == "default"):
                p = admins.WPPosterTemplateDesign(self, self._target, self.__templateId, self.__new)
            else:
                if self.__new == True and self.__baseTemplate != 'blank':
                    dconf = HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference()
                    templMan = self._target.getPosterTemplateManager()
                    newId = self.__templateId
                    dconf.getPosterTemplateManager().getTemplateById(self.__baseTemplate).clone(templMan, newId)
                    url = urlHandlers.UHConfModifPosterPrinting().getURL(self._target)
                    self._redirect(url)
                    return
                else:
                    p = conferences.WPConfModifPosterDesign(self, self._target, self.__templateId, self.__new, self.__baseTemplate)
        return p.display()

class RHConfPosterPrintingPDF(RHConferenceModifBase):
    """
        This class is used to print the PDF from a poster template.
    """
    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        if self.__templateId == None:
            raise FormValuesError(_("Poster not selected"))
        if self.__templateId.find('global') != -1:
            self.__templateId = self.__templateId.replace('global','')
            self.__template = (HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference()
                               .getPosterTemplateManager().getTemplateById(self.__templateId))
        else:
            self.__template = self._conf.getPosterTemplateManager().getTemplateById(self.__templateId)
        try:
            self.__marginH = int(params.get("marginH",'2'))
        except ValueError:
            self.__marginH = 2
        try:
            self.__marginV = int(params.get("marginV",'2'))
        except ValueError:
            self.__marginV = 2
        self.__pagesize = params.get("pagesize",'A4')


    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p
        else:
            pdf = LectureToPosterPDF(self._conf,
                                             self.__template,
                                             self.__marginH,
                                             self.__marginV,
                                             self.__pagesize)

            return send_file('Poster.pdf', StringIO(pdf.getPDFBin()), 'PDF')


class RHConfPosterSaveTempBackground(RHConferenceModifBase):
    """ This class is used to save a background as a temporary file,
        before it is archived. Temporary backgrounds are archived
        after pressing the "save" button.
        The temporary background filepath can be stored in the session
        object (if we are creating a new template and it has not been stored yet)
        or in the corresponding template if we are editing a template.
    """

    def _checkProtection(self):
        if self._conf.id == 'default':
            if not session.user or not session.user.is_admin:
                raise Forbidden
        else:
            RHConferenceModifBase._checkProtection(self)

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesSharedTempDir()
        tempFileName = tempfile.mkstemp( suffix="IndicoPosterBG.tmp", dir = tempPath )[1]
        return tempFileName

    def _saveFileToTemp(self, fs):
        fileName = self._getNewTempFile()
        fs.save(fileName)
        return os.path.split(fileName)[-1]

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)

        self._bgPosition = params.get("bgPosition",None)

        try:
            self._tempFilePath = self._saveFileToTemp(params["file"])
        except AttributeError:
            self._tempFilePath = None

    def _process(self):
        if self._target.isClosed():
            return json.dumps({'status': 'error'}, textarea=True)
        else:
            if self._tempFilePath is not None:
                if self._conf.getPosterTemplateManager().hasTemplate(self.__templateId):
                # Save
                    backgroundId = self._conf.getPosterTemplateManager().getTemplateById(self.__templateId).addTempBackgroundFilePath(self._tempFilePath,self._bgPosition)
                else:
                # New
                    key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    value = session.get(key)
                    if value is None:
                    # First background
                        tempFilePathList = PersistentList()
                        tempFilePathList.append((self._tempFilePath,self._bgPosition))
                        session[key] = tempFilePathList
                        backgroundId = 0
                    else:
                    # We have more
                        value.append((self._tempFilePath, self._bgPosition))
                        backgroundId = len(value) - 1
                        session.modified = True

                return json.dumps({
                    'status': 'OK',
                    'id': backgroundId,
                    'url': str(urlHandlers.UHConfModifPosterGetBackground.getURL(self._conf, self.__templateId, backgroundId)),
                    'pos': self._bgPosition
                }, textarea=True)


class RHConfPosterGetBackground(RHConferenceModifBase):
    """ Class used to obtain a background in order to display it
        on the Poster Design screen.
        The background can be obtained from the archived files
        or from the temporary files.
    """

    def _checkProtection(self):
        if self._conf.id == 'default':
            if not session.user or not session.user.is_admin:
                raise Forbidden
        else:
            RHConferenceModifBase._checkProtection(self)

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        self.__backgroundId = int(params.get("backgroundId",None))
        self.__width = int(params.get("width","-1"))
        self.__height = int(params.get("height","-1"))

    def __imageBin(self, image):
        mimetype = image.getFileType() or 'application/octet-stream'
        return send_file(image.getFileName(), image.getFilePath(), mimetype)

    def __fileBin(self, filePath):
        return send_file('tempBackground', filePath, mimetype='application/octet-stream')

    def _process(self):

        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p
        else:
            cfg = Config.getInstance()
            tempPath = cfg.getUploadedFilesSharedTempDir()

            if self._conf.getPosterTemplateManager().hasTemplate(self.__templateId):

                isArchived, image = self._conf.getPosterTemplateManager().getTemplateById(self.__templateId).getBackground(self.__backgroundId)

                if image is not None:
                    if isArchived:
                        return self.__imageBin(image)
                    else:
                        image = os.path.join(tempPath,image)
                        return self.__fileBin(image)

            else:
                key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                filePath = os.path.join(tempPath, session[key][int(self.__backgroundId)][0])
                return self.__fileBin(filePath)
