# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.rb.settings import RoomEmailMode, rb_user_settings
from indico.modules.users import ExtraUserPreferences
from indico.util.i18n import _
from indico.web.forms.fields import IndicoEnumSelectField


class RBUserPreferences(ExtraUserPreferences):
    fields = {
        'email_mode': IndicoEnumSelectField(_('Room notifications'), enum=RoomEmailMode,
                                            description=_('If you own or manage any rooms, you can choose whether to '
                                                          'receive notifications about activity related to them.'))
    }

    def load(self):
        return {
            'email_mode': rb_user_settings.get(self.user, 'email_mode'),
        }

    def save(self, data):
        rb_user_settings.set(self.user, 'email_mode', data['email_mode'])
