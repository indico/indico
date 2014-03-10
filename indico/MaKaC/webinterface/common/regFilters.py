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

from datetime import datetime
import MaKaC.common.filters as filters
from MaKaC.webinterface.common.countries import CountryHolder

# -------------- FILTERING ------------------
class AccommFilterField( filters.FilterField ):
    """Contains the filtering criteria for the track of a contribution.

        Inherits from: AbstractFilterField

        Attributes:
            _values -- (list) List of track identifiers;
            _showNoValue -- (bool) Tells whether an contribution satisfies the
                filter if it hasn't belonged to any track.
    """

    _id = "accomm"

    def satisfies( self, reg ):
        """
        """
        accomTypesList = reg.getRegistrationForm().getAccommodationForm().getAccommodationTypesList()
        if len(accomTypesList) != len(self._values):
            if reg.getAccommodation().getAccommodationType() is None:
                return self._showNoValue
            if reg.getAccommodation().getAccommodationType() not in accomTypesList:
                return self._showNoValue
            return reg.getAccommodation().getAccommodationType().getId() in self._values
        else:
            return True


class SessionFilterField( filters.FilterField ):
    """
    """
    _id = "session"

    def satisfies( self, reg ):
        """
        """
        if len(reg.getRegistrationForm().getSessionsForm().getSessions().values()) != len(self._values):
            if reg.getSessionList():
                for sess in reg.getSessionList():
                    if sess.getId() in self._values:
                        return True
                    elif sess.getRegSession() not in reg.getRegistrationForm().getSessionsForm().getSessionList():
                        return self._showNoValue
            else:
                return self._showNoValue
            return False
        else:
            return True

class SessionFirstPriorityFilterField( filters.FilterField ):
    """
    """
    _id = "sessionfirstpriority"

    def satisfies( self, reg ):

        """
        """

        if len(reg.getSessionList()) > 0:
            sess=reg.getSessionList()[0]
            if sess.getId() in self._values:
                return True
            elif sess not in reg.getRegistrationForm().getSessionsForm().getSessionList():
                return self._showNoValue
        else:
            return self._showNoValue
        return False


class EventFilterField(filters.FilterField):
    """
    """
    _id = "event"

    def satisfies(self, reg):
        """
        """
        if (reg.getRegistrationForm().getSocialEventForm().getSocialEventList()) != len(self._values):
            if reg.getSocialEvents():
                for event in reg.getSocialEvents():
                    if event.getId() in self._values:
                        return True
                    elif event.getSocialEventItem() not in reg.getRegistrationForm().getSocialEventForm().getSocialEventList():
                        return self._showNoValue
            else:
                return self._showNoValue
            return False
        return True

class StatusesFilterField(filters.FilterField):
    """
    Filter used for filtering by the statuses (if they exist).
    The statuse's values are represented following this format:
        -NameOfTheStatus + IdOfTheStatus + "-" + IdOfTheValue
        -For "-- not set --" values:
         NameOfTheStatus + IdOfTheStatus + "-NoValue"
    """
    _id = "statuses"

    def __init__(self,conf,values,showNoValue=True ):
        filters.FilterField.__init__(self, conf, values, showNoValue)
        self._confStatusSet = set([status.getCaption()+"-"+status.getId() for status in self._conf.getRegistrationForm().getStatusesList(False)])

    def satisfies(self, reg):
        """
        """
        ### If all the status values are selected, there is no need for filtering
        values = 0
        for status in self._conf.getRegistrationForm().getStatusesList(False):
            values += len(status.getStatusValues()) + 1
        if len(self._values) == values:
            return True

        statusDict = reg.getStatuses()

        if statusDict:
            for status in statusDict:
                if statusDict[status].getCaption()+"-"+statusDict[status].getId() in self._confStatusSet:
                    if statusDict[status] and statusDict[status].getStatusValue():
                        field = statusDict[status].getCaption()+statusDict[status].getId() + "-" +statusDict[status].getStatusValue().getCaption() + ""
                        if field not in self._values:
                            return False
                    else:
                        if statusDict[status].getCaption()+statusDict[status].getId()+"-NoValue" not in self._values:
                            return False
                else:
                    continue
            return True
        else:
            return True


