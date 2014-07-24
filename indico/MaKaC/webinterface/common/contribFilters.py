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
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from indico.util.string import natural_sort_key


class TypeFilterField( filters.FilterField ):
    """
    """
    _id = "type"

    def satisfies( self, contribution ):
        """
        """
        if len(self._conf.getContribTypeList()) == len(self._values) and contribution.getType():
            return True
        elif contribution.getType() is None:
            return self._showNoValue
        else:
            return contribution.getType().getId() in self._values


class TrackFilterField( filters.FilterField ):
    """Contains the filtering criteria for the track of a contribution.

        Inherits from: AbstractFilterField

        Attributes:
            _values -- (list) List of track identifiers;
            _showNoValue -- (bool) Tells whether an contribution satisfies the
                filter if it hasn't belonged to any track.
    """
    _id = "track"

    def satisfies( self, contribution ):
        """
        """
        if len(self._conf.getTrackList()) == len(self._values) and contribution.getTrack():
            return True
        elif contribution.getTrack():
            if contribution.getTrack().getId() in self._values:
                return True
        else:
            return self._showNoValue
        return False


class SessionFilterField( filters.FilterField ):
    """Contains the filtering criteria for the session which a contribution belongs.

        Inherits from: AbstractFilterField

        Attributes:
            _values -- (list) List of session identifiers;
            _showNoValue -- (bool) Tells whether an contribution satisfies the
                filter if it hasn't belonged to any session.
    """
    _id = "session"

    def satisfies( self, contribution ):
        """
        """
        if len(self._conf.getSessionList()) == len(self._values) and contribution.getSession():
            return True
        elif contribution.getSession():
            if contribution.getSession().getId() in self._values:
                return True
        else:
            return self._showNoValue
        return False

class PosterFilterField (filters.FilterField):
    """ Contains the filtering criteria for the contribution being a poster or not.
        A contribution is considered a poster contribution if it belongs to a poster session.

        Inherits from: AbstractFilterField

        Attributes:
            _values -- (bool) Tells if the contribution should be a poster or not.
            _showNoValue -- (bool) Tells whether an contribution satisfies the
                filter if it doesn't satisfy the _values criterion. So, if True, all
                contribution will satisfy the criterion.
    """

    _id = "poster"
    def satisfies( self, contribution ):
        if self._showNoValue:
            return True
        elif len(self._values) > 0 and self._values[0]: #values[0] is True or False. Contribution has to be a poster
            return contribution.getSession() and contribution.getSession().getScheduleType() == "poster"
        else: #contribution must not be a poster
            return not contribution.getSession() or contribution.getSession().getScheduleType() != "poster"


class StatusFilterField(filters.FilterField):
    """
    """
    _id = "status"

    def satisfies(self,contribution):
        """
        """
        if len(ContribStatusList().getList()) == len(self._values):
            return True
        stKlass=contribution.getCurrentStatus().__class__
        return ContribStatusList().getId(stKlass) in self._values


class AuthorFilterField( filters.FilterField ):
    """
    """
    _id = "author"

    def satisfies(self,contribution):
        """
        """
        queryText = ""
        if len(self._values) > 0:
            queryText = str(self._values[0]) #The first value is the query text
        query=queryText.strip().lower()
        if query=="":
            return True
        for auth in contribution.getPrimaryAuthorList():
            key="%s %s"%(auth.getFamilyName(),auth.getFirstName())
            if key.lower().find(query)!=-1:
                return True
        return False


class MaterialFilterField(filters.FilterField):
    """
    """
    _id = "material"

    def satisfies(self,contribution):
        """
        """
        #all options selected
        if len(self._values) == 4:
            return True
        from MaKaC.webinterface.materialFactories import PaperFactory
        paper=contribution.getPaper()
        if (PaperFactory().getId() in self._values) and paper is not None:
            return True
        from MaKaC.webinterface.materialFactories import SlidesFactory
        slides=contribution.getSlides()
        if (SlidesFactory().getId() in self._values) and slides is not None:
            return True
        if ("--other--" in self._values) and \
                len(contribution.getAllMaterialList())>0:
            return True
        if ("--none--" in self._values) and \
                len(contribution.getAllMaterialList())==0:
            return True
        return False


