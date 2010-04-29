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
import MaKaC.webinterface.pages.registrationForm as registrationForm
import MaKaC.webinterface.rh.conferenceModif as conferenceModif
from MaKaC.registration import AccommodationType, SocialEventItem, RegistrationSession, GeneralSectionForm, GeneralField, FieldInputs, RadioItem, Status, StatusValue
from MaKaC.errors import FormValuesError,MaKaCError, ConferenceClosedError
from datetime import datetime
from MaKaC.common import utils
from MaKaC.i18n import _

class RHRegistrationFormModifBase( conferenceModif.RHConferenceModifBase ):
    
    def _checkProtection( self ):
        if not self._target.canManageRegistration(self.getAW().getUser()):
            conferenceModif.RHConferenceModifBase._checkProtection(self)
        if self._target.getConference().isClosed():
            raise ConferenceClosedError(self._target.getConference())
        if not self._conf.hasEnabledSection("regForm"):
            raise MaKaCError( _("The registration form was disabled by the conference managers"))
        

class RHRegistrationPreview ( RHRegistrationFormModifBase ):

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
        
    def _process( self ):
        if not self._cancel:
            regForm = self._conf.getRegistrationForm()
            params = self._getRequestParams()
            try:
                sDate = datetime( int( params["sYear"] ), \
                                  int( params["sMonth"] ), \
                                  int( params["sDay"] ) )
            except ValueError,e:
                raise FormValuesError("The start date you have entered is not correct: %s"%e, "RegistrationForm")
            try:
                eDate = datetime( int( params["eYear"] ), \
                                  int( params["eMonth"] ), \
                                  int( params["eDay"] ) )
            except ValueError,e:
                raise FormValuesError("The end date you have entered is not correct: %s"%e, "RegistrationForm")
            if eDate < sDate :
                raise FormValuesError("End date can't be before start date!", "RegistrationForm")
            try:
                meDate = None
                if params["meYear"] or params["meMonth"] or params["meDay"]:
                    meDate = datetime( int( params["meYear"] ), \
                                  int( params["meMonth"] ), \
                                  int( params["meDay"] ) )
            except ValueError,e:
                raise FormValuesError("The modification end date you have entered is not correct: %s"%e, "RegistrationForm")
            if meDate is not None and (meDate < sDate or meDate < eDate):
                raise FormValuesError("End date must be after end date!", "RegistrationForm")
            regForm.setStartRegistrationDate(sDate)
            regForm.setEndRegistrationDate(eDate)
            regForm.setModificationEndDate(meDate)
            regForm.setAnnouncement(params["announcement"])
            regForm.setTitle( params["title"] )
            regForm.setContactInfo( params["contactInfo"] )
            regForm.setUsersLimit( params["usersLimit"] )
            regForm.getNotification().setToList( utils.getEmailList(params.get("toList", "")) )
            regForm.getNotification().setCCList( utils.getEmailList(params.get("ccList", "")) )
            regForm.setMandatoryAccount(params.has_key("mandatoryAccount"))
            regForm.setCurrency(params.get("Currency",""))
        self._redirect(urlHandlers.UHConfModifRegForm.getURL(self._conf))

