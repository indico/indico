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

from MaKaC.common.fossilize import IFossil
from MaKaC.webinterface.urlHandlers import UHFileAccess
from indico.util.date_time import format_date, format_datetime
from MaKaC.common.Conversion import Conversion


###################
# item type fossil
###################
class IRegFormRadioItemFossil(IFossil):

    def getId(self):
        """
        Item id
        """

    def getCaption(self):
        """
        Item caption
        """

    def getPrice(self):
        """
        Item price
        """

    def getPlacesLimit(self):
        """
        Item places limit
        """

    def getNoPlacesLeft(self):
        """
        Number of remaining places
        """

    def isEnabled(self):
        """
        Is item enabled
        """

    def isBillable(self):
        """
        Is item billable
        """


class IRegFormAccommodationTypeItemFossil(IFossil):

    def getId(self):
        """
        Item id
        """

    def getCaption(self):
        """
        Item caption
        """

    def getPlacesLimit(self):
        """
        Places limit
        """

    def getPrice(self):
        """
        Accommodation price
        """

    def getCurrency(self):
        """
        Accommodation price currency
        """

    def getNoPlacesLeft(self):
        """
        Current number of left places
        """

    def isBillable(self):
        """
        is billable
        """
    isBillable.name = 'billable'

    def isCancelled(self):
        """
        Is cancelled
        """
    isCancelled.name = 'cancelled'


class IRegFormRegistrationSessionItemFossil(IFossil):

    def getId(self):
        """
        Registration session id
        """

    def getCaption(self):
        """
        registration session title
        """

    def getStartDate(self):
        """
        registration session start date
        """

    def getCode(self):
        """
        registration session start date
        """

    def isEnabled(self):
        """
        is billable
        """
    isEnabled.produce = lambda s: True
    isEnabled.name = 'enabled'

    def getPrice(self):
        """
        registration session price
        """

    def getCurrency(self):
        """
        registration session price currency
        """

    def isBillable(self):
        """
        is billable
        """
    isBillable.name = 'billable'


class IRegFormSocialEventItemFossil(IFossil):

    def getId(self):
        """
        item id
        """

    def getCaption(self):
        """
        Item caption
        """

    def getCancelledReason(self):
        """
        get cancelled reason
        """

    def getMaxPlacePerRegistrant(self):
        """
        Max place per registrant
        """
    getMaxPlacePerRegistrant.name = 'maxPlace'

    def getPlacesLimit(self):
        """
        Places limit
        """

    def getNoPlacesLeft(self):
        """
        Number of places left
        """

    def getPrice(self):
        """
        item price
        """

    def getCurrency(self):
        """
        item currency
        """

    def isBillable(self):
        """
        Is billable
        """
    isBillable.name = 'billable'

    def isCancelled(self):
        """
        Is cancelled
        """
    isCancelled.name = 'cancelled'

    def isPricePerPlace(self):
        """
        Is the price per place
        """
    isPricePerPlace.name = 'pricePerPlace'


#####################
# input type fossil
#####################
class IRegFormInputFieldBaseFossil(IFossil):

    def getHTMLName(self):
        """
        Get the HTML name of the item
        """
    getHTMLName.name = 'HTMLName'


class IRegFormTextInputFieldFossil(IRegFormInputFieldBaseFossil):

    def getLength(self):
        """
        Field length
        """


class IRegFormTextareaInputFieldFossil(IRegFormInputFieldBaseFossil):

    def getNumberOfRows(self):
        """
        Field number of rows
        """

    def getNumberOfColumns(self):
        """
        Field number of columns
        """


class IRegFormLabelInputFieldFossil(IRegFormInputFieldBaseFossil):

    pass


class IRegFormNumberInputFieldFossil(IRegFormInputFieldBaseFossil):

    def getLength(self):
        """
        Field length
        """

    def getMinValue(self):
        """
        Field minimum value
        """