class RegFilterCrit(filters.FilterCriteria):
    _availableFields = { \
        AccommFilterField.getId():AccommFilterField,
        SessionFilterField.getId():SessionFilterField,
        SessionFirstPriorityFilterField.getId():SessionFirstPriorityFilterField,
        EventFilterField.getId():EventFilterField,
        StatusesFilterField.getId():StatusesFilterField}

#------------- SORTING --------------------
class RegistrantSortingField(filters.SortingField):

    def getSpecialId(self):
        try:
            if self._specialId:
                pass
        except AttributeError, e:
            return self._id
        return self._specialId

class IdSF(RegistrantSortingField):
    _id="Id"

    def compare( self, r1, r2 ):
        """
        """
        res1 = int(r1.getId())
        res2 = int(r2.getId())
        return cmp( res1, res2 )

class NameSF(RegistrantSortingField):
    _id="Name"

    def compare( self, r1, r2 ):
        return cmp( r1.getFamilyName().upper() + r1.getFirstName(), r2.getFamilyName().upper() + r2.getFirstName() )

class PositionSF( RegistrantSortingField ):
    _id = "Position"

    def compare( self, r1, r2 ):
        return cmp( r1.getPosition().lower(), r2.getPosition().lower() )

class CountrySF( RegistrantSortingField ):
    _id = "Country"

    def compare( self, r1, r2 ):
        return cmp( CountryHolder().getCountryById(r1.getCountry()).lower(), CountryHolder().getCountryById(r2.getCountry()).lower() )

class CitySF( RegistrantSortingField ):
    _id = "City"

    def compare( self, r1, r2 ):
        return cmp( r1.getCity().lower(), r2.getCity().lower() )

class PhoneSF( RegistrantSortingField ):
    _id = "Phone"

    def compare( self, r1, r2 ):
        return cmp( r1.getPhone().lower(), r2.getPhone().lower() )

class InstitutionSF( RegistrantSortingField ):
    _id = "Institution"

    def compare( self, r1, r2 ):
        return cmp( r1.getInstitution().lower(), r2.getInstitution().lower() )

class EmailSF( RegistrantSortingField ):
    _id = "Email"

    def compare( self, r1, r2 ):
        return cmp( r1.getEmail().lower(), r2.getEmail().lower() )

class SessionsSF( RegistrantSortingField ):
    _id = "Sessions"

    def compare( self, r1, r2 ):
        ses1 = r1.getSessionList()
        ses2 = r2.getSessionList()
        i = 0
        while(i<min(len(ses1), len(ses2))):
            v = cmp( ses1[i].getTitle().lower(), ses2[i].getTitle().lower() )
            if v != 0:
                return v
            i += 1
        if len(ses1)>len(ses2):
            return 1
        elif len(ses1)<len(ses2):
            return -1
        else:
            return 0

class AccommodationSF( RegistrantSortingField ):
    _id = "Accommodation"

    def compare( self, r1, r2 ):
        if r2.getAccommodation() is None and r1.getAccommodation() is not None:
            return 1
        elif r1.getAccommodation() is None and r2.getAccommodation() is not None:
            return -1
        elif r1.getAccommodation() is None and r2.getAccommodation() is None:
            return 0
        elif r2.getAccommodation().getAccommodationType() is None and r1.getAccommodation().getAccommodationType() is not None:
            return 1
        elif r1.getAccommodation().getAccommodationType() is None and r2.getAccommodation().getAccommodationType() is not None:
            return -1
        elif r1.getAccommodation().getAccommodationType() is None and r2.getAccommodation().getAccommodationType() is None:
            return 0
        else:
            return cmp(r1.getAccommodation().getAccommodationType().getCaption(), r2.getAccommodation().getAccommodationType().getCaption())