class RHRegistrationFormModifSessions( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormSessions( self, self._conf )
        return p.display()

class RHRegistrationFormModifSessionsDataModif( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormSessionsDataModif( self, self._conf )
        return p.display()

class RHRegistrationFormModifSessionsPerformDataModif( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
    
    def _process( self ):
        if not self._cancel:
            ses = self._conf.getRegistrationForm().getSessionsForm()
            ses.setValues(self._getRequestParams())
        self._redirect(urlHandlers.UHConfModifRegFormSessions.getURL(self._conf))

class RHRegistrationFormModifSessionsAdd( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormSessionsAdd( self, self._conf )
        return p.display()

class RHRegistrationFormModifSessionsPerformAdd( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        self._sessionIds = self._normaliseListParam(params.get("sessionIds", []))
    
    def _process( self ):
        if not self._cancel:
            sesForm = self._conf.getRegistrationForm().getSessionsForm()
            for id in self._sessionIds:
                s = self._conf.getSessionById(id)
                rs = s.getRegistrationSession()
                if not rs:
                    rs = RegistrationSession(s, self._conf.getRegistrationForm())
                else:
                    rs.setRegistrationForm(self._conf.getRegistrationForm())
                sesForm.addSession(rs)
        self._redirect(urlHandlers.UHConfModifRegFormSessions.getURL(self._conf))

class RHRegistrationFormModifSessionsRemove( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._sessionsIds = self._normaliseListParam(params.get("sessionIds", []))
    
    def _process( self ):
        ses = self._conf.getRegistrationForm().getSessionsForm()
        for name in self._sessionsIds:
            ses.removeSession(name)
        self._redirect(urlHandlers.UHConfModifRegFormSessions.getURL(self._conf))

class RHRegistrationFormModifAccommodation( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormAccommodation( self, self._conf )
        return p.display()

class RHRegistrationFormModifAccommodationDataModif( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormAccommodationDataModif( self, self._conf )
        return p.display()

class RHRegistrationFormModifAccommodationPerformDataModif( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
    
    def _process( self ):
        if not self._cancel:
            acco = self._conf.getRegistrationForm().getAccommodationForm()
            acco.setValues(self._getRequestParams())
        self._redirect(urlHandlers.UHConfModifRegFormAccommodation.getURL(self._conf))

class RHRegistrationFormModifAccommodationTypeAdd( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormAccommodationTypeAdd( self, self._conf )
        return p.display()

class RHRegistrationFormModifAccommodationTypePerformAdd( RHRegistrationFormModifBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        self._caption = params.get("caption", "")
        if not self._cancel and self._caption.strip() == "":
            raise FormValuesError("You must introduce a caption")
    
    def _process( self ):
        if not self._cancel:
            acco = self._conf.getRegistrationForm().getAccommodationForm()
            accoType = AccommodationType(self._conf.getRegistrationForm())
            accoType.setCaption(self._caption)
            #accoType.setId(self._caption)
            acco.addAccommodationType(accoType)
        self._redirect(urlHandlers.UHConfModifRegFormAccommodation.getURL(self._conf))

class RHRegistrationFormModifAccommodationTypeRemove( RHRegistrationFormModifBase ):
    _uh = urlHandlers.UHConfModifRegFormAccommodationTypeRemove
    _accoTypeIds = []
    
    def __init__(self, req):   
        RHRegistrationFormModifBase.__init__(self,req)
        self._confirm = ""
        self._cancel = ""
        
    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._accoTypeIds = self._normaliseListParam(params.get("accommodationType", []))
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )

    def _process( self ):
        if self._accoTypeIds != []:
            if self._cancel:
                pass
            elif self._confirm:
                acco = self._conf.getRegistrationForm().getAccommodationForm()            
                for id in self._accoTypeIds:
                    accoType = acco.getAccommodationTypeById(id)
                    acco.removeAccommodationType(accoType)
            else:
                acco = self._conf.getRegistrationForm().getAccommodationForm()
                accommodationTypes = []
                for id in self._accoTypeIds:
                    accoType = acco.getAccommodationTypeById(id)
                    accommodationTypes.append(accoType.getCaption())
                return registrationForm.WPConfRemoveAccommodationType( self, self._conf, self._accoTypeIds, accommodationTypes).display()
        url = urlHandlers.UHConfModifRegFormAccommodation.getURL( self._conf )
        self._redirect( url )


class RHRegistrationFormAccommodationTypeModify( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        accoTypeId = params.get("accoTypeId", "")
        self._accoType = self._conf.getRegistrationForm().getAccommodationForm().getAccommodationTypeById(accoTypeId)
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormAccommodationTypeModify( self, self._conf, self._accoType )
        return p.display()

class RHRegistrationFormAccommodationTypePerformModify( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        accoTypeId = params.get("accoTypeId", "")
        self._accoType = self._conf.getRegistrationForm().getAccommodationForm().getAccommodationTypeById(accoTypeId)
        self._cancel = params.has_key("cancel")
    
    def _process( self ):
        if not self._cancel:
            self._accoType.setValues(self._getRequestParams())
        self._redirect(urlHandlers.UHConfModifRegFormAccommodation.getURL(self._conf))

class RHRegistrationFormModifFurtherInformation( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormFurtherInformation( self, self._conf )
        return p.display()

class RHRegistrationFormModifFurtherInformationDataModif( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormFurtherInformationDataModif( self, self._conf )
        return p.display()

class RHRegistrationFormModifFurtherInformationPerformDataModif( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
    
    def _process( self ):
        if not self._cancel:
            fi = self._conf.getRegistrationForm().getFurtherInformationForm()
            fi.setValues(self._getRequestParams())
        self._redirect(urlHandlers.UHConfModifRegFormFurtherInformation.getURL(self._conf))

class RHRegistrationFormModifReasonParticipation( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormReasonParticipation( self, self._conf )
        return p.display()

class RHRegistrationFormModifReasonParticipationDataModif( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormReasonParticipationDataModif( self, self._conf )
        return p.display()

class RHRegistrationFormModifReasonParticipationPerformDataModif( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
    
    def _process( self ):
        if not self._cancel:
            rp = self._conf.getRegistrationForm().getReasonParticipationForm()
            rp.setValues(self._getRequestParams())
        self._redirect(urlHandlers.UHConfModifRegFormReasonParticipation.getURL(self._conf))

class RHRegistrationFormModifSocialEvent( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormSocialEvent( self, self._conf )
        return p.display()

class RHRegistrationFormModifSocialEventDataModif( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormSocialEventDataModif( self, self._conf )
        return p.display()

class RHRegistrationFormModifSocialEventPerformDataModif( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
    
    def _process( self ):
        if not self._cancel:
            se = self._conf.getRegistrationForm().getSocialEventForm()
            se.setValues(self._getRequestParams())
        self._redirect(urlHandlers.UHConfModifRegFormSocialEvent.getURL(self._conf))

class RHRegistrationFormModifSocialEventAdd( RHRegistrationFormModifBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormSocialEventAdd( self, self._conf )
        return p.display()

class RHRegistrationFormModifSocialEventPerformAdd( RHRegistrationFormModifBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        self._caption = params.get("caption", "")
        if not self._cancel and self._caption.strip() == "":
            raise FormValuesError("You must introduce a caption")
    
    def _process( self ):
        if not self._cancel:
            se = self._conf.getRegistrationForm().getSocialEventForm()
            item = SocialEventItem(self._conf.getRegistrationForm())
            item.setCaption(self._caption)
            #item.setId(self._caption)
            se.addSocialEvent(item)
        self._redirect(urlHandlers.UHConfModifRegFormSocialEvent.getURL(self._conf))


class RHRegistrationFormModifSocialEventRemove( RHRegistrationFormModifBase ):
    _uh = urlHandlers.UHConfModifRegFormSocialEventRemove
    _socialEventIds = []
        
    def __init__(self,params):
        RHRegistrationFormModifBase.__init__(self,params)
        self._cancel = ""
        self._confirm = ""
    
    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._socialEventIds = self._normaliseListParam(params.get("socialEvents", []))
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )
    
    def _process( self ):
        if self._socialEventIds != []:
            if self._cancel:
                pass
            elif self._confirm:
                se = self._conf.getRegistrationForm().getSocialEventForm()
                for id in self._socialEventIds:
                    item = se.getSocialEventById(id)
                    se.removeSocialEvent(item)
            else:
                eventNames = []
                se = self._conf.getRegistrationForm().getSocialEventForm()
                for id in self._socialEventIds:
                    item = se.getSocialEventById(id)
                    eventNames.append(item.getCaption())
                return registrationForm.WPConfRemoveSocialEvent( self, self._conf, self._socialEventIds, eventNames ).display()
        url = urlHandlers.UHConfModifRegFormSocialEvent.getURL( self._conf )
        self._redirect( url )


class RHRegistrationFormSocialEventItemModify( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        socialEventId = params.get("socialEventId", "")
        self._socialEventItem = self._conf.getRegistrationForm().getSocialEventForm().getSocialEventById(socialEventId)
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormSocialEventItemModify( self, self._conf, self._socialEventItem )
        return p.display()

class RHRegistrationFormSocialEventItemPerformModify( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        socialEventId = params.get("socialEventId", "")
        self._socialEventItem = self._conf.getRegistrationForm().getSocialEventForm().getSocialEventById(socialEventId)
        self._cancel = params.has_key("cancel")
    
    def _process( self ):
        if not self._cancel:
            self._socialEventItem.setValues(self._getRequestParams())
        self._redirect(urlHandlers.UHConfModifRegFormSocialEvent.getURL(self._conf))

class RHRegistrationFormModifEnableSection( RHRegistrationFormModifBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._section = params.get("section", "")
    
    def _process( self ):
        section = self._conf.getRegistrationForm().getSectionById(self._section)
        if section is not None:
            section.setEnabled(not section.isEnabled())
        self._redirect(urlHandlers.UHConfModifRegForm.getURL(self._conf))


class RHRegistrationFormModifEnablePersonalField( RHRegistrationFormModifBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._personalfield = params.get("personalfield", "")
    
    def _process( self ):
        pdfield = self._conf.getRegistrationForm().getPersonalData().getDataItem(self._personalfield)
        if pdfield is not None:
            pdfield.setEnabled(not pdfield.isEnabled())
        url = str(urlHandlers.UHConfModifRegForm.getURL(self._conf)) + "#personalfields"
        self._redirect(url)


class RHRegistrationFormModifSwitchPersonalField( RHRegistrationFormModifBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._personalfield = params.get("personalfield", "")
    
    def _process( self ):
        pdfield = self._conf.getRegistrationForm().getPersonalData().getDataItem(self._personalfield)
        if pdfield is not None:
            pdfield.setMandatory(not pdfield.isMandatory())
        url = str(urlHandlers.UHConfModifRegForm.getURL(self._conf)) + "#personalfields"
        self._redirect(url)
        

class RHRegistrationFormActionSection( RHRegistrationFormModifBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._action=None
        if params.has_key("newSection"):
            self._action=_ActionNewSection(self, self._conf)
        if params.has_key("removeSection"):
            self._action=_ActionRemoveSection(self, self._conf, params)
        if params.has_key("oldpos") and params["oldpos"]!='':    
            self._action = _ActionMoveSection( self, self._conf, params)
        
    def _process( self ):
        if self._action is not None:
            r=self._action.perform()
            if r is not None:
                return r
        self._redirect("%s#sections"%urlHandlers.UHConfModifRegForm.getURL(self._conf))

class _ActionNewSection:

    def __init__(self, rh, conf):
        self._rh=rh
        self._conf=conf
    
    def perform( self ):
        self._conf.getRegistrationForm().addGeneralSectionForm(GeneralSectionForm(self._conf.getRegistrationForm()))

class _ActionRemoveSection:

    def __init__(self, rh, conf, params):
        self._conf=conf
        self._rh=rh
        self._params=params
    
    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self._rh, params )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key("cancel")
        self.sects=self._rh._normaliseListParam(params.get("sectionsIds",[]))
        self._sections = []
        for id in self.sects:
            self._sections.append(self._conf.getRegistrationForm().getGeneralSectionFormById(id))
    
    def perform( self ):
        self._checkParams(self._params)
        if not self._cancel and self._sections!=[]:
            if self._confirm:
                for sect in self._sections:
                    self._conf.getRegistrationForm().removeGeneralSectionForm(sect)
            else:
                return registrationForm.WPConfModifRegFormGeneralSectionRemConfirm( self._rh, self._conf, self.sects).display()

class _ActionMoveSection:

    def __init__(self,rh,conf,params):
        self._rh = rh
        self._conf=conf
        self._newpos = int(params['newpos'+params['oldpos']])
        self._oldpos = int(params['oldpos'])

    def perform(self):
        sList = self._conf.getRegistrationForm().getSortedForms()
        order = 0
        movedsect = sList[self._oldpos]
        self._conf.getRegistrationForm().addToSortedForms(movedsect, self._newpos)

#
# Added class to move field within section
#

class _ActionMoveField:

    def __init__(self,rh,conf,gs,params):
        self._rh = rh
        self._conf=conf
        self._gs = gs
        self._newpos = int(params['newpos'+params['oldpos']])
        self._oldpos = int(params['oldpos'])

    def perform(self):
        sList = self._gs.getSortedFields()
        order = 0
        movedField = sList[self._oldpos]
        self._gs.addToSortedFields(movedField, self._newpos)


class _RemoveFields:
    def __init__(self,gsf,fields):
        self._gsf = gsf 
        self._fields = fields

    def perform(self):   
        if type(self._fields) == type('string'):
            field = self._gsf.getFieldById(self._fields)
            self._gsf.removeField(field)
        else: 
            for fieldID in self._fields:
                field = self._gsf.getFieldById(fieldID)
                self._gsf.removeField(field)
            


class RHRegistrationFormModifGeneralSectionBase( RHRegistrationFormModifBase ):

    def _checkParams(self, params):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._generalSectionForm=self._conf.getRegistrationForm().getGeneralSectionFormById(params.get("sectionFormId",""))

class RHRegistrationFormModifGeneralSection( RHRegistrationFormModifGeneralSectionBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormGeneralSection( self, self._generalSectionForm )
        return p.display()

class RHRegistrationFormModifGeneralSectionDataModif( RHRegistrationFormModifGeneralSectionBase ):
    
    def _process( self ):
        p = registrationForm.WPConfModifRegFormGeneralSectionDataModif( self, self._generalSectionForm )
        return p.display()

class RHRegistrationFormModifGeneralSectionPerformDataModif( RHRegistrationFormModifGeneralSectionBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifGeneralSectionBase._checkParams( self, params )
        self._cancel = params.has_key("cancel") 
    def _process( self ):
        if not self._cancel:
            self._generalSectionForm.setValues(self._getRequestParams())
        self._redirect(urlHandlers.UHConfModifRegFormGeneralSection.getURL(self._generalSectionForm))
     
class _TmpSectionField:

    def __init__(self, params={}, generalField=None):
        self._caption=""
        self._mandatory=""
        self._input=None
        self._billable =""
        self._price = ""                
        if generalField is not None:
            self._caption=generalField.getCaption()
            self._mandatory=generalField.isMandatory()
            self._input=generalField.getInput().clone(self)
            self._billable =generalField.isBillable()
            self._price = generalField.getPrice()            
        else:
            self.map(params)

    def getValues(self):
        d={}
        d['caption']=self.getCaption()
        d['price']=self.getPrice();
        if self.isMandatory():
            d['mandatory']='True'
        if self.isBillable():
            d['billable']='True'                      
        d['input']=self.getInput().getId()
        d.update(self.getInput().getValues())
        return d
        
    def map(self, params):
        self._caption=params.get("caption","")
        self._mandatory=params.has_key("mandatory")
        self._billable=params.has_key("billable")
        self._price=params.get("price","")                
        if params.get("addradioitem","").strip()!="":
            ri=RadioItem(self._input)
            cap=params.get("newradioitem")
            if cap.strip()!="":
                ri.setCaption(params.get("newradioitem"))
                ri.setBillable(params.get("newbillable"))
                ri.setPrice(params.get("newprice"))
                self._input.addItem(ri)
        elif params.get("removeradioitem","").strip()!="":
            rs=params.get("radioitems",[])
            if type(rs)!=list:
                rs=[rs]
            for id in rs:
                self._input.removeItemById(id)
        elif params.get("disableradioitem","").strip()!="":
            rs=params.get("radioitems",[])
            if type(rs)!=list:
                rs=[rs]
            for id in rs:
                self._input.disableItemById(id)
        elif params.get("defaultradioitem","").strip()!="":
            rs=params.get("radioitems",[])
            if type(rs)!=list:
                rs=[rs]
            for id in rs:
                self._input.setDefaultItemById(id)
        elif not params.has_key("save") or self._input is None:
            self._input=FieldInputs.getAvailableInputKlassById(params.get("input","text"))(self)

    def isBillable(self):
        return self._billable
    
    def setBillable(self,v):
        self._billable=v
        
    def getPrice(self):
        return self._price
    
    def setPrice(self,price):
        self._price=price     
        
    def getCaption(self):
        return self._caption

    def setCaption(self, caption):
        self._caption = caption

    def getInput(self):
        return self._input

    def setInput(self, input):
        self._input = input

    def isMandatory(self):
        return self._mandatory

    def setMandatory(self, v):
        self._mandatory = v

class RHRegistrationFormModifGeneralSectionFieldAdd( RHRegistrationFormModifGeneralSectionBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifGeneralSectionBase._checkParams( self, params )
        self._firstTime=params.get('firstTime','yes')!='no'

    def _process( self ):
        tmpField=None
        if not self._firstTime:
            tmpField=self._getSession().getVar("tmpSectionField")
        else:
            self._getSession().removeVar("tmpSectionField")
            tmpField=_TmpSectionField(self._getRequestParams(), None) 
            self._getSession().setVar("tmpSectionField",tmpField)
        p = registrationForm.WPConfModifRegFormGeneralSectionFieldAdd( self, self._generalSectionForm, tmpField )
        return p.display()

class RHRegistrationFormModifGeneralSectionFieldPerformAdd( RHRegistrationFormModifGeneralSectionBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifGeneralSectionBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        self._save = params.has_key("save")
    
    def _process( self ):
        if not self._cancel:
            # setup the server variable with the values for the section field
            tmpSectionField=self._getSession().getVar("tmpSectionField")
            if tmpSectionField == None:
                tmpSectionField=_TmpSectionField(self._getRequestParams(), None)
            else:
                tmpSectionField.map(self._getRequestParams())
            self._getSession().setVar("tmpSectionField", tmpSectionField)
            #-----
            if self._save:
                #############
                #Change to support sorting fields...
                #self._generalSectionForm.addField(GeneralField(self._generalSectionForm, tmpSectionField.getValues()))
                #
                self._generalSectionForm.addToSortedFields(GeneralField(self._generalSectionForm, tmpSectionField.getValues()))
                self._getSession().removeVar("tmpSectionField")
            else:
                urlfield=urlHandlers.UHConfModifRegFormGeneralSectionFieldAdd.getURL(self._generalSectionForm)
                urlfield.addParam("firstTime",'no')
                self._redirect(urlfield)
                return
        else:
            self._getSession().removeVar("tmpSectionField")
        self._redirect(urlHandlers.UHConfModifRegFormGeneralSection.getURL(self._generalSectionForm))

class RHRegistrationFormModifGeneralSectionFieldModif( RHRegistrationFormModifGeneralSectionBase ):
    def _checkParams( self, params ):
        RHRegistrationFormModifGeneralSectionBase._checkParams( self, params )
        self._sectionField = self._generalSectionForm.getFieldById(params.get("sectionFieldId", ""))
        self._firstTime=params.get('firstTime','yes')!='no'
    
    def _process( self ):
        # setup the server variable with the values for the section field
        if self._firstTime:
            self._getSession().removeVar("tmpSectionField")
        tmpSectionField=self._getSession().getVar("tmpSectionField")
        if tmpSectionField == None:
            tmpSectionField=_TmpSectionField(generalField=self._sectionField)
        self._getSession().setVar("tmpSectionField", tmpSectionField)
        #-----
        p = registrationForm.WPConfModifRegFormGeneralSectionFieldModif( self, self._sectionField, tmpSectionField)
        return p.display()


class RHRegistrationFormModifGeneralSectionFieldPerformModif( RHRegistrationFormModifGeneralSectionBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifGeneralSectionBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        self._save = params.has_key("save")
        self._sectionField = self._generalSectionForm.getFieldById(params.get("sectionFieldId", ""))
    
    def _process( self ):
        if not self._cancel:
            # setup the server variable with the values for the section field
            tmpSectionField=self._getSession().getVar("tmpSectionField")
            if tmpSectionField == None:
                tmpSectionField=_TmpSectionField(sectionField=self._sectionField)
            else:
                tmpSectionField.map(self._getRequestParams())
            self._getSession().setVar("tmpSectionField", tmpSectionField)
            #-----
            if self._save:
                if self._sectionField is not None:
                    self._sectionField.setValues(tmpSectionField.getValues())
                self._getSession().removeVar("tmpSectionField")
            else:
                urlfield=urlHandlers.UHConfModifRegFormGeneralSectionFieldModif.getURL(self._sectionField)
                urlfield.addParam("firstTime",'no')
                self._redirect(urlfield)
                return
        else:
            self._getSession().removeVar("tmpSectionField")
        self._redirect(urlHandlers.UHConfModifRegFormGeneralSection.getURL(self._generalSectionForm))


class RHRegistrationFormModifGeneralSectionFieldProcess( RHRegistrationFormModifGeneralSectionBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifGeneralSectionBase._checkParams( self, params )

        #
        #Mods to support sorting of fields..
        #
        #old code:
        #self._cancel = params.has_key("cancel")
        #self._confirm = params.has_key( "confirm" )
        #self.fields=self._normaliseListParam(params.get("fieldsIds",[]))
        #raise(str(params))
        #self._sectionFields = []
        #for id in self.fields:
        #    self._sectionFields.append(self._generalSectionForm.getFieldById(id))
        #
        #new code:
        #
        self._action=None
        if params.has_key("remove"):
           if params["remove"] == "remove":
               gsf = self._generalSectionForm
               self._action = _RemoveFields(self._generalSectionForm,params.get("fieldsIds"))
        if params.has_key("cancel"):
            self._action=_ActionCancel()
        if params.has_key("confirm"):
            self._action=_ActionConfirm()
        if params.has_key("oldpos") and params["oldpos"] != '':
            self._action=_ActionMoveField(self,self._conf,self._generalSectionForm,params)
        
    
    def _process( self ):
        #
        # Mods to support field sorting.
        # old code:
        #if not self._cancel and self.fields!=[]:
        #    if self._confirm:
        #        for field in self._sectionFields:
        #            self._generalSectionForm.removeField(field)
        #    else:
        #        return registrationForm.WPConfModifRegFormGeneralSectionFieldRemConfirm( self, self._generalSectionForm, self.fields).display()
        #
        #new code:
        #

        if self._action != None:
           r = self._action.perform()
           if r is not None:
              return r

        self._redirect(urlHandlers.UHConfModifRegFormGeneralSection.getURL(self._generalSectionForm))


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
            self._defaultValue=status.getDefaultValue()
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
            d["defaultvalue"]=self._defaultValue.getId()
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
                v=self.getValueById(vs[0])
                self._defaultValue=v

    def getValueById(self, id):
        for v in self._values:
            if v.getId()==id:
                return v
        return None

    def removeValueById(self, id):
        for v in self._values:
            if v.getId()==id:
                self._values.remove(v)
                if v == self._defaultValue:
                    self._defaultValue=None
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
    
    def _process( self ):
        if self._firstTime:
            self._getSession().removeVar("tmpStatus")
        tmpStatus=self._getSession().getVar("tmpStatus")
        if tmpStatus is None:
            tmpStatus=_TmpStatus(self._getRequestParams(), self._status)
        self._getSession().setVar("tmpStatus", tmpStatus)
        p = registrationForm.WPConfModifRegFormStatusModif( self, self._status, tmpStatus )
        return p.display()

class RHRegistrationFormModifStatusPerformModif( RHRegistrationFormModifStatusBase ):
    
    def _checkParams( self, params ):
        RHRegistrationFormModifStatusBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        self._save = params.has_key("save")
    
    def _process( self ):
        if not self._cancel:
            # setup the server variable with the values for the section field
            tmpStatus=self._getSession().getVar("tmpStatus")
            if tmpStatus == None:
                raise MaKaCError( _("Error trying to modify the status"))
            else:
                tmpStatus.map(self._getRequestParams())
            self._getSession().setVar("tmpStatus", tmpStatus)
            #-----
            if self._save:
                self._status.setValues(tmpStatus.getValues())
                self._getSession().removeVar("tmpStatus")
            else:
                urlModif=urlHandlers.UHConfModifRegFormStatusModif.getURL(self._status)
                urlModif.addParam("firstTime", "no")
                self._redirect(urlModif)
                return
        else:
            self._getSession().removeVar("tmpStatus")
        self._redirect("%s#statuses"%urlHandlers.UHConfModifRegForm.getURL(self._conf.getRegistrationForm()))
