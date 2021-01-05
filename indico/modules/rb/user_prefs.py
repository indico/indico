# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from sqlalchemy import func

from indico.modules.rb.models.rooms import Room
from indico.modules.rb.operations.rooms import get_managed_room_ids
from indico.modules.rb.settings import RoomEmailMode, rb_user_settings
from indico.modules.users import ExtraUserPreferences
from indico.util.i18n import _
from indico.web.forms.fields import IndicoEnumSelectField, IndicoQuerySelectMultipleField


class RBUserPreferences(ExtraUserPreferences):
    @property
    def fields(self):
        query = (Room.query
                 .filter(~Room.is_deleted, Room.id.in_(get_managed_room_ids(self.user)))
                 .order_by(func.indico.natsort(Room.full_name)))

        fields = {
            'email_mode': IndicoEnumSelectField(_('Room notifications'), enum=RoomEmailMode,
                                                description=_(
                                                    'If you own or manage any rooms, you can choose whether to '
                                                    'receive notifications about activity related to them.')),
            'email_blacklist': IndicoQuerySelectMultipleField(_('Room blacklist'),
                                                              query_factory=lambda: query,
                                                              get_label='full_name', collection_class=set,
                                                              render_kw={'size': 10},
                                                              description=_(
                                                                  'Regardless of the room notifications selected '
                                                                  'above, you will never receive notifications '
                                                                  'for rooms selected in this list.'))
        }
        if not query.count():
            # don't show an empty select field if user doesn't manage any rooms
            del fields['email_blacklist']
        return fields

    def load(self):
        return {
            'email_mode': rb_user_settings.get(self.user, 'email_mode'),
            'email_blacklist': rb_user_settings.get(self.user, 'email_blacklist'),
        }

    def save(self, data):
        rb_user_settings.set_multi(self.user, data)

    @classmethod
    def is_active(cls, user):
        return (rb_user_settings.get(user, 'email_mode', None) is not None or
                rb_user_settings.get(user, 'email_blacklist', None) is not None or
                get_managed_room_ids(user))
