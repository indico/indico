# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from functools import wraps

from indico.core.db import db
from indico.core.models.settings import SettingsBase, SettingsProxyBase, _get_all, _get, _default
from indico.modules.users import User
from indico.util.string import return_ascii


class UserSetting(SettingsBase, db.Model):
    """User-specific settings"""
    __table_args__ = (db.Index(None, 'user_id', 'module', 'name'),
                      db.Index(None, 'user_id', 'module'),
                      db.UniqueConstraint('user_id', 'module', 'name'),
                      db.CheckConstraint('module = lower(module)', 'lowercase_module'),
                      db.CheckConstraint('name = lower(name)', 'lowercase_name'),
                      {'schema': 'users'})

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(User.id),
        nullable=False,
        index=True
    )

    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            '_all_settings',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
    )

    @return_ascii
    def __repr__(self):
        return '<UserSetting({}, {}, {}, {!r})>'.format(self.user_id, self.module, self.name, self.value)


def user_or_id(f):
    @wraps(f)
    def wrapper(self, user, *args, **kwargs):
        if isinstance(user, User):
            user = user.id
        return f(self, user, *args, **kwargs)

    return wrapper


class UserSettingsProxy(SettingsProxyBase):
    """Proxy class to access user-specific settings for a certain module"""

    @user_or_id
    def get_all(self, user, no_defaults=False):
        """Retrieves all settings

        :param user: User (or their ID)
        :param no_defaults: Only return existing settings and ignore defaults.
        :return: Dict containing the settings
        """
        return _get_all(UserSetting, self, no_defaults, user_id=user)

    @user_or_id
    def get(self, user, name, default=_default):
        """Retrieves the value of a single setting.

        :param user: User (or their ID)
        :param name: Setting name
        :param default: Default value in case the setting does not exist
        :return: The settings's value or the default value
        """
        self._check_strict(name)
        return _get(UserSetting, self, name, default, self._cache, user_id=user)

    @user_or_id
    def set(self, user, name, value):
        """Sets a single setting.

        :param user: User (or their ID)
        :param name: Setting name
        :param value: Setting value; must be JSON-serializable
        """
        self._check_strict(name)
        UserSetting.set(self.module, name, value, user_id=user)
        self._flush_cache()

    @user_or_id
    def set_multi(self, user, items):
        """Sets multiple settings at once.

        :param user: User (or their ID)
        :param items: Dict containing the new settings
        """
        for name in items:
            self._check_strict(name)
        UserSetting.set_multi(self.module, items, user_id=user)
        self._flush_cache()

    @user_or_id
    def delete(self, user, *names):
        """Deletes settings.

        :param user: User (or their ID)
        :param names: One or more names of settings to delete
        """
        for name in names:
            self._check_strict(name)
        UserSetting.delete(self.module, names, user_id=user)
        self._flush_cache()

    @user_or_id
    def delete_all(self, user):
        """Deletes all settings.

        :param user: User (or their ID)
        """
        UserSetting.delete_all(self.module, user_id=user)
        self._flush_cache()
