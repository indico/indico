# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.settings.proxy import SettingsProxy
from indico.modules.events.settings import EventSettingsProxy


receipts_settings = SettingsProxy('receipts', {
    'allow_external_urls': False,
}, acls={
    'authorized_users'
})

# This SettingsProxy stores default template configs within an event.
receipt_defaults = EventSettingsProxy('receipts_defaults', strict=False)
