# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.settings import SettingsProxy


core_settings = SettingsProxy('core', {
    'site_title': 'Indico',
    'site_organization': ''
})


social_settings = SettingsProxy('social', {
    'enabled': True,
})
