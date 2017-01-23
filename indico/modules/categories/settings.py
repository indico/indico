# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from indico.core.settings import SettingsProxyBase
from indico.core.settings.util import get_setting, get_all_settings
from indico.modules.categories import Category
from indico.modules.categories.models.settings import CategorySetting


def _category_or_id(f):
    @wraps(f)
    def wrapper(self, category, *args, **kwargs):
        if isinstance(category, Category):
            category = category.id
        return f(self, int(category), *args, **kwargs)

    return wrapper


class CategorySettingsProxy(SettingsProxyBase):
    """Proxy class to access category-specific settings for a certain module."""

    @property
    def query(self):
        """Return a query object filtering by the proxy's module."""
        return CategorySetting.find(module=self.module)

    @_category_or_id
    def get_all(self, category, no_defaults=False):
        """Retrieve all settings.

        :param category: Category (or its ID)
        :param no_defaults: Only return existing settings and ignore defaults.
        :return: Dict containing the settings
        """
        return get_all_settings(CategorySetting, None, self, no_defaults, category_id=category)

    @_category_or_id
    def get(self, category, name, default=SettingsProxyBase.default_sentinel):
        """Retrieve the value of a single setting.

        :param category: Category (or its ID)
        :param name: Setting name
        :param default: Default value in case the setting does not exist
        :return: The settings's value or the default value
        """
        self._check_name(name)
        return get_setting(CategorySetting, self, name, default, self._cache, category_id=category)

    @_category_or_id
    def set(self, category, name, value):
        """Set a single setting.

        :param category: Category (or its ID)
        :param name: Setting name
        :param value: Setting value; must be JSON-serializable
        """
        self._check_name(name)
        CategorySetting.set(self.module, name, self._convert_from_python(name, value), category_id=category)
        self._flush_cache()

    @_category_or_id
    def set_multi(self, category, items):
        """Set multiple settings at once.

        :param category: Category (or its ID)
        :param items: Dict containing the new settings
        """
        items = {k: self._convert_from_python(k, v) for k, v in items.iteritems()}
        CategorySetting.set_multi(self.module, items, category_id=category)
        self._flush_cache()

    @_category_or_id
    def delete(self, category, *names):
        """Delete settings.

        :param category: Category (or its ID)
        :param names: One or more names of settings to delete
        """
        for name in names:
            CategorySetting.delete(self.module, *name, category_id=category)
        self._flush_cache()

    @_category_or_id
    def delete_all(self, category):
        """Delete all settings.

        :param category: Category (or its ID)
        """
        CategorySetting.delete_all(self.module, category_id=category)
        self._flush_cache()
