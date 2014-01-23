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

class SortingField:
    """Base class containing the sorting logic for a single abstract field.

        This class specifies the common interface that the different sorting
        fields must comply. It also implements basic logic to set up sorting.
        Classes inheriting from this one will implement the necessary checking
        against the abstract propertied to stablish an order for an abstract
        repect to others.

        Attributes:
            _id -- (class) (string) unique id (among other sorting fields) for
                the field.
    """
    _id = ""

    def __init__( self ):
        pass

    def getId( cls ):
        return cls._id
    getId = classmethod( getId )

    def compare( self, a1, a2 ):
        """Performs the comparison between two abstracts for a field.
        """
        return 0


class SortingCriteria:
    """Specifies a criteria by which a list of abstracts must be sorted.

        This class contains the criteria which has to be applied to a list of
        abstracts in order to order it.
        This class doesn't perform the sorting, it only carries the sorting
        specifications allowing to modify or expand it.
        The criteria is specified in the form of "fields" which contain the
        logic needed so an abstract can be compared with others in order to
        stablish a sorting.

        Attributes:
            _availableFields -- (dict) Contains those fields sorting classes
                which can be used with this criteria indexed by field ids.
            _sortingField -- (SortingField) Current sorting field.
    """
    _availableFields = {}


    def __init__( self, crit = []):
        self._sortingField = None
        if crit:
            fieldKlass = self._availableFields.get( crit[0], None )
            if fieldKlass:
                self._sortingField = self._createField( fieldKlass )

    def _createField( self, fieldKlass ):
        """
        """
        return fieldKlass()

    def getFields( self ):
        return [self._sortingField]

    def getField( self ):
        """Returns the current sorting field.
        """
        return self._sortingField

    def compare( self, a1, a2 ):
        """Performs the comparison between two abstracts.
        """
        return self._sortingField.compare( a1, a2 )


class FilterField:
    """Base class containing the filter criteria for a single field.

        This class specifies the common interface that the different filter
        fields must comply. It also implements basic logic to keep filtering
        values.
        Classes inheriting from this one will implement the necessary checking
        against the filtering values to determine whether an abstract satisfies
        the filter for the filter field they represent.

        Attributes:
            _values -- (list) List of values of the filter. The values types
                and meaning will depend on each field implementation.
            _showNoValue -- (bool) Specifies if an abstract satifies the filter
                when the abstract has no value for the required field.
            _id -- (class) (string) unique id (among other filter fields) for
                the field.
    """
    _id = ""

    def __init__(self,conf,values,showNoValue=True ):
        """Class constructor.
        """
        self._conf=conf
        self._values = values
        if not isinstance(self._values, list):
            self._values = [self._values]
        self._showNoValue = showNoValue

    def getId( cls ):
        return cls._id
    getId = classmethod( getId )

    def setShowNoValue( self, showIt=True ):
        self._showNoValue = showIt

    def getShowNoValue( self ):
        return self._showNoValue

    def getValues( self ):
        return self._values

    def satisfies( self, abstract ):
        """Tells whether an abstract verifies the current field.

            This method must be defined by each field specialisation so the
            checking logic is defined.

            Return value: True if the abstract verifies, False in any other
                case.
        """
        return False

    def needsToBeApplied(self):
        return True


class FilterCriteria:
    """Specifies a criteria which allows to filter a list of abstracts.

        This class contains the different criteria which has to be applied to a
        list of abstracts in order to filter it so another list of abtracts
        satisfying the current criteria can be obtained. This class doesn't
        perform the filtering, it only contains the filtering criteria allowing
        to modify or expand it.
        The criteria is specified in the form of "fields" which contain the
        logic and values needed so an abstract can be checked in order to
        determine whether it satifies or not the criteria specified for that
        field (represented by specialisations of the AbstractFilterField class).

        Attributes:
            _availableFields -- (dict) Contains those fields filters classes
                which can be used with this criteria indexed by field names.
            _fields -- (dict) Current filter criteria fields indexed by field
                names.
    """
    _availableFields = { }

    def __init__(self,conf,criteria={}):
        """Class constructor.

            Initialises the object and builds up the different FilterFields
            according to the specified criteria.

            Arguments:
                criteria -- (dict) Specifies the criteria to be used. Is a short
                    way of configuring the filter criteria so the client can
                    specify filtering values without bothering about the
                    FilterField classes which need to be specified.
                    Keys of this dictionary must be field names (which must
                    match any of the keys of the _availableFields attribute)
                    and the values must be a list of the values the field must
                    satisfy in order to make it pass the filter.
        """

        self._conf=conf
        self._fields = {}
        #Match the criteria keys with the allowed fields and construct the
        #   field classes according to the _availableFields attribute
        for fieldName in criteria.keys():
            cfieldName = fieldName.strip().lower()
            if self._availableFields.has_key( cfieldName ):
                fieldKlass = self._availableFields[ cfieldName ]
                fieldValues = criteria[ fieldName ]
                self._fields[ cfieldName ] = self._createField( fieldKlass, fieldValues )

    def _createField( self, klass, values ):
        """Contains the creation of filter fields.

            Thanks to this method, subclasses can customise the creation of
            the filter fields without changing the initialisation.
        """
        return klass(self._conf,values)

    def getField( self, fieldId ):
        """Returns the FilterField matching the specified id.

            Return value: AbstractFilterField for the specified field
                identifier or None if no field matched the id.

            Arguments:
                fieldId -- (string) field identifier. Possible values: track,
                    type, status
        """
        return self._fields.get( fieldId.strip().lower(), None )

    def satisfies( self, abstract ):
        """Tells whether an abstract satisfies the current criteria.

            Abstract is checked against the different fields which compose
            the ciriteria and if it satifies each of them it returns True.

            Return value: True if the abstract satisfies the current criteria,
                False in any other case.

            Arguments:
                abstract -- (MaKaC.review.Abstract) abstract which has to be
                    checked if it satisfies the current criteria.
        """
        for field in self._fields.values():
            if not field.satisfies( abstract ):
                return False
        return True

    def optimise(self):
        newFields={}
        for kf in self._fields.keys():
            field=self._fields[kf]
            if field.needsToBeApplied():
                newFields[kf]=field
        self._fields=newFields


class SimpleFilter:
    """Performs filtering and sorting over a list of abstracts.
    """

    def __init__(self,filterCrit,sortingCrit):
        """
        """
        self._filter = filterCrit
        self._sorting = sortingCrit

    def apply(self,targetList):
        """
        """
        result = []
        if self._filter:
            result = [item for item in targetList if self._filter.satisfies( item )]
        else:
            result = targetList
        if self._sorting:
            if self._sorting.getField():
                result.sort( self._sorting.compare )
        return result