class IRegFormRadioGroupInputFieldFossil(IRegFormInputFieldBaseFossil):

    def getDefaultItem(self):
        """
        default item
        """

    def getInputType(self):
        """
        field input type
        """

    def getEmptyCaption(self):
        """
        field empty caption
        """

    def getItemsList(self):
        """
        Field Caption
        """
    getItemsList.name = 'radioitems'
    getItemsList.result = IRegFormRadioItemFossil


class IRegFormCheckboxInputFieldFossil(IRegFormInputFieldBaseFossil):

    pass


class IRegFormYesNoInputFieldFossil(IRegFormInputFieldBaseFossil):

    pass


class IRegFormFileInputFieldFossil(IRegFormInputFieldBaseFossil):

    pass


class IRegFormCountryInputFieldFossil(IRegFormInputFieldBaseFossil):

    def getCountriesList(self):
        """
        the countries list
        """
    getCountriesList.name = 'radioitems'


class IRegFormDateInputFieldFossil(IRegFormInputFieldBaseFossil):

    def getId(self):
        """
        Field Caption
        """

    def getDateFormat(self):
        """
        Date Format
        """

    def getDisplayFormats(self):
        """
        Different available date formats
        """


class IRegFormTelephoneInputFieldFossil(IRegFormInputFieldBaseFossil):

    def getLength(self):
        """
        Field length
        """


class IRegFormGeneralFieldFossil(IFossil):

    def getId(self):
        """
        Field id
        """

    def getCaption(self):
        """
        Field Caption
        """

    def getDescription(self):
        """
        Field description
        """

    def getLocked(self):
        """
        Field locks
        """
    getLocked.name = 'lock'

    def isMandatory(self):
        """
        Is field mandatory
        """
    isMandatory.name = 'mandatory'

    def isDisabled(self):
        """
        Is field disabled
        """
    isDisabled.name = 'disabled'

    def isBillable(self):
        """
        Is field disabled
        """
    isBillable.name = 'billable'

    def getPrice(self):
        """
        Field price
        """

    def getPlacesLimit(self):
        """
        Field places limit
        """

    def getNoPlacesLeft(self):
        """
        Number of left places
        """

    def getInput(self):
        """
        Field Caption
        """
    getInput.convert = lambda x: x.getId()

    def getValues(self):
        """
        Field Values
        """
    getValues.convert = lambda x: x['inputObj']
    getValues.result = {"MaKaC.registration.TextInput":        IRegFormTextInputFieldFossil,
                        "MaKaC.registration.TextareaInput":    IRegFormTextareaInputFieldFossil,
                        "MaKaC.registration.LabelInput":       IRegFormLabelInputFieldFossil,
                        "MaKaC.registration.NumberInput":      IRegFormNumberInputFieldFossil,
                        "MaKaC.registration.RadioGroupInput":  IRegFormRadioGroupInputFieldFossil,
                        "MaKaC.registration.CheckboxInput":    IRegFormCheckboxInputFieldFossil,
                        "MaKaC.registration.YesNoInput":       IRegFormYesNoInputFieldFossil,
                        "MaKaC.registration.CountryInput":     IRegFormCountryInputFieldFossil,
                        "MaKaC.registration.DateInput":        IRegFormDateInputFieldFossil,
                        "MaKaC.registration.TelephoneInput":   IRegFormTelephoneInputFieldFossil,
                        "MaKaC.registration.FileInput":        IRegFormFileInputFieldFossil
                        }


###########################
# Section type fossil
###########################
class IRegFormSectionBaseFossil(IFossil):

    def getId(self):
        """
        Section id
        """

    def getTitle(self):
        """
        Section title
        """

    def isEnabled(self):
        """
        Section is enabled
        """
    isEnabled.name = 'enabled'


