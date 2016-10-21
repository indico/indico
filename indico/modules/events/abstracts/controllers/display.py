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

from flask import request
from flask import session
from indico.modules.events.abstracts.controllers.base import AbstractMixin
from indico.modules.events.abstracts.views import WPDisplayAbstracts
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.users import User
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
        tracks_set, events_set = set(), set()
        tracks_set.update(user.convener_for_tracks, user.abstract_reviewer_for_tracks)
        events_set.update(user.global_convener_for_events, user.global_abstract_reviewer_for_events)
        for e in events_set:
            tracks_set.update(e.tracks)
        tracks = {t for t in tracks_set if t.event_id == self.event_new.id}
        return WPDisplayAbstracts.render_template('display/tracks.html', self._conf, event=self.event_new,
                                                  tracks=tracks)


class RHDisplayReviewableTrackAbstracts(RHConferenceBaseDisplay):
    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self.track = Track.get_one(request.view_args['track_id'])

    def _process(self):
        abstracts_set = set()
        abstracts_set.update(self.track.abstracts_accepted, self.track.abstracts_reviewed,
                             self.track.abstracts_submitted)
        return WPDisplayAbstracts.render_template('display/abstracts.html', self._conf, track_title=self.track.title,
                                                  abstracts=abstracts_set)
