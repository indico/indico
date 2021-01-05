# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.settings.converters import EnumConverter, ModelListConverter
from indico.modules.users import UserSettingsProxy
from indico.util.i18n import _
from indico.util.struct.enum import RichIntEnum


class RoomEmailMode(RichIntEnum):
    __titles__ = (_('None'), _('Rooms I own'), _('Rooms I manage'), _('Rooms I own or manage'))
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
