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


from __future__ import unicode_literals

from flask import request, session
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts.controllers.base import (AbstractMixin, DisplayAbstractListMixin,
                                                              CustomizeAbstractListMixin)
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.util import AbstractListGeneratorDisplay
from indico.modules.events.abstracts.views import WPDisplayAbstractsReviewing
from indico.modules.events.tracks.models.tracks import Track
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHAbstractsBase(RHConferenceBaseDisplay):
    CSRF_ENABLED = True
    EVENT_FEATURE = 'abstracts'


class RHAbstractsReviewBase(AbstractMixin, RHAbstractsBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract
        }
    }

    def _checkProtection(self):
        RHAbstractsBase._checkProtection(self)
        AbstractMixin._checkProtection(self)

    def _checkParams(self, params):
        RHAbstractsBase._checkParams(self, params)
        AbstractMixin._checkParams(self)


class RHAbstractsDownloadAttachment(RHAbstractsReviewBase):
    """Download an attachment file belonging to an abstract."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.abstract_file
        }
    }

    def _checkParams(self, params):
        RHAbstractsReviewBase._checkParams(self, params)
        self.abstract_file = AbstractFile.get_one(request.view_args['file_id'])

    def _process(self):
        return self.abstract_file.send()


class RHDisplayReviewableTracks(RHAbstractsBase):
    def _process(self):
        user = session.user
        tracks_set = (user.convener_for_tracks | user.abstract_reviewer_for_tracks) & set(self.event_new.tracks)
        if user in self.event_new.global_abstract_reviewers or user in self.event_new.global_conveners:
            tracks_set.update(self.event_new.tracks)
        return WPDisplayAbstractsReviewing.render_template('display/tracks.html', self._conf, event=self.event_new,
                                                           tracks=tracks_set)


class RHDisplayAbstractListBase(RHAbstractsBase):
    """Base class for all abstract list operations"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.track
        }
    }

    def _checkParams(self, params):
        RHAbstractsBase._checkParams(self, params)
        self.track = Track.get_one(request.view_args['track_id'])
        self.list_generator = AbstractListGeneratorDisplay(event=self.event_new, track=self.track)

    def _checkProtection(self):
        if not self.track.can_review_abstracts(session.user) and not self.track.can_convene(session.user):
            raise Forbidden


class RHDisplayReviewableTrackAbstracts(DisplayAbstractListMixin, RHDisplayAbstractListBase):
    view_class = WPDisplayAbstractsReviewing
    template = 'display/abstracts.html'

    def _render_template(self, **kwargs):
        return DisplayAbstractListMixin._render_template(self, track=self.track, **kwargs)


class RHDisplayAbstractListCustomize(CustomizeAbstractListMixin, RHDisplayAbstractListBase):
    view_class = WPDisplayAbstractsReviewing
