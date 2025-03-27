# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.settings.converters import EnumConverter, ModelListConverter
from indico.modules.users import UserSettingsProxy
from indico.util.enum import RichIntEnum
from indico.util.i18n import _, pgettext


class RoomEmailMode(RichIntEnum):
    __titles__ = (pgettext('Room notifications', 'None'), _('Rooms I own'),
                  _('Rooms I manage or moderate'), _('Rooms I own, manage or moderate'))
    none = 0
    owned = 1
    managed = 2
    all = 3


rb_user_settings = UserSettingsProxy('roombooking', {
    'email_mode': RoomEmailMode.all,
    'email_blacklist': [],
}, converters={
    'email_mode': EnumConverter(RoomEmailMode),
    'email_blacklist': ModelListConverter('Room'),
})
