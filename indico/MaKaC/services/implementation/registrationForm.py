# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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


"""
Asynchronous request handlers for registration form related data modification.
"""

from MaKaC.common.logger import Logger
from MaKaC.i18n import _

from MaKaC.services.implementation.base import ParameterManager
from MaKaC.services.implementation.conference import ConferenceModifBase, ConferenceDisplayBase
from MaKaC.services.interface.rpc.common import ServiceError, ServiceAccessError, Warning, \
        ResultWithWarning, TimingNoReportError, NoReportError, ResultWithHighlight
from MaKaC.registration import AccommodationType, SocialEventItem, RegistrationSession, GeneralSectionForm, GeneralField

from indico.util.fossilize import fossilize
from itertools import ifilter


class RegistrationFormDisplayBase( ConferenceDisplayBase ):

    def getFormFossil( self ):
        sectionList = self._conf.getRegistrationForm().getSortedForms()
        return { 'sections'     : fossilize( ifilter( lambda x: x.isEnabled(), sectionList ) ),
                  'currency'    : self._conf.getRegistrationForm().getCurrency()
               }

    def getSectionsFossil( self ):
        sectionList = self._conf.getRegistrationForm().getSortedForms()
        return fossilize( ifilter( lambda x: x.isEnabled(), sectionList ))

    def _checkParams( self ):
        ConferenceDisplayBase._checkParams( self )
        self._regForm = self._conf.getRegistrationForm()

class RegistrationFormModifBase( ConferenceModifBase ):

    def getFormFossil( self ):
        return { 'sections'     : fossilize( self._conf.getRegistrationForm().getSortedForms() ),
                  'currency'    : self._conf.getRegistrationForm().getCurrency()
               }
    def getSectionsFossil( self ):
        return fossilize( self._conf.getRegistrationForm().getSortedForms() )

    def parseJsonItem(self, item):
        # Convert to boolean type
        item['billable'] = item.get( 'billable', 'false' ) == 'true'
        item['enabled'] = item.get( 'enabled', 'true' ) == 'true'
        item['cancelled'] = item.get( 'cancelled', 'false' ) == 'true'
        item['isEnabled'] = item.get( 'isEnabled', 'true' ) == 'true'
        return item

    def _checkProtection( self ):
        if not self._target.canManageRegistration( self.getAW().getUser() ):
            ConferenceModifBase._checkProtection( self )

    def _checkParams( self ):
        ConferenceModifBase._checkParams( self )
        self._regForm = self._conf.getRegistrationForm()

class RegistrationFormModifSectionBase( RegistrationFormModifBase ):

    def _checkParams( self ):
        RegistrationFormModifBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._sectionId = self._pm.extract( 'sectionId', pType=str, allowEmpty=False )
        try:
            self._section = self._regForm.getSectionById( self._sectionId )
        except:
            raise ServiceError( "", _( "Invalid section Id" ) )

class RegistrationFormDisplay ( RegistrationFormDisplayBase ):

    def _getAnswer( self ):
        return self.getFormFossil()

class RegistrationFormEdition ( RegistrationFormModifBase ):

    def _getAnswer( self ):
        return  self.getFormFossil()

class RegistrationFormSectionCreate ( RegistrationFormModifBase ):

    def _checkParams( self ):
        RegistrationFormModifBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._sectionHeader = self._pm.extract( 'sectionHeader', pType=dict, allowEmpty=False )

    def _getAnswer( self ):
        pos = next((i for i, f in enumerate(self._regForm.getSortedForms()) if not f.isEnabled()), None)
        section = GeneralSectionForm( self._regForm, data=self._sectionHeader )
        self._regForm.addGeneralSectionForm( section, preserveTitle=True, pos=pos )
        return ResultWithHighlight(self.getSectionsFossil(), section.fossilize()).fossilize()

class RegistrationFormSectionRemove ( RegistrationFormModifSectionBase ):

    def _getAnswer( self ):
        if not self._section.isRequired():
            self._regForm.removeGeneralSectionForm( self._section )
        return self.getSectionsFossil()

