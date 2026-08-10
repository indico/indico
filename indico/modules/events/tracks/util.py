# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import render_template

from indico.modules.events.layout.util import get_menu_entry_by_name
from indico.modules.events.timetable.util import create_pdf
from indico.modules.events.tracks.settings import track_settings


def generate_program_pdf(event):
    title = get_menu_entry_by_name('program', event).localized_title
    program_text = track_settings.get(event, 'program')
    top_level_tracks = event.get_sorted_tracks()
    css = render_template('events/tracks/pdf/program.css')
    html = render_template(
        'events/tracks/pdf/program.html',
        event=event,
        title=title,
        program_text=program_text,
        top_level_tracks=top_level_tracks,
    )
    return create_pdf(html, css, event)
