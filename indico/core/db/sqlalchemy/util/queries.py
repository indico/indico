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

import re

from sqlalchemy import over, func


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
    escape_char = u'\\'
    return (value
            .replace(escape_char, escape_char * 2)  # literal escape char needs to be escaped
            .replace(u'%', escape_char + u'%')      # we don't want % wildcards inside the value
            .replace(u'_', escape_char + u'_'))     # same for _ wildcards


def preprocess_ts_string(text, prefix=True):
    atoms = [TS_REGEX.sub(r'\\\1', atom.strip()) for atom in text.split()]
    return ' & '.join('{}:*'.format(atom) if prefix else atom for atom in atoms)


def has_extension(conn, name):
    """Checks if the postgres database has a certain extension installed"""
    return conn.execute("SELECT EXISTS(SELECT TRUE FROM pg_extension WHERE extname = %s)", (name,)).scalar()
