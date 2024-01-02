# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.settings import EventSettingsProxy


attachments_settings = EventSettingsProxy('attachments', {
    'managers_only': False,  # Only event managers can upload attachments
})
