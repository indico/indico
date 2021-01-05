# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db.sqlalchemy.descriptions import RenderMode
from indico.core.settings.converters import EnumConverter
from indico.modules.events.settings import EventSettingsProxy


track_settings = EventSettingsProxy('tracks', {
    'program': '',
    'program_render_mode': RenderMode.markdown
}, converters={
    'program_render_mode': EnumConverter(RenderMode)
})
