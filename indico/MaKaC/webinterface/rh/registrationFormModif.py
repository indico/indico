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
from flask import session
from flask import jsonify
from flask import request

from indico.util.fossilize import fossilize
from indico.util import json

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.registrationForm as registrationForm
from MaKaC.registration import Status, StatusValue, GeneralSectionForm, SocialEventItem, AccommodationType, \
    RegistrationSession, GeneralField
from MaKaC.webinterface.rh.conferenceModif import RHModificationBaseProtected, RHConferenceBase
from MaKaC.errors import FormValuesError, MaKaCError, ConferenceClosedError
from datetime import datetime
from MaKaC.common import utils
from MaKaC.i18n import _

# indico legacy imports
from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.interface.rpc.json import decode


class RHRegistrationFormModifBase(RHConferenceBase, RHModificationBaseProtected):

    def _checkParams( self, params ):
        RHConferenceBase._checkParams( self, params )

    def _checkProtection( self ):
        if not self._target.canManageRegistration(self.getAW().getUser()):
            RHModificationBaseProtected._checkProtection(self)
        if self._target.getConference().isClosed():
            raise ConferenceClosedError(self._target.getConference())


class RHRegistrationModification ( RHRegistrationFormModifBase ):

    def _process( self ):
        p = registrationForm.WPConfModifRegFormPreview( self, self._conf )
        return p.display()

class RHRegistrationFormModif( RHRegistrationFormModifBase ):
    _uh = urlHandlers.UHConfModifRegForm

    def _process( self ):
        p = registrationForm.WPConfModifRegForm( self, self._conf )
        return p.display()