class RefereeFilterField( filters.FilterField ):
    """ Contains the filtering criteria for the Referee of a contribution.
        Attributes:
            _value -- (User object) a User object. Can also be the string "any",
                      and then the contribution won't be filtered by referee.
            _showNoValue -- (bool) Tells whether an contribution satisfies the
                filter if it doesn't have a Referee
    """
    _id = "referee"

    def __init__( self, conf, values, showNoValue = True ):
        filters.FilterField.__init__(self, conf, values, showNoValue)

    def satisfies( self, contribution ):
        rm = contribution.getReviewManager()
        if rm.hasReferee():
            user = self._values[0]
            if user == "any" or rm.isReferee(user):
                return True
            else:
                return False
        else:
            return self._showNoValue

class EditorFilterField( filters.FilterField ):
    """ Contains the filtering criteria for the Editor of a contribution.
        Attributes:
            _value -- (User object) a User object. Can also be the string "any",
                      and then the contribution won't be filtered by editor.
            _showNoValue -- (bool) Tells whether an contribution satisfies the
                filter if it doesn't have an Editor
    """
    _id = "editor"

    def __init__( self, conf, values, showNoValue = True ):
        filters.FilterField.__init__(self, conf, values, showNoValue)

    def satisfies( self, contribution ):
        rm = contribution.getReviewManager()
        if rm.hasEditor():
            user = self._values[0]
            if user == "any" or rm.isEditor(user):
                return True
            else:
                return False
        else:
            return self._showNoValue

class ReviewerFilterField( filters.FilterField ):
    """ Contains the filtering criteria for a Reviewer of a contribution.
        Attributes:
            _value -- (User object) a User object. Can also be the string "any",
                      and then the contribution won't be filtered by reviewer.
            _showNoValue -- (bool) Tells whether an contribution satisfies the
                filter if it doesn't have any Reviewers
    """
    _id = "reviewer"

    def __init__( self, conf, values, showNoValue = True ):
        filters.FilterField.__init__(self, conf, values, showNoValue)

    def satisfies( self, contribution ):
        rm = contribution.getReviewManager()
        if rm.hasReviewers():
            user = self._values[0]
            if user == "any" or rm.isReviewer(user):
                return True
            else:
                return False
        else:
            return self._showNoValue


class ReviewingFilterField( filters.FilterField ):
    """ Contains the filtering criteria for a Reviewing of a contribution.
        Attributes:
            _value -- (list) List of User objects with keys "referee", "editor" and "reviewer". Can also be the string "any",
                      and then the contribution won't be filtered by reviewer.
            _showNoValue -- (bool) Tells whether an contribution satisfies the
                filter if it doesn't have reviewing team
    """
    _id = "reviewing"

    def __init__( self, conf, values, showNoValue = True ):
        filters.FilterField.__init__(self, conf, values, showNoValue)

    def satisfies( self, contribution ):
        rm = contribution.getReviewManager()
        if rm.isReferee(self._values[0].get("referee", "")):
            if (self._values[0].get("editor", "") == "any" and rm.hasEditor()) \
                or (self._values[0].get("reviewer", "") == "any" and rm.hasReviewers()):
                return True
            elif not rm.hasEditor() and not rm.hasReviewers():
                return self._showNoValue
            else:
                return False
        elif self._values[0].get("referee", "") == "any" or self._values[0].get("referee", "") == "":
            if ((self._values[0].get("referee", "") == "any") and rm.hasReferee()) \
                or (self._values[0].get("editor", "") == "any" and rm.hasEditor()) \
                or (self._values[0].get("reviewer", "") == "any" and rm.hasReviewers()):
                return True
            elif not rm.hasReferee() and not rm.hasEditor() and not rm.hasReviewers():
                return self._showNoValue
            else:
                return False


class MaterialSubmittedFilterField( filters.FilterField ):
    """ Contains the filtering criteria for a Review material of a contribution.
        Attributes:
            _value -- (User object) a User object. Can also be the string "any",
                      and then the contribution won't be filtered by reviewer.
            _showNoValue -- (bool) Tells whether an contribution satisfies the
                filter if it doesn't have any Reviewers
    """
    _id = "materialsubmitted"

    def satisfies( self, contribution ):
        review = contribution.getReviewManager().getLastReview()
        if self._values[0] and review.isAuthorSubmitted():
            return True
        elif review.isAuthorSubmitted():
            return False
        else:
            return self._showNoValue

