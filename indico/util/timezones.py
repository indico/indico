# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import cached_property

from flask import session
from pytz import common_timezones, common_timezones_set

from indico.core.config import config


class ActiveTz:
    USER = 'user'
    LOCAL = 'local'
    CUSTOM = 'custom'
    LOCAL_TZ_ALIAS = 'LOCAL'

    def __init__(self, page_local_tz=None):
        self.profile_tz = session.user and session.user.settings.get('timezone')
        self.session_tz = session.timezone
        self.default_tz = config.DEFAULT_TIMEZONE
        self.page_local_tz = page_local_tz

    @cached_property
    def tz_mode(self):
        if self.profile_tz and self.profile_tz == self.session_tz:
            return self.USER
        if self.session_tz == self.LOCAL_TZ_ALIAS:
            return self.LOCAL
        return self.CUSTOM

    @cached_property
    def active_tz(self):
        if self.tz_mode == self.USER:
            return self.profile_tz
        if self.tz_mode == self.LOCAL:
            return self.page_local_tz or self.default_tz
        return self.session_tz

    @classmethod
    def get_active_tz(cls, page_local_tz=None, protected_object=None):
        tz = cls(page_local_tz).active_tz
        if tz == cls.LOCAL_TZ_ALIAS and protected_object:
            return protected_object.timezone
        return tz


class TzChoice(ActiveTz):

    def __init__(self, page_local_tz=None, page_forces_tz=False):
        super().__init__(page_local_tz)
        self.page_forces_tz = page_forces_tz

    @cached_property
    def has_no_choice(self):
        return self.page_forces_tz

    @cached_property
    def all_tzs(self):
        if self.active_tz not in common_timezones_set:
            return [*common_timezones, self.active_tz]
        return common_timezones
