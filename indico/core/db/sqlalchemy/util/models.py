# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
from sqlalchemy import inspect, orm
from sqlalchemy.event import listens_for
from sqlalchemy.orm import joinedload, contains_eager
from sqlalchemy.orm.attributes import get_history, set_committed_value
from sqlalchemy.orm.exc import NoResultFound

from indico.core import signals


class IndicoModel(Model):
    """Indico DB model"""

    @classmethod
    def find(cls, *args, **kwargs):
        special_field_names = ('join', 'eager')
        special_fields = {}
        for key in special_field_names:
            value = kwargs.pop('_{}'.format(key), ())
            if not isinstance(value, (list, tuple)):
                value = (value,)
            special_fields[key] = value
        joined_eager = set(special_fields['eager']) & set(special_fields['join'])
        options = []
        options += [joinedload(rel) for rel in special_fields['eager'] if rel not in joined_eager]
        options += [contains_eager(rel) for rel in joined_eager]
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
    def get(cls, oid, is_deleted=None):
        """Get an object based on its primary key.

        :param oid: The primary key of the object
        :param is_deleted: If specified, ``None`` will be returned if
                           the ``is_deleted`` attribute of the object
                           does not match the specified value.  This
                           is useful when you want to keep the
                           simplicity of ``get()`` without having to
                           write extra code to filter out deleted
                           objects.
        """
        obj = cls.query.get(oid)
        if obj is None:
            return None
        if is_deleted is not None and obj.is_deleted != is_deleted:
            return None
        return obj

    @classmethod
    def get_one(cls, oid, is_deleted=None):
        obj = cls.get(oid, is_deleted=is_deleted)
        if obj is None:
            raise NoResultFound()
        return obj

    @classmethod
    def has_rows(cls):
        """Checks if the underlying table has any rows.

        This is done in an efficient way and should preferred over
        calling the `count` method unless you actually care about
        the exact number of rows.
        """
        from indico.core.db import db
        # we just need one "normal" column so sqlalchemy doesn't involve relationships
        # it doesn't really matter which one it is - it's never even used in the query
        pk_col = getattr(cls, inspect(cls).primary_key[0].name)
        return db.session.query(db.session.query(pk_col).exists()).one()[0]

    def assign_id(self):
        """Immediately assigns an ID to the object.

        This only works if the table has exactly one serial column.
        It also "wastes" the ID if the new object is not actually
        committed, but it allows you to use it e.g. in a filename
        that needs to be stored in that row.

        If the object already has an ID, calling this function does
        nothing so it is safe to call it unconditionally in places
        where you always need an ID but don't really care if the
        object already has one or not.
        """
        from indico.core.db import db
        table_name = type(self).__table__.fullname
        mapper = inspect(type(self))
        candidates = [(attr, col.name) for attr, col in mapper.columns.items()
                      if col.primary_key and col.autoincrement and isinstance(col.type, db.Integer)]
        if len(candidates) != 1:
            raise TypeError('assign_id only works for tables with exactly one auto-incrementing PK column')
        attr_name, col_name = candidates[0]
        if getattr(self, attr_name) is not None:
            return
        with db.session.no_autoflush:
            id_ = db.session.query(db.func.nextval(db.func.pg_get_serial_sequence(table_name, col_name))).one()[0]
        setattr(self, attr_name, id_)

    def populate_from_dict(self, data):
        """Populates the object with values in a dictionary

        :param data: a dict containing values to populate the object.
        """
        for key, value in data.iteritems():
            if not hasattr(self, key):
                raise ValueError("{} has no attribute '{}'".format(type(self).__name__, key))
            setattr(self, key, value)

    def __committed__(self, change):
        """Called after a commit for this object.

        ALWAYS call super if you override this method!

        :param change: The operation that has been committed (delete/insert/update)
        """
        if hasattr(g, 'memoize_cache'):
            del g.memoize_cache
        signals.model_committed.send(type(self), obj=self, change=change)


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


def get_default_values(model):
    """Returns a dict containing all static default values of a model.
    This only takes `default` into account, not `server_default`.
    :param model: A SQLAlchemy model
    """
    return {attr.key: attr.columns[0].default.arg
            for attr in model.__mapper__.column_attrs
            if len(attr.columns) == 1 and attr.columns[0].default and attr.columns[0].default.is_scalar}


def get_simple_column_attrs(model):
    """
    Returns a set containing all "simple" column attributes, i.e.
    attributes which map to a table column and are neither primary
    key nor foreign key.

    This is useful if you want to get a list of attributes are are
    usually safe to copy without extra processing when creating a
    copy of a database object.

    :param model: A SQLAlchemy model
    :return: A set of attribute names
    """
    return {attr.key
            for attr in inspect(model).column_attrs
            if len(attr.columns) == 1 and not attr.columns[0].primary_key and not attr.columns[0].foreign_keys}


def auto_table_args(cls, **extra_kwargs):
    """Merges SQLAlchemy ``__table_args__`` values.

    This is useful when using mixins to compose model classes if the
    mixins need to define custom ``__table_args__``. Since defining
    them directly they can define ``__auto_table_args`` classproperties
    which will then merged in the final model class using the regular
    table args attribute::

        @declared_attr
        def __table_args__(cls):
            return auto_table_args(cls)


    :param cls: A class that has one or more `__auto_table_args`
                classproperties (usually from mixins)
    :param extra_kwargs: Additional keyword arguments that will be
                         added after merging the table args.
                         This is mostly for convenience so you can
                         quickly specify e.g. a schema.
    :return: A value suitable for ``__table_args__``.
    """
    posargs = []
    kwargs = {}
    for attr in dir(cls):
        if not attr.endswith('__auto_table_args'):
            continue
        value = getattr(cls, attr)
        if not value:
            continue
        if isinstance(value, dict):
            kwargs.update(value)
        elif isinstance(value, tuple):
            if isinstance(value[-1], dict):
                posargs.extend(value[:-1])
                kwargs.update(value[-1])
            else:
                posargs.extend(value)
        else:  # pragma: no cover
            raise ValueError('Unexpected tableargs: {}'.format(value))
    kwargs.update(extra_kwargs)
    if posargs and kwargs:
        return tuple(posargs) + (kwargs,)
    elif kwargs:
        return kwargs
    else:
        return tuple(posargs)


def _get_backref_name(relationship):
    return relationship.backref if isinstance(relationship.backref, basestring) else relationship.backref[0]


def populate_one_to_one_backrefs(model, *relationships):
    """Populates the backref of a one-to-one relationship on load

    See this post in the SQLAlchemy docs on why it's useful/necessary:
    http://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html#creating-custom-load-rules

    :param model: The model class.
    :param relationships: The names of the relationships.
    """
    assert relationships

    @listens_for(orm.mapper, 'after_configured', once=True)
    def _mappers_configured():
        mappings = {rel.key: _get_backref_name(rel) for rel in inspect(model).relationships if rel.key in relationships}

        @listens_for(model, 'load')
        def _populate_backrefs(target, context):
            for name, backref in mappings.iteritems():
                # __dict__ to avoid triggering lazy-loaded relationships
                if target.__dict__.get(name) is not None:
                    set_committed_value(getattr(target, name), backref, target)
