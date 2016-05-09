# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import MaKaC.common.filters as filters
from indico.util.string import natural_sort_key


class TypeFilterField( filters.FilterField ):
    """
    """
    _id = "type"

    def satisfies( self, contribution ):
        """
        """
        if self._conf.as_event.contribution_types.count() == len(self._values) and contribution.type:
            return True
        elif contribution.type is None:
            return self._showNoValue
        else:
            return str(contribution.type.id) in self._values


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
        if len(self._conf.getTrackList()) == len(self._values) and contribution.track:
            return True
        elif contribution.track:
            if contribution.track.getId() in self._values:
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
        if len(self._conf.sessions) == len(self._values) and contribution.session:
            return True
        elif contribution.session:
            if str(contribution.session.id) in self._values:
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
        rm = self._conf.getReviewManager(contribution)
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
        rm = self._conf.getReviewManager(contribution)
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
        rm = self._conf.getReviewManager(contribution)
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
        rm = self._conf.getReviewManager(contribution)
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
        review = self._conf.getReviewManager(contribution).getLastReview()
        if self._values[0] and review.isAuthorSubmitted():
            return True
        elif review.isAuthorSubmitted():
            return False
        else:
            return self._showNoValue


class NumberSF(filters.SortingField):
    _id = 'number'

    def compare(self, c1, c2):
        return cmp(c1.friendly_id, c2.friendly_id)


class SortingCriteria(filters.SortingCriteria):
    _availableFields = {NumberSF.getId(): NumberSF}
