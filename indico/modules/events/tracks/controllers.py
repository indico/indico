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

from __future__ import unicode_literals

from io import BytesIO
from operator import itemgetter

from flask import request, flash
from sqlalchemy.orm import subqueryload

from indico.core.db.sqlalchemy.descriptions import RENDER_MODE_WRAPPER_MAP
from indico.modules.events.layout.util import get_menu_entry_by_name
from indico.modules.events.tracks.forms import TrackForm, ProgramForm
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.tracks.operations import create_track, update_track, delete_track, update_program
from indico.modules.events.tracks.settings import track_settings
from indico.modules.events.tracks.views import WPManageTracks, WPDisplayTracks
from indico.util.i18n import _
from indico.util.string import handle_legacy_description
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_form, jsonify_data
from indico.legacy.PDFinterface.conference import ProgrammeToPDF
from indico.legacy.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from indico.legacy.webinterface.rh.conferenceModif import RHConferenceModifBase


def _render_track_list(event):
    tpl = get_template_module('events/tracks/_track_list.html', event=event)
    return tpl.render_track_list(event)


class RHManageTracksBase(RHConferenceModifBase):
    """Base class for all track management RHs"""

    CSRF_ENABLED = True


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


class RHEditProgram(RHManageTracksBase):
    def _process(self):
        settings = track_settings.get_all(self.event_new)
        form = ProgramForm(obj=FormDefaults(**settings))
        if form.validate_on_submit():
            update_program(self.event_new, form.data)
            flash(_("The program has been updated."))
            return jsonify_data()
        elif not form.is_submitted():
            handle_legacy_description(form.program, settings, get_render_mode=itemgetter('program_render_mode'),
                                      get_value=itemgetter('program'))
        return jsonify_form(form)


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
        page_title = get_menu_entry_by_name('program', self.event_new).localized_title
        program = track_settings.get(self.event_new, 'program')
        render_mode = track_settings.get(self.event_new, 'program_render_mode')
        program = RENDER_MODE_WRAPPER_MAP[render_mode](program)
        tracks = (Track.query.with_parent(self.event_new)
                  .options(subqueryload('conveners'),
                           subqueryload('abstract_reviewers'))
                  .order_by(Track.position)
                  .all())
        return WPDisplayTracks.render_template('display.html', self._conf, event=self.event_new, page_title=page_title,
                                               program=program, tracks=tracks)


class RHTracksPDF(RHConferenceBaseDisplay):
    def _process(self):
        pdf = ProgrammeToPDF(self.event_new)
        return send_file('program.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')