class RegistrationFormSectionEnable ( RegistrationFormModifSectionBase ):

    def _getAnswer( self ):
        self._section.setEnabled( True )
        # Move the section to the first position
        self._regForm.addToSortedForms( self._section, 0 )
        return ResultWithHighlight( self.getSectionsFossil(), self._section.fossilize()).fossilize()

class RegistrationFormSectionDisable ( RegistrationFormModifSectionBase ):

    def _getAnswer( self ):
        self._section.setEnabled( False )
        # Move the section to the end
        self._regForm.addToSortedForms( self._section )
        return self.getSectionsFossil()

class RegistrationFormSectionMove ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._sectionEndPos = self._pm.extract( 'endPos', pType=str, allowEmpty=False )
        try:
            self._sectionEndPos = int( self._sectionEndPos )
        except ValueError:
            raise ServiceError( "", _( "Invalid value type for end position. Type must be an int" ) )

    def _getAnswer( self ):
        self._regForm.addToSortedForms( self._section, self._sectionEndPos )
        return self.getSectionsFossil()

class RegistrationFormSectionSetHeader ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._sectionTitle = self._pm.extract( "title", pType=str, defaultValue=False, allowEmpty=True )
        self._sectionDescription = self._pm.extract( "description", pType=str, defaultValue=False, allowEmpty=True )

    def _getAnswer( self ):

        if self._sectionTitle != False:
            if self._sectionTitle == "":
                raise NoReportError( _( "Invalid title (can not be empty)" ) )
            self._section.setTitle( self._sectionTitle )

        if self._sectionDescription != False:
            self._section.setDescription( self._sectionDescription )

        return self._section.fossilize()

class RegistrationFormAccommodationSetConfig ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._datesOffsets = self._pm.extract( 'datesOffsets', pType=dict, allowEmpty=False )

    def _getAnswer ( self ):
        arrDates = [int( self._datesOffsets.get( "aoffset1", -2 ) ), int( self._datesOffsets.get( "aoffset2", 0 ) )]
        depDates = [int( self._datesOffsets.get( "doffset1", 1 ) ), int( self._datesOffsets.get( "doffset2", 3 ) )]
        self._section.setArrivalOffsetDates( arrDates )
        self._section.setDepartureOffsetDates( depDates )
        return self._section.fossilize()

class RegistrationFormSocialEventsSetConfig ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._intro = self._pm.extract( 'intro', pType=str, allowEmpty=False )
        self._selectionType = self._pm.extract( 'selectionType', pType=str, allowEmpty=False )

    def _getAnswer ( self ):
        self._section.setIntroSentence( self._intro )
        self._section.setSelectionType( self._selectionType )
        return self._section.fossilize()

class RegistrationFormSessionsSetConfig ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._type = self._pm.extract( 'type', pType=str, allowEmpty=False )

    def _getAnswer ( self ):
        if ( self._type == "all" or self._type == "2priorities" ):
            self._section.setType( self._type );
        else :
            raise ServiceError( "", _( "Unknown type" ) )
        return self._section.fossilize()

class RegistrationFormAccommodationSetItems ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._items = map(self.parseJsonItem, self._pm.extract( 'items', pType=list, allowEmpty=False ))

    def _getAnswer ( self ):
        for item in self._items:

            accoType = None
            if item['id'] == 'isNew':
                accoType = AccommodationType( self._regForm )
                self._section.addAccommodationType( accoType )
            else:
                accoType = self._section.getAccommodationTypeById( item['id'] )


            if item.has_key( 'remove' ):
                self._section.removeAccommodationType( accoType )
            else:
                accoType.setValues( item )

        return self._section.fossilize()

class RegistrationFormSocialEventsSetItems ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._items = self._pm.extract( 'items', pType=list, allowEmpty=False )

    def _getAnswer ( self ):
        for item in self._items:

            # Convert to boolean type
            if item.has_key('billable'):
                item['billable'] = item['billable'] == 'true'
            if item.has_key('pricePerPlace'):
                item['pricePerPlace'] = item['pricePerPlace'] == 'true'
            if item.has_key('cancelled'):
                item['cancelled'] = item['cancelled'] == 'true'

            # Load or create social event
            socialEventItem = None
            if item['id'] == 'isNew':
                socialEventItem = SocialEventItem( self._regForm )
                self._section.addSocialEvent( socialEventItem )
            else :
                socialEventItem = self._section.getSocialEventById( item['id'] )

            # set or remove social event
            if item.has_key( 'remove' ):
                self._section.removeSocialEvent( socialEventItem )
            else :
                socialEventItem.setValues( item )

        return self._section.fossilize()

