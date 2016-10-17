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

from indico.modules.events.layout.util import get_menu_entry_by_name
from indico.modules.events.tracks.forms import TrackForm
from indico.modules.events.tracks.operations import create_track
from indico.modules.events.tracks.settings import track_settings
from indico.modules.events.tracks.views import WPManageTracks, WPDisplayTracks
from indico.web.util import jsonify_form, jsonify_data
from indico.util.string import to_unicode
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageTracksBase(RHConferenceModifBase):
    """Base class for all track management RHs"""

    CSRF_ENABLED = True

    def _process(self):
        return RH._process(self)


class RHManageTracks(RHManageTracksBase):
    def _process(self):
        tracks = self.event_new.tracks
        return WPManageTracks.render_template('management.html', self._conf, event=self.event_new, tracks=tracks)


class RHCreateTrack(RHManageTracksBase):
    def _process(self):
        form = TrackForm()
        if form.validate_on_submit():
            create_track(self.event_new, form.data)
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHCreateTrackOld(RHManageTracksBase):
    """Create a track"""

    def _process(self):
        form = TrackForm()
        if form.validate_on_submit():
            track = self._conf.newTrack()
            track.setTitle(form.title.data.encode('utf-8'))
            track.setDescription(form.description.data.encode('utf-8'))
            self._conf.addTrack(track)
            return jsonify_data(flash=False, new_track_id=int(track.getId()),
                                tracks=[{'id': int(t.getId()), 'title': to_unicode(t.getTitle())}
                                        for t in self._conf.getTrackList()])
        return jsonify_form(form)


class RHDisplayTracks(RHConferenceBaseDisplay):
    def _process(self):
        page_title = get_menu_entry_by_name('program', self._conf).localized_title
        program = track_settings.get(self.event_new, 'program')
        return WPDisplayTracks.render_template('display.html', self._conf, event=self.event_new, page_title=page_title,
                                               program=program)
