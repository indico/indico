# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.settings import EventSettingsProxy


# This SettingsProxy stores default template configs within an event.
receipt_defaults = EventSettingsProxy('receipts_defaults', strict=False)
