# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.settings import SettingsProxy
from indico.modules.events.settings import EventSettingsProxy


program_codes_settings = EventSettingsProxy('program_codes', {
    'session_template': '',
    'session_block_template': '',
    'contribution_template': '',
    'subcontribution_template': '',
})


privacy_settings = EventSettingsProxy('privacy', {
    'data_controller_name': '',
    'data_controller_email': '',
    'privacy_policy_urls': [],
    'privacy_policy': '',
})

global_event_settings = SettingsProxy('events', {
    'allowed_keywords': [],
})
