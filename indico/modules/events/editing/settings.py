# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.editing.models.editable import EditableType
from indico.modules.events.settings import EventSettingsProxy


editing_settings = EventSettingsProxy('editing', {
    'editable_types': ['paper'],
})

_defaults = {'self_assign_allowed': False}

editable_type_settings = {
    EditableType.paper: EventSettingsProxy('editing_paper', _defaults),
    EditableType.poster: EventSettingsProxy('editing_poster', _defaults),
    EditableType.slides: EventSettingsProxy('editing_slides', _defaults)
}
