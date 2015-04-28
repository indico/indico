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

import os
import pkg_resources
from importlib import import_module

from flask import g
from flask_sqlalchemy import Model
from sqlalchemy.orm import joinedload, joinedload_all
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.orm.exc import NoResultFound


class IndicoModel(Model):
    """Indico DB model"""

    @classmethod
    def find(cls, *args, **kwargs):
        special_field_names = ('join', 'eager', 'eager_all')
        special_fields = {}
        for key in special_field_names:
            value = kwargs.pop('_{}'.format(key), ())
            if not isinstance(value, (list, tuple)):
                value = (value,)
            special_fields[key] = value
        options = []
        options += [joinedload(rel) for rel in special_fields['eager']]
        options += [joinedload_all(rel) for rel in special_fields['eager_all']]
        return (cls.query
                .filter_by(**kwargs)
                .join(*special_fields['join'])
                .filter(*args)
                .options(*options))

    @classmethod
    def find_all(cls, *args, **kwargs):
        return cls.find(*args, **kwargs).all()

    @classmethod
    def find_first(cls, *args, **kwargs):
        return cls.find(*args, **kwargs).first()

    @classmethod
    def find_one(cls, *args, **kwargs):
        return cls.find(*args, **kwargs).one()

    @classmethod
    def get(cls, oid):
        return cls.query.get(oid)

    @classmethod
    def get_one(cls, oid):
        obj = cls.query.get(oid)
        if obj is None:
            raise NoResultFound()
        return obj

    def __committed__(self, change):
        """Called after a commit for this object.

        ALWAYS call super if you override this method!

        :param change: The operation that has been committed (delete/change/update)
        """
        if hasattr(g, 'memoize_cache'):
            del g.memoize_cache


def import_all_models(package_name=None):
    """Utility that imports all modules in indico/**/models/

    :param package_name: Package name to scan for models. If unset,
                         the top-level package containing this file
                         is used.
    """
    if package_name:
        distribution = pkg_resources.get_distribution(package_name)
        package_root = os.path.join(distribution.location, package_name)
    else:
        # Don't use pkg_resources since `indico` is still a namespace package...`
        package_name = 'indico'
        up_segments = ['..'] * __name__.count('.')
        package_root = os.path.normpath(os.path.join(__file__, *up_segments))
    modules = []
    for root, dirs, files in os.walk(package_root):
        if os.path.basename(root) == 'models':
            package = os.path.relpath(root, package_root).replace(os.sep, '.')
            modules += ['{}.{}.{}'.format(package_name, package, name[:-3])
                        for name in files
                        if name.endswith('.py') and name != '__init__.py' and not name.endswith('_test.py')]

    for module in modules:
        import_module(module)


def attrs_changed(obj, *attrs):
    """Checks if the given fields have been changed since the last flush

    :param obj: SQLAlchemy-mapped object
    :param attrs: attribute names
    """
    return any(get_history(obj, attr).has_changes() for attr in attrs)