class IRegFormGeneralSectionFossil(IRegFormSectionBaseFossil):

    def isRequired(self):
        """
        Section is required
        """
    isRequired.name = 'required'

    def getDescription(self):
        """
        Section description
        """

    def getSortedFields(self):
        """
        Returns the sorted field in the section
        """
    getSortedFields.name = 'items'
    getSortedFields.result = IRegFormGeneralFieldFossil


class IRegFormFurtherInformationSectionFossil(IRegFormSectionBaseFossil):

    def getContent(self):
        """
        Section content
        """

    def getItems(self):
        """
        Section items list
        """


class IRegFormAccommodationSectionFossil(IRegFormSectionBaseFossil):

    def getDescription(self):
        """
        Section description
        """

    def getArrivalOffsetDates(self):
        """
        Arrival offset dates
        """
    getArrivalOffsetDates.convert = lambda x: [-el for el in x]

    def getDepartureOffsetDates(self):
        """
        Departure offset dates
        """

    def getArrivalDates(self):
        """
        Get arrival dates
        """
    getArrivalDates.convert = lambda x: dict((format_date(date, "dd-MM-yyyy"), format_date(date, "dd-MMMM-yyyy"))
                                             for date in x)

    def getDepartureDates(self):
        """
        Get departure dates
        """
    getDepartureDates.convert = lambda x: dict((format_date(date, "dd-MM-yyyy"), format_date(date, "dd-MMMM-yyyy"))
                                               for date in x)

    def getAccommodationTypesList(self):
        """
        Accommodation types list
        """
    getAccommodationTypesList.name = 'items'
    getAccommodationTypesList.result = IRegFormAccommodationTypeItemFossil


class IRegFormReasonParticipationSectionFossil(IRegFormSectionBaseFossil):

    def getDescription(self):
        """
        Section description
        """

    def getItems(self):
        """
        Section items
        """


class IRegFormSessionSectionFossil(IRegFormSectionBaseFossil):

    def getDescription(self):
        """
        Section description
        """

    def getType(self):
        """
        Type of menu
        """

    def getSessionList(self, doSort=True):
        """
        Session list
        """
    getSessionList.name = 'items'
    getSessionList.result = IRegFormRegistrationSessionItemFossil


class IRegFormSocialEventSectionFossil(IRegFormSectionBaseFossil):

    def getDescription(self):
        """
        Section description
        """

    def getIntroSentence(self):
        """
        Intro sentence
        """

    def getMandatory(self):
        """
        Mandatory to select at least one event
        """

    def getSelectionTypeId(self):
        """
        Selection type
        """
    getSelectionTypeId.name = 'selectionType'

    def getSocialEventList(self, sort=True):
        """
        Social event List
        """
    getSocialEventList.name = 'items'
    getSocialEventList.result = IRegFormSocialEventItemFossil


#############################################
# Registration form registrant data fossil
#############################################
class IRegFormMiscellaneousInfoSimpleItemFossil(IFossil):

    def getId(self):
        """
        Get item ID
        """

    def getHTMLName(self):
        """
        Get HTML Name
        """
    getHTMLName.name = 'HTMLName'

    def getValue(self):
        """
        Get value
        """
    getValue.convert = lambda x: {
        'name': x.getFileName(), 'path': str(UHFileAccess.getURL(x))
    } if (x.__class__.__name__ == 'LocalFile') else x

    def getCurrency(self):
        """
        Get currency
        """

    def getQuantity(self):
        """
        Get quantity
        """

    def getPrice(self):
        """
        Get price
        """

    def getCaption(self):
        """
        Get price
        """
    getCaption.produce = lambda item: item.getGeneralField().getCaption()


class IRegFormSocialEventFossil(IFossil):

    def getId(self):
        """
        Get id
        """

    def getCaption(self):
        """
        Get caption
        """

    def getNoPlaces(self):
        """
        get number of places
        """

    def getCurrency(self):
        """
        get currency
        """

    def getPrice(self):
        """
        get currency
        """


