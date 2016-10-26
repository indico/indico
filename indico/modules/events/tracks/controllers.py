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

from io import BytesIO

from flask import request, flash

from indico.modules.events.layout.util import get_menu_entry_by_name
from indico.modules.events.tracks.forms import TrackForm
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.tracks.operations import create_track, update_track, delete_track
from indico.modules.events.tracks.settings import track_settings
from indico.modules.events.tracks.views import WPManageTracks, WPDisplayTracks
from indico.util.i18n import _
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file
from indico.web.util import jsonify_form, jsonify_data
from MaKaC.PDFinterface.conference import ProgrammeToPDF
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


def _render_track_list(event):
    tpl = get_template_module('events/tracks/_track_list.html', event=event)
    return tpl.render_track_list(event)


class RHManageTracksBase(RHConferenceModifBase):
    """Base class for all track management RHs"""

    CSRF_ENABLED = True

    def _process(self):
        return RH._process(self)


class RHManageTrackBase(RHManageTracksBase):
    """Base class for track management RHs related to a specific track"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.track
        }
    }

    def _checkParams(self, params):
        RHManageTracksBase._checkParams(self, params)
        self.track = Track.get_one(request.view_args['track_id'])


class RHManageTracks(RHManageTracksBase):
    def _process(self):
        tracks = self.event_new.tracks
        return WPManageTracks.render_template('management.html', self._conf, event=self.event_new, tracks=tracks)


class RHCreateTrack(RHManageTracksBase):
    def _process(self):
        form = TrackForm()
        if form.validate_on_submit():
            track = create_track(self.event_new, form.data)
            flash(_('Track "{}" has been created.').format(track.title), 'success')
            return jsonify_data(html=_render_track_list(self.event_new), new_track_id=track.id,
                                tracks=[{'id': t.id, 'title': t.title} for t in self.event_new.tracks])
        return jsonify_form(form)


class RHEditTrack(RHManageTrackBase):
    def _process(self):
        form = TrackForm(obj=self.track)
        if form.validate_on_submit():
            update_track(self.track, form.data)
            flash(_('Track "{}" has been modified.').format(self.track.title), 'success')
            return jsonify_data(html=_render_track_list(self.event_new))
        return jsonify_form(form)


class RHSortTracks(RHManageTracksBase):
    def _process(self):
        sort_order = request.json['sort_order']
        tracks = {t.id: t for t in self.event_new.tracks}
        for position, track_id in enumerate(sort_order, 1):
            if track_id in tracks:
                tracks[track_id].position = position


class RHDeleteTrack(RHManageTrackBase):
    def _process(self):
        delete_track(self.track)
        flash(_('Track "{}" has been deleted.').format(self.track.title), 'success')
        return jsonify_data(html=_render_track_list(self.event_new))


class RHDisplayTracks(RHConferenceBaseDisplay):
    def _process(self):
        page_title = get_menu_entry_by_name('program', self._conf).localized_title
        program = track_settings.get(self.event_new, 'program')
        return WPDisplayTracks.render_template('display.html', self._conf, event=self.event_new, page_title=page_title,
                                               program=program)


class RHTracksPDF(RHConferenceBaseDisplay):
    def _process(self):
        pdf = ProgrammeToPDF(self.event_new)
        return send_file('program.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')
