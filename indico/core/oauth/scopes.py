# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.util.i18n import _


SCOPES = {
    'read:user': _('User information (read only)'),
    'read:legacy_api': _('Legacy API (read only)'),
    'write:legacy_api': _('Legacy API (write only)'),
    'registrants': _('Event registrants'),
    'read:everything': _('Everything (only GET)'),
    'full:everything': _('Everything (all methods)'),
}
