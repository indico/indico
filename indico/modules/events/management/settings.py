# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.settings import EventSettingsProxy


program_codes_settings = EventSettingsProxy('program_codes', {
    'session_template': '',
    'session_block_template': '',
    'contribution_template': '',
    'subcontribution_template': '',
})
