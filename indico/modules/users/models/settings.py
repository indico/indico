# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from indico.core.settings import SettingsProxyBase
from indico.core.settings.models.base import JSONSettingsBase
from indico.core.settings.util import get_all_settings, get_setting
from indico.util.string import return_ascii


class UserSetting(JSONSettingsBase, db.Model):
    """User-specific settings"""
    __table_args__ = (db.Index(None, 'user_id', 'module', 'name'),
                      db.Index(None, 'user_id', 'module'),
                      db.UniqueConstraint('user_id', 'module', 'name'),
                      db.CheckConstraint('module = lower(module)', 'lowercase_module'),
                      db.CheckConstraint('name = lower(name)', 'lowercase_name'),
                      {'schema': 'users'})

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
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
        if isinstance(user, db.m.User):
            user = {'user': user}
        else:
            user = {'user_id': user.id}
        return f(self, user, *args, **kwargs)

    return wrapper


class UserSettingsProxy(SettingsProxyBase):
    """Proxy class to access user-specific settings for a certain module"""

    @property
    def query(self):
        """Returns a query object filtering by the proxy's module."""
        return UserSetting.find(module=self.module)

    @user_or_id
    def get_all(self, user, no_defaults=False):
        """Retrieves all settings

        :param user: ``{'user': user}`` or ``{'user_id': id}``
        :param no_defaults: Only return existing settings and ignore defaults.
        :return: Dict containing the settings
        """
        return get_all_settings(UserSetting, None, self, no_defaults, **user)

    @user_or_id
    def get(self, user, name, default=SettingsProxyBase.default_sentinel):
        """Retrieves the value of a single setting.

        :param user: ``{'user': user}`` or ``{'user_id': id}``
        :param name: Setting name
        :param default: Default value in case the setting does not exist
        :return: The settings's value or the default value
        """
        self._check_name(name)
        return get_setting(UserSetting, self, name, default, self._cache, **user)

    @user_or_id
    def set(self, user, name, value):
        """Sets a single setting.

        :param user: ``{'user': user}`` or ``{'user_id': id}``
        :param name: Setting name
        :param value: Setting value; must be JSON-serializable
        """
        self._check_name(name)
        UserSetting.set(self.module, name, self._convert_from_python(name, value), **user)
        self._flush_cache()

    @user_or_id
    def set_multi(self, user, items):
        """Sets multiple settings at once.

        :param user: ``{'user': user}`` or ``{'user_id': id}``
        :param items: Dict containing the new settings
        """
        for name in items:
            self._check_name(name)
        items = {k: self._convert_from_python(k, v) for k, v in items.iteritems()}
        UserSetting.set_multi(self.module, items, **user)
        self._flush_cache()

    @user_or_id
    def delete(self, user, *names):
        """Deletes settings.

        :param user: ``{'user': user}`` or ``{'user_id': id}``
        :param names: One or more names of settings to delete
        """
        for name in names:
            self._check_name(name)
        UserSetting.delete(self.module, names, **user)
        self._flush_cache()

    @user_or_id
    def delete_all(self, user):
        """Deletes all settings.

        :param user: ``{'user': user}`` or ``{'user_id': id}``
        """
        UserSetting.delete_all(self.module, **user)
        self._flush_cache()
