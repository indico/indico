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
from flask_sqlalchemy import Model, BaseQuery, Pagination
from sqlalchemy import inspect, orm
from sqlalchemy.event import listens_for, listen
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import joinedload, contains_eager
from sqlalchemy.orm.attributes import get_history, set_committed_value
from sqlalchemy.orm.exc import NoResultFound

from indico.core import signals


class IndicoBaseQuery(BaseQuery):
    def paginate(self, page=1, per_page=25, show_all=False):
        """Paginate a query object.

        This behaves almost like the default `paginate` method from
        Flask-SQLAlchemy but allows showing all results on a single page.

        :param page: Number of the page to return.
        :param per_page: Number of items per page.
        :param show_all: Whether to show all the elements on one page.
        :return: a :class:`Pagination` object
        """
        if page < 1 or show_all:
            page = 1

        if show_all:
            items = self.all()
            per_page = total = len(items)
        else:
            items = self.limit(per_page).offset((page - 1) * per_page).all()
            if page == 1 and len(items) < per_page:
                total = len(items)
            else:
                total = self.order_by(None).count()

        return Pagination(self, page, per_page, total, items)


class IndicoModel(Model):
    """Indico DB model"""

    #: Whether relationship preloading is allowed.  If disabled,
    #: the on-load event that populates relationship from the preload
    #: cache is not registered.
    allow_relationship_preloading = False
    query_class = IndicoBaseQuery

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

    @classmethod
    def preload_relationships(cls, query, *relationships, **kwargs):
        """Preload relationships for all objects from a query.

        :param query: A SQLAlchemy query object.
        :param relationships: The names of relationships to preload.
        :param strategy: The loading strategy to use for the
                         relationships.  Defaults to `joinedload` and
                         can be any callable that takes a relationship
                         name and returns a query option.
        """
        assert cls.allow_relationship_preloading
        strategy = kwargs.pop('strategy', joinedload)
        assert not kwargs  # no other kwargs allowed
        cache = g.setdefault('relationship_cache', {}).setdefault(cls, {'data': {}, 'relationships': set()})
        missing_relationships = set(relationships) - cache['relationships']
        if not missing_relationships:
            return
        query = query.options(*map(strategy, missing_relationships))
        data_cache = cache['data']
        for obj in query:
            obj_cache = data_cache.setdefault(obj, {})
            for rel in missing_relationships:
                obj_cache[rel] = getattr(obj, rel)
        cache['relationships'] |= missing_relationships

    @classmethod
    def _populate_preloaded_relationships(cls, target, *unused):
        cache = g.get('relationship_cache', {}).get(type(target))
        if not cache:
            return
        for rel, value in cache['data'].get(target, {}).iteritems():
            if rel not in target.__dict__:
                set_committed_value(target, rel, value)

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

    def populate_from_dict(self, data, keys=None, skip=None):
        """Populates the object with values in a dictionary

        :param data: a dict containing values to populate the object.
        :param keys: If set, only keys from that list are populated.
        :param skip: If set, keys from that list are skipped.
        """
        cls = type(self)
        for key, value in data.iteritems():
            if keys and key not in keys:
                return False
            if skip and key in skip:
                continue
            if not hasattr(cls, key):
                raise ValueError("{} has no attribute '{}'".format(cls.__name__, key))
            setattr(self, key, value)

    def populate_from_attrs(self, obj, attrs):
        """Populates the object from another object's attributes

        :param obj: an object
        :param attrs: a set containing the attributes to copy
        """
        cls = type(self)
        for attr in attrs:
            if not hasattr(cls, attr):
                raise ValueError("{} has no attribute '{}'".format(cls.__name__, attr))
            setattr(self, attr, getattr(obj, attr))

    def __committed__(self, change):
        """Called after a commit for this object.

        ALWAYS call super if you override this method!

        :param change: The operation that has been committed (delete/insert/update)
        """
        if hasattr(g, 'memoize_cache'):
            del g.memoize_cache
        signals.model_committed.send(type(self), obj=self, change=change)


@listens_for(orm.mapper, 'after_configured', once=True)
def _mappers_configured():
    from indico.core.db import db
    for model in db.Model._decl_class_registry.itervalues():
        if hasattr(model, '__table__') and model.allow_relationship_preloading:
            listen(model, 'load', model._populate_preloaded_relationships)


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


def override_attr(attr_name, parent_name, fget=None):
    """Create property that overrides an attribute coming from parent.

    In order to ensure setter functionality at creation time, ``parent`` must be
    initialized before the overriden attribute.

    :param attr_name: The name of the attribute to be overriden.
    :param parent_name: The name of the attribute from which to override the attribute.
    :param fget: Getter for own property
    """

    own_attr_name = '_' + attr_name

    def _get(self):
        parent = getattr(self, parent_name)
        attr = getattr(self, own_attr_name)
        fget_ = (lambda self, __: attr) if fget is None else fget
        return fget_(self, own_attr_name) if attr is not None or not parent else getattr(parent, attr_name)

    def _set(self, value):
        parent = getattr(self, parent_name)
        own_value = getattr(self, own_attr_name)
        if not parent or own_value is not None or value != getattr(parent, attr_name):
            setattr(self, own_attr_name, value)

    def _expr(cls):
        return getattr(cls, own_attr_name)

    return hybrid_property(_get, _set, expr=_expr)


def get_model_by_table_name(table_name):
    """Get the model class based on the name of the table"""
    from indico.core.db import db
    return next((x for x in db.Model._decl_class_registry.itervalues()
                 if hasattr(x, '__table__') and x.__table__.fullname == 'events.events'), None)