class RegistrationFormSessionsSetItems ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._items = self._pm.extract( 'items', pType=list, allowEmpty=False )

    def _getAnswer ( self ):
        for item in self._items:

            # Convert to boolean type
            item['billable'] = item.get( 'billable', False ) == 'true'
            item['enabled'] = item.get( 'enabled', False ) == 'true'

            session = self._section.getSessionById( item['id'] )
            if( session != None ):
                session.setValues( item )
                if not item['enabled'] :
                    self._section.removeSession( item['id'] )
            else:
                session = self._conf.getSessionById( item['id'] )
                if( item['enabled'] ):
                    s = self._conf.getSessionById( item['id'] )
                    rs = session.getRegistrationSession()
                    if not rs:
                        rs = RegistrationSession( s, self._regForm )
                    else:
                        rs.setRegistrationForm( self._regForm )
                    self._section.addSession( rs )
                    rs.setValues( item )

        return self._section.fossilize()

class RegistrationFormFieldCreate ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._fieldData = self._pm.extract( 'field', pType=dict, allowEmpty=False )


    def _getAnswer( self ):

        if self._fieldData.has_key('billable'):
            self._fieldData['billable'] = self._fieldData['billable'] == 'true'
        if (self._fieldData.has_key('radioitems')):
            radioitems = self._fieldData['radioitems']
            radioitems = [item for item in radioitems if not item.has_key('remove')]
            self._fieldData['radioitems'] = map(self.parseJsonItem, radioitems)
        # For compatibility reason the client side uses yesno
        if (self._fieldData['input'] == 'yesno'):
            self._fieldData['input'] = 'yes/no'  
        field = GeneralField( self._section, data = self._fieldData )
        pos = next((i for i, f in enumerate(self._section.getSortedFields()) if f.isDisabled()), None)
        self._section.addToSortedFields( field, i=pos );
        return ResultWithHighlight(self._section.fossilize(), field.fossilize()).fossilize()

class RegistrationFormFieldSetStatus ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._fieldId = self._pm.extract( 'fieldId', pType=str, allowEmpty=False )
        self._action = self._pm.extract( 'action', pType=str, allowEmpty=False )

    def _getAnswer( self ):
        field = self._section.getFieldById( self._fieldId )
        if not field.isLocked( 'delete' ) and self._action == 'remove':
            self._section.removeField( field )
        elif not field.isLocked( 'disable' ) and self._action == 'disable':
            # Move field to the end of the list
            self._section.addToSortedFields( field )
            field.setDisabled( True )
        elif  self._action == 'enable':
            # Move field to the first position
            self._section.addToSortedFields( field, 0 )
            field.setDisabled( False )
        else:
            raise ServiceError( "", _( "Action couldn't be perform" ) )

        return ResultWithHighlight(self._section.fossilize(), field.fossilize()).fossilize()

class RegistrationFormFieldSetItems ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._fieldId = self._pm.extract( 'fieldId', pType=str, allowEmpty=False )
        self._items = self._pm.extract( 'items', pType=list, allowEmpty=False )

    def _getAnswer( self ):
        field = self._section.getFieldById( self._fieldId ).getInput()
        for i in range( 0, len( self._items ) ):
            itemValues = self._items[i]
            itemValues["isEnabled"] = itemValues["isEnabled"] == "true"
            itemValues["billable"] = itemValues["billable"] == "true"
            item = field.getItemById( itemValues['id'] )
            if ( item == None ):
                field.createItem( itemValues, i )
            else:
                # remove else set and move
                if itemValues.has_key( 'remove' ):
                    field.removeItem( item )
                else :
                    item.setValues( itemValues )
                    field.addItem( item, i )

        return ResultWithHighlight(self._section.fossilize(),self._section.getFieldById( self._fieldId).fossilize()).fossilize()

