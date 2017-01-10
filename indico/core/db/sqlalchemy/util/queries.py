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

import re

from sqlalchemy import over, func, inspect
from sqlalchemy.sql import update

TS_REGEX = re.compile(r'([@<>!()&|:\'])')


def limit_groups(query, model, partition_by, order_by, limit=None, offset=0):
    """Limits the number of rows returned for each group


    This utility allows you to apply a limit/offset to grouped rows of a query.
    Note that the query will only contain the data from `model`; i.e. you cannot
    add additional entities.

    :param query: The original query, including filters, joins, etc.
    :param model: The model class for `query`
    :param partition_by: The column to group by
    :param order_by: The column to order the partitions by
    :param limit: The maximum number of rows for each partition
    :param offset: The number of rows to skip in each partition
    """
    inner = query.add_columns(over(func.row_number(), partition_by=partition_by,
                                   order_by=order_by).label('rownum')).subquery()

    query = model.query.select_entity_from(inner)
    if limit:
        return query.filter(offset < inner.c.rownum, inner.c.rownum <= (limit + offset))
    else:
        return query.filter(offset < inner.c.rownum)


def db_dates_overlap(entity, start_column, start, end_column, end, inclusive=False):
    element_start = getattr(entity, start_column)
    element_end = getattr(entity, end_column)
    if inclusive:
        return (element_start <= end) & (start <= element_end)
    else:
        return (element_start < end) & (start < element_end)


def escape_like(value):
    """Escapes a string to be used as a plain string in LIKE"""
    escape_char = '\\'
    return (value
            .replace(escape_char, escape_char * 2)  # literal escape char needs to be escaped
            .replace('%', escape_char + '%')      # we don't want % wildcards inside the value
            .replace('_', escape_char + '_'))     # same for _ wildcards


def preprocess_ts_string(text, prefix=True):
    atoms = [TS_REGEX.sub(r'\\\1', atom.strip()) for atom in text.split()]
    return ' & '.join('{}:*'.format(atom) if prefix else atom for atom in atoms)


def has_extension(conn, name):
    """Checks if the postgres database has a certain extension installed"""
    return conn.execute("SELECT EXISTS(SELECT TRUE FROM pg_extension WHERE extname = %s)", (name,)).scalar()


def increment_and_get(col, filter_):
    """Increments and returns a numeric column.

    This is committed to the database immediately in a separate
    transaction to avoid possible conflicts.

    The main purpose of this utility is to generate "scoped" IDs
    (which cannot be represented using database-level sequences as you
    would need one sequence per scope) without risking collisions when
    inserting the objects those IDs are eventually assigned to.

    :param col: The column to update, e.g. ``SomeModel.last_num``
    :param filter_: A filter expression such as ``SomeModel.id == n``
                    to restrict which columns to update.
    """
    from indico.core.db import db
    with db.tmp_session() as s:
        rv = s.execute(update(col.class_).where(filter_).values({col: col + 1}).returning(col)).fetchone()[0]
        s.commit()
    return rv


def get_related_object(obj, relationship, criteria):
    """Get an object from a one-to-many relationship.

    If the relationship is already loaded, the criteria are evaluated
    in Python; otherwise a query is sent to the database to get just
    the specified object.

    For maximum compatibility between the two loading methods, values
    consisting of only digits are compared as numbers even if they are
    provided as strings since this is how it works when sending a query.

    :param obj: A model instance that has a relationship
    :param relationship: The name of said relationship
    :param criteria: A dict used to filter the objects from the
                     relationship.
    :return: A single object from the relationship or ``None`` if no
             such object could be found.
    """
    def _compare(a, b):
        if isinstance(a, basestring) and a.isdigit():
            a = int(a)
        if isinstance(b, basestring) and b.isdigit():
            b = int(b)
        return a == b

    # if the relationship is loaded evaluate the criteria in python
    if relationship not in inspect(obj).unloaded:
        return next((x for x in getattr(obj, relationship)
                     if all(_compare(getattr(x, k), v) for k, v in criteria.iteritems())),
                    None)
    # otherwise query that specific object
    cls = getattr(type(obj), relationship).prop.mapper.class_
    return cls.query.with_parent(obj, relationship).filter_by(**criteria).first()


def get_n_matching(query, n, predicate):
    """Get N objects from a query that satisfy a condition.

    This queries for ``n * 5`` objects initially and then loads
    more objects until no more results are available or ``n`` objects
    have been found.

    :param query: A sqlalchemy query object
    :param n: The max number of objects to return
    :param predicate: A callable used to filter the found objects
    """
    _offset = [0]

    def _get():
        limit = n * 5
        rv = query.offset(_offset[0]).limit(limit).all()
        _offset[0] += limit
        return rv

    results = filter(predicate, _get())
    while len(results) < n:
        objects = _get()
        if not objects:
            break
        results.extend(x for x in objects if predicate(x))
    return results[:n]
