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

import os
from importlib import import_module

from flask_sqlalchemy import Model
from sqlalchemy.orm import joinedload, joinedload_all


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

    def __committed__(self, change):
        """Called after a commit for this object.

        ALWAYS call super if you override this method!

        :param change: The operation that has been committed (delete/change/update)
        """
        pass


def import_all_models():
    """Utility that imports all modules in indico/**/models/"""
    up_segments = ['..'] * __name__.count('.')
    package_root = os.path.normpath(os.path.join(__file__, *up_segments))
    modules = []
    for root, dirs, files in os.walk(package_root):
        if os.path.basename(root) == 'models':
            package = os.path.relpath(root, package_root).replace(os.sep, '.')
            modules += ['indico.{}.{}'.format(package, name[:-3])
                        for name in files
                        if name.endswith('.py') and name != '__init__.py']

    for module in modules:
        import_module(module)