class RegistrationFormFieldMove ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._sectionEndPos = self._pm.extract( 'endPos', pType=str, allowEmpty=False )
        self._fieldId = self._pm.extract( 'fieldId', pType=str, allowEmpty=False )
        try:
            self._sectionEndPos = int( self._sectionEndPos )
        except ValueError:
            raise ServiceError( "", _( "Invalid value type for end position. Type must be an int" ) )

    def _getAnswer( self ):
        # If general section
        if self._section.getId().isdigit():
            movedField = self._section.getFieldById( self._fieldId )
            # Enable field if moved out side of the disabled fields
            if ( self._sectionEndPos == 0 or not self._section.getSortedFields()[self._sectionEndPos].isDisabled() ):
                movedField.setDisabled( False )
            else :
                if movedField.isLocked( 'disable' ):
                    w = Warning(_('Warning'), _('This field can\'t be disabled'))
                    return ResultWithWarning(self._section.fossilize(), w).fossilize()
                else :
                    movedField.setDisabled( True )
            self._section.addToSortedFields( movedField, self._sectionEndPos )
        else :
            raise ServiceError( "", _( "Section id: " + self._section.getId() + " doesn't support field move" ) )

        return self._section.fossilize()

class RegistrationFormFieldSet ( RegistrationFormModifSectionBase ):

    def _checkParams( self ):
        RegistrationFormModifSectionBase._checkParams( self )
        self._pm = ParameterManager( self._params )
        self._updateFieldData = self._pm.extract( 'updateFieldData', pType=dict, allowEmpty=False )
        fieldId = self._pm.extract( 'fieldId', pType=str, allowEmpty=False )
        try:
            self._field = self._section.getFieldById( fieldId )
        except:
            raise ServiceError( "", _( "Invalid field Id : " + fieldId ) )

    def _getAnswer( self ):
        self._updateFieldData['input'] = self._field.getInput().getId()
        self._field.setValues( self._updateFieldData )
        return ResultWithHighlight(self._section.fossilize(), self._field.fossilize()).fossilize()

class RegistrationFormUserData( RegistrationFormDisplayBase ):

    def _getAnswer( self ):
        user = self._aw.getUser()
        reg_data = {}
        if user is not None and user.isRegisteredInConf(self._conf):
            registrant = user.getRegistrantById(self._conf.getId())
            reg_data = fossilize(registrant)
        else:
            personalData = self._regForm.getPersonalData()
            reg_data['avatar'] = personalData.getFormValuesFromAvatar(user)
        return reg_data

methodMap = {
    "registrationForm.FormDisplay"                         : RegistrationFormDisplay,
    "registrationForm.FormModification"                    : RegistrationFormEdition,

    "registrationForm.SectionCreate"                       : RegistrationFormSectionCreate,
    "registrationForm.SectionRemove"                       : RegistrationFormSectionRemove,
    "registrationForm.SectionEnable"                       : RegistrationFormSectionEnable,
    "registrationForm.SectionDisable"                      : RegistrationFormSectionDisable,
    "registrationForm.SectionMove"                         : RegistrationFormSectionMove,

    "registrationForm.SectionSetHeader"                    : RegistrationFormSectionSetHeader,
    "registrationForm.SectionAccommodationSetConfig"       : RegistrationFormAccommodationSetConfig,
    "registrationForm.SectionSocialEventsSetConfig"        : RegistrationFormSocialEventsSetConfig,
    "registrationForm.SectionSessionsSetConfig"            : RegistrationFormSessionsSetConfig,
    "registrationForm.SectionAccommodationSetItems"        : RegistrationFormAccommodationSetItems,
    "registrationForm.SectionSocialEventsSetItems"         : RegistrationFormSocialEventsSetItems,
    "registrationForm.SectionSessionsSetItems"             : RegistrationFormSessionsSetItems,

    "registrationForm.FieldCreate"                         : RegistrationFormFieldCreate,
    "registrationForm.FieldMove"                           : RegistrationFormFieldMove,
    "registrationForm.FieldSetStatus"                      : RegistrationFormFieldSetStatus,
    "registrationForm.FieldRadioSetItems"                  : RegistrationFormFieldSetItems,
    "registrationForm.FieldSet"                            : RegistrationFormFieldSet,

    "registrationForm.UserData"                            : RegistrationFormUserData,
   }