class RHRegistrationFormModifChangeStatus( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._newStatus = params["changeTo"]

    def _process( self ):
        regForm = self._conf.getRegistrationForm()
        if self._newStatus == "True":
            regForm.activate()
        else:
            regForm.deactivate()
        self._redirect(urlHandlers.UHConfModifRegForm.getURL(self._conf))

class RHRegistrationFormModifDataModification( RHRegistrationFormModifBase ):

    def _process( self ):
        p = registrationForm.WPConfModifRegFormDataModification( self, self._conf )
        return p.display()

class RHRegistrationFormModifPerformDataModification( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")

        try:
            self._extraTimeAmount = int(params.get("extraTimeAmount"))
        except ValueError:
            raise FormValuesError(_("The extra allowed time amount is not a valid integer number!"))

        self._extraTimeUnit = params.get("extraTimeUnit")
        if self._extraTimeUnit not in ['days', 'weeks']:
            raise FormValuesError(_("The extra allowed time unit is not valid!"))

    def _process( self ):
        if not self._cancel:
            regForm = self._conf.getRegistrationForm()
            params = self._getRequestParams()
            try:
                sDate = datetime(int(params["sYear"]), int(params["sMonth"]), int(params["sDay"]))
            except ValueError, e:
                raise FormValuesError("The start date you have entered is not correct: %s" % e, "RegistrationForm")
            try:
                eDate = datetime(int(params["eYear"]), int(params["eMonth"]), int(params["eDay"]))
            except ValueError, e:
                raise FormValuesError("The end date you have entered is not correct: %s" % e, "RegistrationForm")
            if eDate < sDate:
                raise FormValuesError("End date can't be before start date!", "RegistrationForm")
            try:
                meDate = None
                if params["meYear"] or params["meMonth"] or params["meDay"]:
                    meDate = datetime(int(params["meYear"]), int(params["meMonth"]), int(params["meDay"]))
            except ValueError, e:
                raise FormValuesError("The modification end date you have entered is not correct: %s" % e,
                                      "RegistrationForm")
            if meDate is not None and meDate < eDate:
                raise FormValuesError("Modification end date must be after end date!", "RegistrationForm")
            regForm.setStartRegistrationDate(sDate)
            regForm.setEndRegistrationDate(eDate)
            regForm.setEndExtraTimeAmount(self._extraTimeAmount)
            regForm.setEndExtraTimeUnit(self._extraTimeUnit)
            regForm.setModificationEndDate(meDate)
            regForm.setAnnouncement(params["announcement"])
            regForm.setTitle( params["title"] )
            regForm.setContactInfo( params["contactInfo"] )
            regForm.setUsersLimit( params["usersLimit"] )
            regForm.getNotification().setToList( utils.getEmailList(params.get("toList", "")) )
            regForm.getNotification().setCCList( utils.getEmailList(params.get("ccList", "")) )
            regForm.setMandatoryAccount(params.has_key("mandatoryAccount"))
            regForm.setNotificationSender(params["notificationSender"])
            regForm.setSendRegEmail(params.has_key("sendRegEmail"))
            regForm.setSendReceiptEmail(params.has_key("sendReceiptEmail"))
            regForm.setSendPaidEmail(params.has_key("sendPaidEmail"))
        self._redirect(urlHandlers.UHConfModifRegForm.getURL(self._conf))

class RHRegistrationFormActionStatuses( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._action=None
        if params.has_key("addStatus"):
            self._action=_ActionNewStatus(self, self._conf, params)
        if params.has_key("removeStatuses"):
            self._action=_ActionRemoveStatuses(self, self._conf, params)

    def _process( self ):
        if self._action is not None:
            r=self._action.perform()
            if r is not None:
                return r
        self._redirect("%s#statuses"%urlHandlers.UHConfModifRegForm.getURL(self._conf))

class _ActionNewStatus:

    def __init__(self, rh, conf, params):
        self._rh=rh
        self._conf=conf
        self._params=params

    def perform( self ):
        if self._params.get("caption","").strip() !="":
            self._conf.getRegistrationForm().addStatus(Status(self._conf.getRegistrationForm(), self._params))

class _ActionRemoveStatuses:

    def __init__(self, rh, conf, params):
        self._conf=conf
        self._rh=rh
        self._params=params

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self._rh, params )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key("cancel")
        self.statusesIds=self._rh._normaliseListParam(params.get("statusesIds",[]))
        self._statuses = []
        for id in self.statusesIds:
            self._statuses.append(self._conf.getRegistrationForm().getStatusById(id))

    def perform( self ):
        self._checkParams(self._params)
        if not self._cancel and self._statuses!=[]:
            if self._confirm:
                for st in self._statuses:
                    self._conf.getRegistrationForm().removeStatus(st)
            else:
                return registrationForm.WPConfModifRegFormStatusesRemConfirm( self._rh, self._conf, self.statusesIds).display()

class RHRegistrationFormModifStatusBase( RHRegistrationFormModifBase ):

    def _checkParams(self, params):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._status=self._conf.getRegistrationForm().getStatusById(params.get("statusId",""))

class _TmpStatus:

    def __init__(self, params, status=None):
        self._id=""
        self._caption=""
        self._counter=0
        self._values=[]
        self._defaultValue=None
        if status is not None:
            self._caption=status.getCaption()
            for sv in status.getStatusValuesList():
                nsv=sv.clone(self)
                nsv.setId(sv.getId())
                self._values.append(nsv)
            self._defaultValue = status.getDefaultValue().getId() if status.getDefaultValue() else None
        else:
            self.map(params)

    def getValues(self):
        d={}
        d['caption']=self.getCaption()
        d['values']=[]
        for v in self._values:
            d['values'].append({'id':v.getId(),'caption':v.getCaption()})
        d["defaultvalue"]=""
        if self._defaultValue is not None:
            d["defaultvalue"] = self._defaultValue
        return d

    def map(self, params):
        self._caption=params.get("caption","")
        if params.get("addvalue","").strip()!="":
            sv=StatusValue(self)
            cap=params.get("newvalue")
            if cap.strip()!="":
                sv.setCaption(params.get("newvalue"))
                sv.setId("t%s"%self._counter)
                self._counter+=1
                self._values.append(sv)
        elif params.get("removevalue","").strip()!="":
            vs=params.get("valuesIds",[])
            if type(vs)!=list:
                vs=[vs]
            for id in vs:
                self.removeValueById(id)
        elif params.get("defaultvalue","").strip()!="":
            vs=params.get("valuesIds",[])
            if type(vs)!=list:
                vs=[vs]
            if len(vs) == 1:
                self._defaultValue = vs[0]

    def getValueById(self, id):
        for v in self._values:
            if v.getId()==id:
                return v
        return None

    def removeValueById(self, id):
        for v in self._values:
            if v.getId()==id:
                self._values.remove(v)
                if v.getId() == self._defaultValue:
                    self._defaultValue = None
                return

    def getCaption(self):
        return self._caption

    def setCaption(self,c):
        self._caption=c

    def getDefaultValue(self):
        return self._defaultValue

    def getStatusValuesList(self, sort=False):
        r=self._values
        if sort:
            r.sort(StatusValue._cmpCaption)
        return r

class RHRegistrationFormStatusModif( RHRegistrationFormModifStatusBase ):

    def _checkParams(self, params):
        RHRegistrationFormModifStatusBase._checkParams(self, params)
        self._firstTime=params.get('firstTime','yes')!='no'

    def _process(self):
        if self._firstTime:
            session.pop('tmpStatus', None)
        tmpStatus = session.get('tmpStatus')
        if tmpStatus is None:
            tmpStatus = _TmpStatus(self._getRequestParams(), self._status)
        session['tmpStatus'] = tmpStatus
        p = registrationForm.WPConfModifRegFormStatusModif(self, self._status, tmpStatus)
        return p.display()

class RHRegistrationFormModifStatusPerformModif( RHRegistrationFormModifStatusBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifStatusBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        self._save = params.has_key("save")

    def _process( self ):
        if not self._cancel:
            # setup the server variable with the values for the section field
            tmpStatus = session.get('tmpStatus')
            if tmpStatus is None:
                raise MaKaCError(_("Error trying to modify the status"))
            else:
                tmpStatus.map(self._getRequestParams())
            session['tmpStatus'] = tmpStatus
            #-----
            if self._save:
                self._status.setValues(tmpStatus.getValues())
                session.pop('tmpStatus', None)
            else:
                urlModif=urlHandlers.UHConfModifRegFormStatusModif.getURL(self._status)
                urlModif.addParam("firstTime", "no")
                self._redirect(urlModif)
                return
        else:
            session.pop('tmpStatus', None)
        self._redirect("%s#statuses"%urlHandlers.UHConfModifRegForm.getURL(self._conf.getRegistrationForm()))


# START of RESTFUL

class RegistrationFormModifRESTBase(RHRegistrationFormModifBase):

    def getSectionsFossil(self):
        return fossilize(self._conf.getRegistrationForm().getSortedForms())

    def parseJsonItem(self, item):
        # Convert to boolean type
        if item.get('billable') and not isinstance(item.get('billable'), bool):
            item['billable'] = item.get('billable', 'false') == 'true'
        if item.get('enabled') and not isinstance(item.get('enabled'), bool):
            item['enabled'] = item.get('enabled', 'true') == 'true'
        if item.get('cancelled') and not isinstance(item.get('cancelled'), bool):
            item['cancelled'] = item.get('cancelled', 'false') == 'true'
        if item.get('isEnabled') and not isinstance(item.get('isEnabled'), bool):
            item['isEnabled'] = item.get('isEnabled', 'true') == 'true'
        if item.get('isBillable') and not isinstance(item.get('isBillable'), bool):
            item['isBillable'] = item.get('isBillable', 'false') == 'true'
        return item

    def _checkParams(self, params):
        RHRegistrationFormModifBase._checkParams(self, params)
        self._pm = ParameterManager(params)
        self._regForm = self._conf.getRegistrationForm()


class RHRegistrationModificationSectionQuery(RegistrationFormModifRESTBase):

    def _checkParams_POST(self):
        post_pm = ParameterManager(decode(request.data))
        self._sectionHeader = {}
        self._sectionHeader["title"] = post_pm.extract('title', pType=str, allowEmpty=False)
        self._sectionHeader["description"] = post_pm.extract('description', pType=str, allowEmpty=True)

    def _process_POST(self):
        pos = next((i for i, f in enumerate(self._regForm.getSortedForms()) if not f.isEnabled()), None)
        section = GeneralSectionForm(self._regForm, data=self._sectionHeader)
        self._regForm.addGeneralSectionForm(section, preserveTitle=True, pos=pos)
        return json.dumps(section.fossilize())


class RHRegistrationFormModifSectionBase(RegistrationFormModifRESTBase):

    def _checkParams(self, params):
        RegistrationFormModifRESTBase._checkParams(self, params)
        self._sectionId = self._pm.extract('sectionId', pType=str, allowEmpty=False)
        self._section = self._regForm.getSectionById(self._sectionId)
        if not self._section:
            raise MaKaCError(_("Invalid section Id"))


class RHRegistrationFormModifAccomodationBase(RegistrationFormModifRESTBase):

    def _checkParams(self, params):
        RegistrationFormModifRESTBase._checkParams(self, params)
        self._section = self._regForm.getSectionById("accommodation")


class RHRegistrationFormModifFurtherInformationBase(RegistrationFormModifRESTBase):

    def _checkParams(self, params):
        RegistrationFormModifRESTBase._checkParams(self, params)
        self._section = self._regForm.getSectionById("furtherInformation")


class RHRegistrationFormModifSocialEventsBase(RegistrationFormModifRESTBase):

    def _checkParams(self, params):
        RegistrationFormModifRESTBase._checkParams(self, params)
        self._section = self._regForm.getSectionById("socialEvents")


class RHRegistrationFormModifSessionsBase(RegistrationFormModifRESTBase):

    def _checkParams(self, params):
        RegistrationFormModifRESTBase._checkParams(self, params)
        self._section = self._regForm.getSectionById("sessions")


class RHRegistrationDeleteSection(RHRegistrationFormModifSectionBase):

    def _process_DELETE(self):
        if not self._section.isRequired():
            self._regForm.removeGeneralSectionForm(self._section)
        return json.dumps(self.getSectionsFossil())


class RHRegistrationFormSectionEnable(RHRegistrationFormModifSectionBase):

    def _process_POST(self):
        self._section.setEnabled(True)
        # Move the section to the last position
        self._regForm.addToSortedForms(self._section)
        return json.dumps(self._section.fossilize())


class RHRegistrationFormSectionDisable(RHRegistrationFormModifSectionBase):

    def _process_POST(self):
        self._section.setEnabled(False)
        # Move the section to the last position
        self._regForm.addToSortedForms(self._section)
        return json.dumps(self._section.fossilize())


class RHRegistrationFormSectionMove(RHRegistrationFormModifSectionBase):

    def _checkParams_POST(self):
        post_pm = ParameterManager(decode(request.data))
        self._sectionEndPos = post_pm.extract('endPos', pType=int, allowEmpty=False)

    def _process_POST(self):
        self._regForm.addToSortedForms(self._section, self._sectionEndPos)
        return json.dumps(self._section.fossilize())


class RHRegistrationFormSectionTitle(RHRegistrationFormModifSectionBase):

    def _checkParams_POST(self):
        post_pm = ParameterManager(decode(request.data))
        self._sectionTitle = post_pm.extract('title', pType=str, allowEmpty=False)

    def _process_POST(self):
        self._section.setTitle(self._sectionTitle)
        return json.dumps(self._section.fossilize())


class RHRegistrationFormSectionDescription(RHRegistrationFormModifSectionBase):

    def _checkParams_POST(self):
        post_pm = ParameterManager(decode(request.data))
        self._sectionDescription = post_pm.extract('description', pType=str, allowEmpty=True)

    def _process_POST(self):
        self._section.setDescription(self._sectionDescription)
        return json.dumps(self._section.fossilize())


class RHRegistrationFormAccommodationSetConfig(RHRegistrationFormModifAccomodationBase):

    def _checkParams_POST(self):
        defaultArrivalOffset = [-2, 0]
        defaultDepartureOffset = [1, 3]

        post_pm = ParameterManager(decode(request.data))
        self._arrivalOffsetDates = post_pm.extract(
            'arrivalOffsetDates',
            pType=list,
            allowEmpty=False,
            defaultValue=defaultArrivalOffset)
        self._departureOffsetDates = post_pm.extract(
            'departureOffsetDates',
            pType=list,
            allowEmpty=False,
            defaultValue=defaultDepartureOffset)
        self._items = post_pm.extract('items', pType=list, allowEmpty=False)

        if (len(self._arrivalOffsetDates) != 2 or
                self._arrivalOffsetDates[0] == '' or
                self._arrivalOffsetDates[1] == ''):
            self._arrivalOffsetDates = defaultArrivalOffset
        if (len(self._departureOffsetDates) != 2 or
                self._departureOffsetDates[0] == '' or
                self._departureOffsetDates[1] == ''):
            self._departureOffsetDates = defaultDepartureOffset

    def _setItems(self):
        for item in self._items:
            accoType = None
            if item.get('id') == 'isNew':
                accoType = AccommodationType(self._regForm)
                self._section.addAccommodationType(accoType)
            else:
                accoType = self._section.getAccommodationTypeById(item.get('id'))

            if 'remove' in item:
                self._section.removeAccommodationType(accoType)
            else:
                accoType.setValues(item)

    def _process_POST(self):
        self._section.setArrivalOffsetDates([int(-d) for d in self._arrivalOffsetDates])
        self._section.setDepartureOffsetDates([int(d) for d in self._departureOffsetDates])
        self._setItems()
        return json.dumps(self._section.fossilize())


class RHRegistrationFormFurtherInformationSetConfig(RHRegistrationFormModifFurtherInformationBase):

    def _checkParams_POST(self):
        post_pm = ParameterManager(decode(request.data))
        self._content = post_pm.extract('content', pType=str, allowEmpty=True)

    def _process_POST(self):
        self._section.setContent(self._content)
        return json.dumps(self._section.fossilize())


class RHRegistrationFormSocialEventsSetConfig(RHRegistrationFormModifSocialEventsBase):

    def _checkParams_POST(self):
        post_pm = ParameterManager(decode(request.data))
        self._introSentence = post_pm.extract('introSentence', pType=str, allowEmpty=False)
        self._selectionType = post_pm.extract('selectionType', pType=str, allowEmpty=False)
        self._items = post_pm.extract('items', pType=list, allowEmpty=False)
        self._mandatory = post_pm.extract('mandatory', pType=bool)

    def _setItems(self):
        for item in self._items:

            # Load or create social event
            socialEventItem = None
            if item.get('id') == 'isNew':
                socialEventItem = SocialEventItem(self._regForm)
                self._section.addSocialEvent(socialEventItem)
            else:
                socialEventItem = self._section.getSocialEventById(item.get('id'))

            # set or remove social event
            if 'remove' in item:
                self._section.removeSocialEvent(socialEventItem)
            else:
                socialEventItem.setValues(item)

    def _process_POST(self):
        self._section.setIntroSentence(self._introSentence)
        self._section.setSelectionType(self._selectionType)
        self._section.setMandatory(self._mandatory)
        self._setItems()
        return json.dumps(self._section.fossilize())


class RHRegistrationFormSessionsSetConfig(RHRegistrationFormModifSessionsBase):

    def _checkParams_POST(self):
        post_pm = ParameterManager(decode(request.data))
        self._type = post_pm.extract('type', pType=str, allowEmpty=False)
        self._items = post_pm.extract('items', pType=list, allowEmpty=False)

    def _setItems(self):
        for item in self._items:
            session = self._section.getSessionById(item.get('id'))
            if session is not None:
                session.setValues(item)
                if not item.get('enabled'):
                    self._section.removeSession(item.get('id'))
            else:
                session = self._conf.getSessionById(item.get('id'))
                if(item.get('enabled')):
                    s = self._conf.getSessionById(item.get('id'))
                    rs = session.getRegistrationSession()
                    if not rs:
                        rs = RegistrationSession(s, self._regForm)
                    else:
                        rs.setRegistrationForm(self._regForm)
                    self._section.addSession(rs)
                    rs.setValues(item)

    def _process_POST(self):
        if self._type in ["all", "2priorities"]:
            self._section.setType(self._type)
        else:
            raise MaKaCError(_("Unknown type"))
        self._setItems()
        return json.dumps(self._section.fossilize())


class RHRegistrationFormFieldCreate(RHRegistrationFormModifSectionBase):

    def _checkParams_POST(self):
        post_pm = ParameterManager(decode(request.data))
        self._fieldData = post_pm.extract('fieldData', pType=dict, allowEmpty=False)

    def _process_POST(self):
        if 'radioitems' in self._fieldData:
            radioitems = self._fieldData['radioitems']
            radioitems = [item for item in radioitems if not 'remove' in item]
            self._fieldData['radioitems'] = map(self.parseJsonItem, radioitems)
        # For compatibility reason the client side uses yesno
        if (self._fieldData['input'] == 'yesno'):
            self._fieldData['input'] = 'yes/no'
        field = GeneralField(self._section, data=self._fieldData)
        pos = next((i for i, f in enumerate(self._section.getSortedFields()) if f.isDisabled()), None)
        self._section.addToSortedFields(field, i=pos)
        return json.dumps(field.fossilize())


class RHRegistrationFormModifFieldBase(RHRegistrationFormModifSectionBase):

    def _checkParams(self, params):
        RHRegistrationFormModifSectionBase._checkParams(self, params)
        self._pm = ParameterManager(params)
        fieldId = self._pm.extract('fieldId', pType=str, allowEmpty=False)
        self._field = self._section.getFieldById(fieldId)
        if not self._field:
            raise MaKaCError(_("Invalid field Id"))


class RHRegistrationFormField(RHRegistrationFormModifFieldBase):

    def _checkParams_POST(self):
        post_pm = ParameterManager(decode(request.data))
        self._updateFieldData = post_pm.extract('fieldData', pType=dict, allowEmpty=False)
        self._updateFieldData['input'] = self._field.getInput().getId()

    def _process_POST(self):
        self._field.setValues(self._updateFieldData)
        return json.dumps(self._field.fossilize())

    def _process_DELETE(self):
        if self._field.isLocked('delete'):
            raise MaKaCError(_("Deleted action couldn't be perform"))
        self._section.removeField(self._field)
        return json.dumps(self._section.fossilize())


class RHRegistrationFormFieldEnable(RHRegistrationFormModifFieldBase):

    def _process_POST(self):
        # Move field to the first position
        self._section.addToSortedFields(self._field)
        self._field.setDisabled(False)
        return json.dumps(self._field.fossilize())


class RHRegistrationFormFieldDisable(RHRegistrationFormModifFieldBase):

    def _process_POST(self):
        if not self._field.isLocked('disable'):
            # Move field to the end of the list
            self._section.addToSortedFields(self._field)
            self._field.setDisabled(True)
        else:
            raise MaKaCError(_("Action couldn't be perform"))

        return json.dumps(self._field.fossilize())


class RHRegistrationFormFieldMove(RHRegistrationFormModifFieldBase):

    def _checkParams_POST(self):
        post_pm = ParameterManager(decode(request.data))
        self._sectionEndPos = post_pm.extract('endPos', pType=int, allowEmpty=False)

    def _process_POST(self):
        # If general section
        if self._section.getId().isdigit():
            # Enable field if moved out side of the disabled fields
            if (self._sectionEndPos == 0 or not self._section.getSortedFields()[self._sectionEndPos].isDisabled()):
                self._field.setDisabled(False)
            else:
                if self._field.isLocked('disable'):
                    return json.dumps(self._section.fossilize())
                    #w = Warning(_('Warning'), _('This field can\'t be disabled'))
                    #return ResultWithWarning(self._section.fossilize(), w).fossilize()
                else:
                    self._field.setDisabled(True)
            self._section.addToSortedFields(self._field, self._sectionEndPos)
        else:
            raise MaKaCError(_("Section id: " + self._section.getId() + " doesn't support field move"))

        return json.dumps(self._section.fossilize())
