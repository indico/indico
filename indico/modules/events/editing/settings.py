# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.editing.models.editable import EditableType
from indico.modules.events.settings import EventSettingsProxy


editing_settings = EventSettingsProxy('editing', {
    'service_event_identifier': None,
    'service_url': None,
    'service_token': None,
    'editable_types': ['paper'],
})

_defaults = {
    'self_assign_allowed': False,
    'anonymous_team': False,
    'submission_enabled': False,
    'editing_enabled': False,
}

editable_type_settings = {
    EditableType.paper: EventSettingsProxy('editing_paper', _defaults),
    EditableType.poster: EventSettingsProxy('editing_poster', _defaults),
    EditableType.slides: EventSettingsProxy('editing_slides', _defaults)
}
