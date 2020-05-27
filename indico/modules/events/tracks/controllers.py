# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from io import BytesIO
from operator import attrgetter, itemgetter

from flask import flash, request

from indico.core.db.sqlalchemy.descriptions import RENDER_MODE_WRAPPER_MAP
from indico.legacy.pdfinterface.conference import ProgrammeToPDF
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.tracks.forms import ProgramForm, TrackForm, TrackGroupForm
from indico.modules.events.tracks.models.groups import TrackGroup
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.tracks.operations import (create_track, create_track_group, delete_track, delete_track_group,
                                                     update_program, update_track, update_track_group)
from indico.modules.events.tracks.settings import track_settings
from indico.modules.events.tracks.views import WPDisplayTracks, WPManageTracks
from indico.util.i18n import _
from indico.util.string import handle_legacy_description
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form


def _render_track_list(event):
    list_items = event.get_sorted_tracks()
    tpl = get_template_module('events/tracks/_track_list.html', event=event, list_items=list_items)
    return tpl.render_list(event, list_items)


class RHManageTracksBase(RHManageEventBase):
    """Base class for all track management RHs"""


class RHManageTrackBase(RHManageTracksBase):
    """Base class for track management RHs related to a specific track"""

    normalize_url_spec = {
        'locators': {
            lambda self: self.track
        }
    }

    def _process_args(self):
        RHManageTracksBase._process_args(self)
        self.track = Track.get_or_404(request.view_args['track_id'])


class RHManageTrackGroupBase(RHManageEventBase):
    normalize_url_spec = {
        'locators': {
            lambda self: self.track_group
        }
    }

    def _process_args(self):
        RHManageEventBase._process_args(self)
        self.track_group = TrackGroup.get_or_404(request.view_args['track_group_id'])


class RHManageTracks(RHManageTracksBase):
    def _process(self):
        tracks = self.event.tracks
        list_items = self.event.get_sorted_tracks()
        return WPManageTracks.render_template('management.html', self.event, list_items=list_items, tracks=tracks)


class RHEditProgram(RHManageTracksBase):
    def _process(self):
        settings = track_settings.get_all(self.event)
        form = ProgramForm(obj=FormDefaults(**settings))
        if form.validate_on_submit():
            update_program(self.event, form.data)
            flash(_("The program has been updated."))
            return jsonify_data()
        elif not form.is_submitted():
            handle_legacy_description(form.program, settings, get_render_mode=itemgetter('program_render_mode'),
                                      get_value=itemgetter('program'))
        return jsonify_form(form)


class RHCreateTrack(RHManageTracksBase):
    def _process(self):
        form = TrackForm(event=self.event)
        if form.validate_on_submit():
            track = create_track(self.event, form.data)
            flash(_('Track "{}" has been created.').format(track.title), 'success')
            return jsonify_data(html=_render_track_list(self.event), new_track_id=track.id,
                                tracks=[{'id': t.id, 'title': t.title} for t in self.event.tracks])
        return jsonify_form(form)


class RHEditTrack(RHManageTrackBase):
    def _process(self):
        form = TrackForm(event=self.event, obj=self.track)
        if form.validate_on_submit():
            update_track(self.track, form.data)
            flash(_('Track "{}" has been modified.').format(self.track.title), 'success')
            return jsonify_data(html=_render_track_list(self.event))
        return jsonify_form(form)


class RHSortTracks(RHManageTracksBase):
    def _process(self):
        sort_order = request.json['sort_order']
        tracks = {t.id: t for t in self.event.tracks}
        track_groups = {tg.id: tg for tg in self.event.track_groups}
        for position, item in enumerate(sort_order, 1):
            if item['type'] == 'track':
                tracks[item['id']].position = position
                parent_id = item['parent']
                track_group = (TrackGroup.query.with_parent(self.event)
                               .filter(TrackGroup.id == parent_id).first())
                tracks[item['id']].track_group = track_group
            elif item['type'] == 'group':
                track_groups[item['id']].position = position
        return jsonify_data(html=_render_track_list(self.event))


class RHDeleteTrack(RHManageTrackBase):
    def _process(self):
        delete_track(self.track)
        flash(_('Track "{}" has been deleted.').format(self.track.title), 'success')
        return jsonify_data(html=_render_track_list(self.event))


class RHDisplayTracks(RHDisplayEventBase):
    def _process(self):
        program = track_settings.get(self.event, 'program')
        render_mode = track_settings.get(self.event, 'program_render_mode')
        program = RENDER_MODE_WRAPPER_MAP[render_mode](program)
        tracks = (Track.query.with_parent(self.event)
                  .filter(~Track.track_group.has())
                  .all())
        track_groups = self.event.track_groups
        items = sorted(tracks + track_groups, key=attrgetter('position'))
        return WPDisplayTracks.render_template('display.html', self.event, program=program, items=items)


class RHTracksPDF(RHDisplayEventBase):
    def _process(self):
        pdf = ProgrammeToPDF(self.event)
        return send_file('program.pdf', BytesIO(pdf.getPDFBin()), 'application/pdf')


class RHCreateTrackGroup(RHManageEventBase):
    def _process(self):
        form = TrackGroupForm()
        if form.validate_on_submit():
            create_track_group(self.event, form.data)
            return jsonify_data(html=_render_track_list(self.event))
        return jsonify_form(form)


class RHEditTrackGroup(RHManageTrackGroupBase):
    def _process(self):
        form = TrackGroupForm(obj=self.track_group)
        if form.validate_on_submit():
            update_track_group(self.track_group, form.data)
            return jsonify_data(html=_render_track_list(self.event))
        return jsonify_form(form)


class RHDeleteTrackGroup(RHManageTrackGroupBase):
    def _process(self):
        delete_track_group(self.track_group)
        flash(_('Track Group "{}" has been deleted.').format(self.track_group.title), 'success')
        return jsonify_data(html=_render_track_list(self.event))