class IRegFormSessionsFormFossil(IFossil):

    def getId(self):
        """
        Get id
        """


class IRegFormAccommodationFossil(IFossil):

    def getArrivalDate(self):
        """
        Get arrival dates
        """
    getArrivalDate.convert = lambda x: format_date(x, "dd-MM-yyyy")

    def getDepartureDate(self):
        """
        Get departure dates
        """
    getDepartureDate.convert = lambda x: format_date(x, "dd-MM-yyyy")

    def getAccommodationType(self):
        """
        Get accommodation type
        """
    getAccommodationType.result = IRegFormAccommodationTypeItemFossil

    def getPrice(self):
        """
        Accommodation price
        """

    def isBillable(self):
        """
        Accommodation billability
        """
    isBillable.name = 'billable'


class IRegFormMiscellaneousInfoGroupFossil(IFossil):

    def getId(self):
        """
        Get section ID
        """

    def getTitle(self):
        """
        Get section Title
        """

    def getResponseItems(self):
        """
        Get response items
        """
    getResponseItems.result = IRegFormMiscellaneousInfoSimpleItemFossil


class IRegFormMiscellaneousInfoGroupFullFossil(IRegFormMiscellaneousInfoGroupFossil):

    def getResponseItems(self):
        """
        Get response items
        """
    getResponseItems.produce = lambda x: x.getResponseItems().values()
    getResponseItems.result = IRegFormMiscellaneousInfoSimpleItemFossil


class IRegFormRegistrantBasicFossil(IFossil):
    def getId(self):
        """
        Registrarant id
        """
    getId.name = "registrant_id"

    def getFullName(self):
        """
        Registrarant fullname
        """
    getFullName.name = "full_name"
    getFullName.produce = lambda x: x.getFullName(title=True, firstNameFirst=True)

    def getAdjustedRegistrationDate(self):
        """
        If the user payed
        """
    getAdjustedRegistrationDate.name = "registration_date"
    getAdjustedRegistrationDate.produce = lambda x: format_datetime(x.getAdjustedRegistrationDate(), format="short")

    def getPayed(self):
        """
        If the user payed
        """
    getPayed.name = "paid"
    getPayed.produce = lambda x: x.getPayed() if x.getConference().getModPay().isActivated() else None

    def getTotal(self):
        """
        Total amount payed
        """
    getTotal.name = "amount_paid"
    getTotal.produce = lambda x: x.getTotal() if x.getConference().getModPay().isActivated() else None

    def isCheckedIn(self):
        """
        Registrarant fullname
        """
    isCheckedIn.name = "checked_in"

    def getAdjustedCheckInDate(self):
        """
        If the user payed
        """
    getAdjustedCheckInDate.name = "checkin_date"
    getAdjustedCheckInDate.produce = lambda x: format_datetime(x.getAdjustedCheckInDate(), format="short") if x.isCheckedIn() else None


class IRegFormRegistrantFossil(IRegFormRegistrantBasicFossil):

    def getAccommodation(self):
        """
        Get Accommodation
        """
    getAccommodation.result = IRegFormAccommodationFossil

    def getReasonParticipation(self):
        """
        Get Reason Participation
        """

    def getSocialEvents(self):
        """
        Get the social events
        """
    getSocialEvents.result = IRegFormSocialEventFossil

    def getSessionList(self):
        """
        Get session list
        """
    getSessionList.result = IRegFormSessionsFormFossil

    def getMiscellaneousGroupList(self):
        """
        Get Miscellaneous group list
        """
    getMiscellaneousGroupList.result = IRegFormMiscellaneousInfoGroupFossil


class IRegFormRegistrantFullFossil(IRegFormRegistrantFossil):

    def getMiscellaneousGroupList(self):
        """
        Get Miscellaneous group list
        """
    getMiscellaneousGroupList.result = IRegFormMiscellaneousInfoGroupFullFossil
