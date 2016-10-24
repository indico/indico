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
from indico.modules.events.abstracts.controllers.base import AbstractMixin
from indico.modules.events.abstracts.views import WPDisplayAbstracts
from indico.modules.events.tracks.models.tracks import Track
from indico.util.fs import secure_filename
from indico.web.flask.util import send_file
from MaKaC.PDFinterface.conference import AbstractToPDF
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay


class RHDisplayAbstract(AbstractMixin, RHConferenceBaseDisplay):
    CSRF_ENABLED = True

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        AbstractMixin._checkParams(self)

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        AbstractMixin._checkProtection(self)

    def _process(self):
        return WPDisplayAbstracts.render_template('abstract.html', self._conf, abstract=self.abstract, management=False)


class RHDisplayAbstractExportPDF(RHDisplayAbstract):
    def _process(self):
        pdf = AbstractToPDF(self.abstract)
        file_name = secure_filename('abstract-{}.pdf'.format(self.abstract.friendly_id), 'abstract.pdf')
        return send_file(file_name, pdf.generate(), 'application/pdf')


class RHDisplayReviewableTracks(RHConferenceBaseDisplay):
    def _process(self):
        user = session.user
        tracks_set = (user.convener_for_tracks | user.abstract_reviewer_for_tracks) & set(self.event_new.tracks)
        if user in self.event_new.global_abstract_reviewers or user in self.event_new.global_conveners:
            tracks_set.update(self.event_new.tracks)
        return WPDisplayAbstracts.render_template('display/tracks.html', self._conf, event=self.event_new,
                                                  tracks=tracks_set)


class RHDisplayReviewableTrackAbstracts(RHConferenceBaseDisplay):
    normalize_url_spec = {
        'locators': {
            lambda self: self.track
        }
    }

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.track = Track.get_one(request.view_args['track_id'])

    def _process(self):
        abstracts_set = set(self.track.abstracts_accepted) | self.track.abstracts_reviewed |\
                        self.track.abstracts_submitted
        return WPDisplayAbstracts.render_template('display/abstracts.html', self._conf, track_title=self.track.title,
                                                  abstracts=abstracts_set)