class ArrivalDateSF( RegistrantSortingField ):
    _id = "ArrivalDate"

    def compare( self, r1, r2 ):
        if r2.getAccommodation() is None and r1.getAccommodation() is not None:
            return 1
        elif r1.getAccommodation() is None and r2.getAccommodation() is not None:
            return -1
        elif r1.getAccommodation() is None and r2.getAccommodation() is None:
            return 0
        elif r2.getAccommodation().getArrivalDate() is None and r1.getAccommodation().getArrivalDate() is not None:
            return 1
        elif r1.getAccommodation().getArrivalDate() is None and r2.getAccommodation().getArrivalDate() is not None:
            return -1
        elif r1.getAccommodation().getArrivalDate() is None and r2.getAccommodation().getArrivalDate() is None:
            return 0
        else:
            return cmp(r1.getAccommodation().getArrivalDate(), r2.getAccommodation().getArrivalDate())

class DepartureDateSF( RegistrantSortingField ):
    _id = "DepartureDate"

    def compare( self, r1, r2 ):
        if r2.getAccommodation() is None and r1.getAccommodation() is not None:
            return 1
        elif r1.getAccommodation() is None and r2.getAccommodation() is not None:
            return -1
        elif r1.getAccommodation() is None and r2.getAccommodation() is None:
            return 0
        elif r2.getAccommodation().getDepartureDate() is None and r1.getAccommodation().getDepartureDate() is not None:
            return 1
        elif r1.getAccommodation().getDepartureDate() is None and r2.getAccommodation().getDepartureDate() is not None:
            return -1
        elif r1.getAccommodation().getDepartureDate() is None and r2.getAccommodation().getDepartureDate() is None:
            return 0
        else:
            return cmp(r1.getAccommodation().getDepartureDate(), r2.getAccommodation().getDepartureDate())

class SocialEventsSF( RegistrantSortingField ):
    _id = "SocialEvents"

    def compare( self, r1, r2 ):
        ses1 = r1.getSocialEvents()
        ses2 = r2.getSocialEvents()
        i = 0
        while(i<min(len(ses1), len(ses2))):
            v = cmp( ses1[i].getCaption().lower(), ses2[i].getCaption().lower() )
            if v != 0:
                return v
            i += 1
        if len(ses1)>len(ses2):
            return 1
        elif len(ses1)<len(ses2):
            return -1
        else:
            return 0

class ReasonParticipationSF( RegistrantSortingField ):
    _id = "ReasonParticipation"

    def compare( self, r1, r2 ):
        rp1=r1.getReasonParticipation() or ""
        rp2=r2.getReasonParticipation() or ""
        return cmp( rp1.lower(), rp2.lower() )

class AddressSF( RegistrantSortingField ):
    _id = "Address"

    def compare( self, r1, r2 ):
        a1=r1.getAddress() or ""
        a2=r2.getAddress() or ""
        return cmp( a.lower().strip(), a.lower().strip() )

class RegistrationDateSF( RegistrantSortingField ):
    _id = "RegistrationDate"

    def compare( self, r1, r2 ):
        rd1=r1.getRegistrationDate() or datetime(1995, 1, 1)
        rd2=r2.getRegistrationDate() or datetime(1995, 1, 1)
        return cmp( rd1, rd2 )


class GeneralFieldSF( RegistrantSortingField ):
    _id = "groupID-fieldId"

    def compare( self, r1, r2 ):
        if self.getSpecialId() != self._id:
            ids=self.getSpecialId().split("-")
            if len(ids)==2:
                group1=r1.getMiscellaneousGroupById(ids[0])
                group2=r2.getMiscellaneousGroupById(ids[0])
                v1=""
                if group1 is not None:
                    i1=group1.getResponseItemById(ids[1])
                    if i1 is not None:
                        v1=i1.getValue()
                v2=""
                if group2 is not None:
                    i2=group2.getResponseItemById(ids[1])
                    if i2 is not None:
                        v2=i2.getValue()
                return cmp(str(v1).lower().strip(), str(v2).lower().strip())
        return 0