class TitleSF(filters.SortingField):
    _id="name"

    def compare( self, c1, c2 ):
        """
        """
        if c1.getTitle() == None and c2.getTitle() == None:
            return 0
        if c1.getTitle() == None:
            return +1
        if c2.getTitle() == None:
            return -1
        return cmp(natural_sort_key(c1.getTitle().lower().strip()),
                   natural_sort_key(c2.getTitle().lower().strip()))


class NumberSF( filters.SortingField ):
    _id = "number"

    def compare( self, c1, c2 ):
        try:
            n1 = int(c1.getId())
            n2 = int(c2.getId())
            return cmp(n1,n2)
        except ValueError, e:
            return cmp( c1.getId(), c2.getId() )


class DateSF( filters.SortingField ):
    _id = "date"

    def compare( self, c1, c2 ):
        if c1.getStartDate()==None and c2.getStartDate()==None:
            return 0
        if c1.getStartDate() is None:
            return +1
        if c2.getStartDate() is None:
            return -1
        return cmp( c1.getStartDate() ,c2.getStartDate())


class ContribTypeSF( filters.SortingField ):

    _id = "type"

    def compare( self, c1, c2 ):
        """
        """
        if c1.getType() == None and c2.getType() == None:
            return 0
        elif c1.getType() == None:
            return +1
        elif c2.getType() == None:
            return -1
        return cmp(natural_sort_key(c1.getType().getName().lower().strip()),
                   natural_sort_key(c2.getType().getName().lower().strip()))


class SessionSF( filters.SortingField ):
    _id = "session"

    def compare( self, c1, c2 ):
        """
        """
        if c1.getSession() == None and c2.getSession() == None:
            return 0
        elif c1.getSession() == None:
            return +1
        elif c2.getSession() == None:
            return -1
        return cmp( c1.getSession().getCode(), c2.getSession().getCode() )

class SessionTitleSF( filters.SortingField ):
    _id = "sessionTitle"

    def compare( self, c1, c2 ):
        """
        """
        if c1.getSession() == None and c2.getSession() == None:
            return 0
        elif c1.getSession() == None:
            return +1
        elif c2.getSession() == None:
            return -1
        return cmp(natural_sort_key(c1.getSession().getTitle().lower().strip()),
                   natural_sort_key(c2.getSession().getTitle().lower().strip()))

class TrackSF(filters.SortingField):
    _id = "track"

    def compare( self, c1, c2 ):
        """
        """
        if c1.getTrack() == None and c2.getTrack() == None:
            return 0
        elif c1.getTrack() == None:
            return +1
        elif c2.getTrack() == None:
            return -1
        return cmp( c1.getTrack().getTitle(), c2.getTrack().getTitle() )


class SpeakerSF(filters.SortingField):
    _id = "speaker"

    def compare( self, c1, c2 ):
        """
        """
        if c1.getSpeakerList() == [] and c2.getSpeakerList() == []:
            return 0
        elif c1.getSpeakerList() == []:
            return +1
        elif c2.getSpeakerList() == []:
            return -1
        s1 = "%s %s"%(c1.getSpeakerList()[0].getFamilyName().lower(), c1.getSpeakerList()[0].getFirstName().lower())
        s2 = "%s %s"%(c2.getSpeakerList()[0].getFamilyName().lower(), c2.getSpeakerList()[0].getFirstName().lower())
        return cmp( s1, s2 )


class BoardNumberSF( filters.SortingField ):
    _id = "board_number"

    def compare(self,c1,c2):
        try:
            n1=int(c1.getBoardNumber())
        except ValueError, e:
            n1=c1.getBoardNumber()
        try:
            n2=int(c2.getBoardNumber())
        except ValueError, e:
            n2=c2.getBoardNumber()
        return cmp(n1,n2)


class SortingCriteria( filters.SortingCriteria ):
    """
    """
    _availableFields = {NumberSF.getId():NumberSF, \
                        DateSF.getId():DateSF, \
                        ContribTypeSF.getId():ContribTypeSF, \
                        SessionSF.getId():SessionSF, \
                        SessionTitleSF.getId():SessionTitleSF, \
                        TrackSF.getId():TrackSF, \
                        SpeakerSF.getId():SpeakerSF, \
                        BoardNumberSF.getId():BoardNumberSF, \
                        TitleSF.getId():TitleSF}



