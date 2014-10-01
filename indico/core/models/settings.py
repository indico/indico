## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db.sqlalchemy import db
from indico.util.string import return_ascii


_default = object()


class Setting(db.Model):
    __tablename__ = 'settings'
    __table_args__ = (db.Index('ix_settings_module_key', 'module', 'name'),
                      db.UniqueConstraint('module', 'name'),
                      db.CheckConstraint('module = lower(module)'),
                      db.CheckConstraint('name = lower(name)'),
                      {'schema': 'indico'})

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    module = db.Column(
        db.String,
        index=True
    )
    name = db.Column(
        db.String,
        index=True
    )
    value = db.Column(
        JSON
    )

    @return_ascii
    def __repr__(self):
        return u'<Setting({}, {}, {!r})>'.format(self.module, self.name, self.value)

    @classmethod
    def get_setting(cls, module, name):
        return cls.find_first(module=module, name=name)

    @classmethod
    def get_all_settings(cls, module):
        return {s.name: s for s in cls.find(module=module)}

    @classmethod
    def get_all(cls, module):
        return {s.name: s.value for s in cls.find(module=module)}

    @classmethod
    def get(cls, module, name, default=None):
        setting = cls.get_setting(module, name)
        if setting is None:
            return default
        return setting.value

    @classmethod
    def set(cls, module, name, value):
        setting = cls.get_setting(module, name)
        if setting is None:
            setting = cls(module=module, name=name)
            db.session.add(setting)
        setting.value = value
        db.session.flush()

    @classmethod
    def set_multi(cls, module, items):
        existing = cls.get_all_settings(module)
        for name in items.viewkeys() - existing.viewkeys():
            setting = cls(module=module, name=name, value=items[name])
            db.session.add(setting)
        for name in items.viewkeys() & existing.viewkeys():
            existing[name].value = items[name]
        db.session.flush()

    @classmethod
    def delete(cls, module, *names):
        if not names:
            return
        Setting.find(Setting.name.in_(names), Setting.module == module).delete(synchronize_session='fetch')
        db.session.flush()

    @classmethod
    def delete_all(cls, module):
        Setting.find(module=module).delete()
        db.session.flush()


class SettingsProxy(object):
    """Proxy class to access settings for a certain module"""

    def __init__(self, module, defaults=None):
        self.module = module
        self.defaults = defaults or {}

    def get_setting(self, name):
        """Retrieves a single setting.

        :param name: Setting name
        :return: The setting
        """
        return Setting.get_setting(self.module, name)

    def get_all(self, no_defaults=False):
        """Retrieves all settings

        :param no_defaults: Only return existing settings and ignore defaults.
        :return: Dict containing the settings
        """
        if no_defaults:
            return Setting.get_all(self.module)
        settings = dict(self.defaults)
        settings.update(Setting.get_all(self.module))
        return settings

    def get(self, name, default=_default):
        """Retrieves the value of a single setting.

        :param name: Setting name
        :param default: Default value in case the setting does not exist
        :return: The settings's value or the default value
        """
        setting = Setting.get(self.module, name, default)
        if setting is _default:
            return self.defaults.get(name)
        return setting

    def set(self, name, value):
        """Sets a single setting.

        :param name: Setting name
        :param value: Setting value; must be JSON-serializable
        """
        return Setting.set(self.module, name, value)

    def set_multi(self, items):
        """Sets multiple settings at once.

        :param items: Dict containing the new settings
        """
        return Setting.set_multi(self.module, items)

    def delete(self, *names):
        """Deletes settings.

        :param names: One or more names of settings to delete
        """
        return Setting.delete(self.module, names)

    def delete_all(self):
        """Deletes all settings."""
        return Setting.delete_all(self.module)

    @return_ascii
    def __repr__(self):
        return u'<SettingsProxy({})>'.format(self.module)