class StatusesSF( RegistrantSortingField ):
    _id = "s-statusId"


    def compare( self, r1, r2 ):
        if self.getSpecialId() != self._id:
            ids=self.getSpecialId().split("-")
            if len(ids)==2:
                s1=r1.getStatusById(ids[1])
                s2=r2.getStatusById(ids[1])
                if s1.getStatusValue() is None and s2.getStatusValue() is None:
                    return 0
                if s1.getStatusValue() is None:
                    return -1
                if s2.getStatusValue() is None:
                    return 1
                return cmp( s1.getStatusValue().getCaption().lower().strip(), s2.getStatusValue().getCaption().lower().strip() )
        return 0

class IsPayedSF(RegistrantSortingField):
    _id="isPayed"

    def compare( self, r1, r2 ):
        """
        """
        return cmp( r1.isPayedText(), r2.isPayedText() )

class IdPayment(RegistrantSortingField):
    _id="idpayment"

    def compare( self, r1, r2 ):
        """
        """
        return cmp( r1.getIdPay(), r2.getIdPay() )


class IsCheckedInSF(RegistrantSortingField):
    _id="checkedIn"

    def compare(self, r1, r2):
        """
        """
        return cmp(r1.isCheckedIn(), r2.isCheckedIn())


class CheckInDateSF(RegistrantSortingField):
    _id="checkInDate"

    def compare(self, r1, r2):
        """
        """
        if r2.getCheckInDate() is None and r1.getCheckInDate() is not None:
            return 1
        elif r1.getCheckInDate() is None and r2.getCheckInDate() is not None:
            return -1
        elif r1.getCheckInDate() is None and r2.getCheckInDate() is None:
            return 0
        else:
            return cmp(r1.getCheckInDate(), r2.getCheckInDate())


class SortingCriteria( filters.SortingCriteria ):
    """
    """
    _availableFields = {IdSF.getId():IdSF, \
                        NameSF.getId():NameSF, \
                        PositionSF.getId(): PositionSF, \
                        CitySF.getId():CitySF, \
                        PhoneSF.getId():PhoneSF, \
                        InstitutionSF.getId():InstitutionSF, \
                        EmailSF.getId():EmailSF, \
                        SessionsSF.getId():SessionsSF, \
                        AccommodationSF.getId():AccommodationSF, \
                        ArrivalDateSF.getId():ArrivalDateSF, \
                        DepartureDateSF.getId():DepartureDateSF, \
                        SocialEventsSF.getId():SocialEventsSF, \
                        ReasonParticipationSF.getId():ReasonParticipationSF, \
                        GeneralFieldSF.getId():GeneralFieldSF, \
                        StatusesSF.getId():StatusesSF, \
                        RegistrationDateSF.getId():RegistrationDateSF, \
                        CountrySF.getId():CountrySF, \
                        IsPayedSF.getId():IsPayedSF, \
                        IdPayment.getId():IdPayment, \
                        IsCheckedInSF.getId():IsCheckedInSF, \
                        CheckInDateSF.getId():CheckInDateSF}


    def __init__( self, crit = []):
        self._sortingField = None
        if crit:
            fieldKlass = self._availableFields.get( crit[0], None )
            if fieldKlass:
                self._sortingField = self._createField( fieldKlass )
            elif crit[0].startswith("s-"):
                self._sortingField = self._createField( StatusesSF )
                self._sortingField._specialId=crit[0]
            else:
                self._sortingField = self._createField( GeneralFieldSF )
                self._sortingField._specialId=crit[0]


