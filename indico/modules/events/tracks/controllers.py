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

from indico.modules.events.tracks.forms import TrackForm
from indico.web.util import jsonify_form, jsonify_data
from indico.util.string import to_unicode
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageTracksBase(RHConferenceModifBase):
    """Base class for all track management RHs"""

    CSRF_ENABLED = True

    def _process(self):
        return RH._process(self)


class RHCreateTrack(RHManageTracksBase):
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
