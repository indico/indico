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

import MaKaC.common.filters as filters
import MaKaC.review as review


class ContribTypeSortingField(filters.SortingField):
    """Allows to determine the abstract order regarding its contribution type.
    """
    _id = "type"

    def compare( self, a1, a2 ):
        """
        """
        if a1.getContribType() == None and a2.getContribType() == None:
            return 0
        elif a1.getContribType() == None:
            return -1
        elif a2.getContribType() == None:
            return +1
        return cmp( a1.getContribType().getName(), a2.getContribType().getName() )


class SubmissionDateSortingField(filters.SortingField):
    """
    """
    _id = "date"

    def compare( self, a1, a2 ):
        """
        """
        return cmp( a2.getSubmissionDate(), a1.getSubmissionDate() )

class ModificationDateSortingField(filters.SortingField):
    """
    """
    _id = "modifDate"

    def compare( self, a1, a2 ):
        """
        """
        return cmp( a2.getModificationDate(), a1.getModificationDate() )

class TrackFilterField(filters.FilterField):
    """Contains the filtering criteria for the track of an abstract.

        Implements the logic to determine whether abstracts have been submitted
        for a certain list of tracks. Objects of this class will keep a list
        of track identifiers; then an abstract will satisfy the filter if any
        of the tracks ids for which it is suggested is in the filter list of
        values.

        Inherits from: AbstractFilterField

        Attributes:
            _values -- (list) List of track identifiers; if an identifier of
                any track an abstract is suggested for is included in this
                list, the abstract will satisfy the filter field.
            _showNoValue -- (bool) Tells whether an abstract satisfies the
                filter if it hasn't been suggested for any track.
            _onlyMultiple -- (bool) In case of having to filter by track,
                determines whether to accept only abstracts being proposed
                for more than one track.
    """
    _id = "track"
    _onlyMultiple = False

    def onlyMultiple( self ):
        return self._onlyMultiple

    def setOnlyMultiple( self, val ):
        self._onlyMultiple = val

    def satisfies( self, abstract ):
        """
        """
        if self.onlyMultiple() and len(abstract.getTrackList())<2:
            return False
        if len(self._conf.getTrackList()) == len(self._values):
            return True
        else:
            #ToDo: to be optimised by using OOSet intersections or indexes
            hasTracks = False
            for track in abstract.getTrackList():
                hasTracks = True
                if track.getId() in self._values:
                    return True
            if not hasTracks:
                return self._showNoValue
            return False

    def needsToBeApplied(self):
        for t in self._conf.getTrackList():
            if t.getId() not in self._values:
                return True
        return not self._showNoValue


class ContribTypeFilterField(filters.FilterField):
    """Contains the filtering criteria for the contribution type of an abstract.

        Implements the logic to determine whether abstracts have been proposed
        to become a certain set of types. Objects of this class will keep a
        list of contribution types; then an abstract will satisfy the filter if
        its suggested contribution type is in the list of values.

        Inherits from: AbstractFilterField

        Attributes:
            _values -- (list) List of contribution types; if the contribution
                type of an abstract is included in this list, the abstract will
                satisfy the filter field.
            _showNoValue -- (bool) Tells whether an abstract satisfies the
                filter if any type hasn't been proposed.
    """
    _id = "type"

    def satisfies( self, abstract ):
        if len(self._conf.getContribTypeList()) == len(self._values):
            return True
        elif not abstract.getContribType():
            return self._showNoValue
        else:
            return abstract.getContribType().getId() in self._values

    def needsToBeApplied(self):
        for ct in self._conf.getContribTypeList():
            if ct.getId() not in self._values:
                return True
        return not self._showNoValue


class AccContribTypeFilterField(filters.FilterField):
    """
    """
    _id = "acc_type"

    def satisfies(self,abstract):
        if len(self._conf.getContribTypeList()) == len(self._values):
            return True
        else:
            s=abstract.getCurrentStatus()
            if s.__class__ in [review.AbstractStatusAccepted,\
                                review.AbstractStatusProposedToAccept]:
                if s.getType() is None or s.getType()=="":
                    return self._showNoValue
                return s.getType().getId() in self._values
            else:
                return self._showNoValue

    def needsToBeApplied(self):
        for ct in self._conf.getContribTypeList():
            if ct.getId() not in self._values:
                return True
        return not self._showNoValue


class AccTrackFilterField(filters.FilterField):
    """
    """
    _id = "acc_track"

    def satisfies( self, abstract ):
        """
        """
        s=abstract.getCurrentStatus()
        if s.__class__ in [review.AbstractStatusAccepted,\
                            review.AbstractStatusProposedToAccept]:
            if s.getTrack() is None:
                return self._showNoValue
            elif len(self._conf.getTrackList()) == len(self._values):
                return True
            else:
                return s.getTrack().getId() in self._values
        else:
            return self._showNoValue

    def needsToBeApplied(self):
        for t in self._conf.getTrackList():
            if t.getId() not in self._values:
                return True
        return not self._showNoValue


class CommentFilterField(filters.FilterField):

    _id = "comment"

    def satisfies( self, abstract ):
        """
        """
        if abstract.getComments().strip() == "":
            return False
        return True
