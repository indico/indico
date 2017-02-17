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

"""
Asynchronous request handlers for conference-related data modification.
"""

from sqlalchemy.orm import joinedload

from indico.core.logger import Logger
from indico.modules.events.contributions.models.contributions import Contribution
from MaKaC import conference
from MaKaC.common import filters
from MaKaC.common.Conversion import Conversion
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.reviewing import IReviewManagerFossil
from MaKaC.services.implementation.base import ProtectedModificationService, ListModificationBase, ParameterManager
from MaKaC.services.interface.rpc.common import ServiceError
from MaKaC.webinterface.common import contribFilters
from MaKaC.webinterface.rh.reviewingModif import RCReferee, RCPaperReviewManager


def _serialize_contribution(contrib):
    return {
        'id': contrib.id,
        'friendly_id': contrib.friendly_id,
        'contributionId': contrib.id,
        'title': contrib.title,
        'location': contrib.venue_name,
        'room': contrib.room_name,
        'startDate': Conversion.datetime(contrib.start_dt),
        'endDate': Conversion.datetime(contrib.end_dt),
        'duration': Conversion.duration(contrib.duration),
        'description': contrib.description,
        'track': contrib.track.title if contrib.track else None,
        'session': contrib.session.title if contrib.session else None,
        'type': contrib.type.name if contrib.type else None,
        'address': contrib.address,
        'reviewManager': fossilize(contrib.event_new.as_legacy.getReviewManager(contrib), IReviewManagerFossil)
    }


class ConferenceBase:
    """
    Base class for conference modification
    """

    def _checkParams(self):

        try:
            self._target = self._conf = conference.ConferenceHolder().getById(self._params["conference"])
        except Exception:
            try:
                self._target = self._conf = conference.ConferenceHolder().getById(self._params["confId"])
            except Exception:
                raise ServiceError("ERR-E4", "Invalid conference id.")
            if self._target is None:
                Logger.get('rpc.conference').debug('self._target is null')
                raise Exception("Null target.")


class ConferenceModifBase(ProtectedModificationService, ConferenceBase):
    def _checkParams(self):
        ConferenceBase._checkParams(self)
        ProtectedModificationService._checkParams(self)


class ConferenceListModificationBase(ListModificationBase, ConferenceModifBase):
    pass


class ConferenceListContributionsReview(ConferenceListModificationBase):
    """ Returns a list of all contributions of a conference, ordered by id
    """

    def _checkParams(self):
        ConferenceListModificationBase._checkParams(self)
        pm = ParameterManager(self._params)
        self._selTypes = pm.extract("selTypes", pType=list, allowEmpty=True, defaultValue=[])  # ids of selected types
        self._selTracks = pm.extract("selTracks", pType=list, allowEmpty=True, defaultValue=[])  # ids of selected tracks
        self._selSessions = pm.extract("selSessions", pType=list, allowEmpty=True, defaultValue=[])  # ids of selected sessions

        self._typeShowNoValue = self._params.get("typeShowNoValue", True)
        self._trackShowNoValue = self._params.get("trackShowNoValue", True)
        self._sessionShowNoValue = self._params.get("sessionShowNoValue", True)

        self._showWithoutTeam = self._params.get("showWithoutTeam", True)
        self._showWithReferee = self._params.get("showWithReferee", False)
        self._showWithEditor = self._params.get("showWithEditor", False)
        self._showWithReviewer = self._params.get("showWithReviewer", False)

        self._showWithMaterial = self._params.get("showWithMaterial", False)
        self._showWithoutMaterial = self._params.get("showWithoutMaterial", False)

    def _checkProtection(self):
        if not RCPaperReviewManager.hasRights(self) and not RCReferee.hasRights(self):
            ProtectedModificationService._checkProtection(self)

    def _handleGet(self):
        contributions = (Contribution.find(event_new=self._conf.as_event, is_deleted=False).
                         options(joinedload('timetable_entry'), joinedload('legacy_paper_reviewing_roles')))

        filter = {}

        #filtering if the active user is a referee: he can only see his own contribs
        isOnlyReferee = RCReferee.hasRights(self) \
            and not RCPaperReviewManager.hasRights(self) \
            and not self._conf.canModify(self.getAW())

        # We want to make an 'or', not an 'and' of the reviewing assign status

        filter["reviewing"] = {}
        if isOnlyReferee:
            filter["reviewing"]["referee"] = self._getUser()
        elif self._showWithReferee:
            filter["reviewing"]["referee"] = "any"
        if self._showWithEditor:
            filter["reviewing"]["editor"] = "any"
        if self._showWithReviewer:
            filter["reviewing"]["reviewer"] = "any"

        filter["type"] = self._selTypes
        filter["track"] = self._selTracks
        filter["session"] = self._selSessions

        filter["materialsubmitted"] = self._showWithMaterial

        filterCrit = ContributionsReviewingFilterCrit(self._conf, filter)
        sortingCrit = contribFilters.SortingCriteria(["number"])

        filterCrit.getField("type").setShowNoValue(self._typeShowNoValue)
        filterCrit.getField("track").setShowNoValue(self._trackShowNoValue)
        filterCrit.getField("session").setShowNoValue(self._sessionShowNoValue)

        filterCrit.getField("reviewing").setShowNoValue(self._showWithoutTeam)
        filterCrit.getField("materialsubmitted").setShowNoValue(self._showWithoutMaterial)

        f = filters.SimpleFilter(filterCrit, sortingCrit)
        contributions = f.apply(contributions)

        return [_serialize_contribution(contrib) for contrib in contributions]


#########################
# Contribution filtering
#########################


class ContributionsReviewingFilterCrit(filters.FilterCriteria):
    _availableFields = {
        contribFilters.RefereeFilterField.getId(): contribFilters.RefereeFilterField,
        contribFilters.EditorFilterField.getId(): contribFilters.EditorFilterField,
        contribFilters.ReviewerFilterField.getId(): contribFilters.ReviewerFilterField,
        contribFilters.TypeFilterField.getId(): contribFilters.TypeFilterField,
        contribFilters.TrackFilterField.getId(): contribFilters.TrackFilterField,
        contribFilters.SessionFilterField.getId(): contribFilters.SessionFilterField,
        contribFilters.MaterialSubmittedFilterField.getId(): contribFilters.MaterialSubmittedFilterField,
        contribFilters.ReviewingFilterField.getId(): contribFilters.ReviewingFilterField
    }


methodMap = {
    "contributions.list": ConferenceListContributionsReview
}
