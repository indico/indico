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

"""
Bulk-renaming utility for constraints/indexes, intended to be used
in alembic migrations.

The `bulk_rename` method takes a mapping of this form::

    mapping = {
        'SCHEMA.TABLE': {
            'indexes': {
                'OLDNAME': 'NEWNAME',
            },
            'constraints': {
                'OLDNAME': 'NEWNAME',
            }
        }
    }

The *indexes* dict contains the primary key and indexes, while the
*constraints* dict includes foreign keys, unique and check constraints.
"""

# TODO: remove this module before releasing 2.0 when removing all the alembic revisions from the 1.9 era
# Indico 2.0 should come with a clean revision list!


def _rename_constraint(schema, table, name, new_name):
    stmt = 'ALTER TABLE "{}"."{}" RENAME CONSTRAINT "{}" TO "{}"'
    return stmt.format(schema, table, name, new_name)


def _rename_index(schema, name, new_name):
    stmt = 'ALTER INDEX "{}"."{}" RENAME TO "{}"'
    return stmt.format(schema, name, new_name)


def _iter_renames(mapping):
    for table, types in mapping.iteritems():
        schema, table = table.split('.', 1)
        for type_, renames in types.iteritems():
            for old, new in renames.iteritems():
                yield schema, table, type_, old, new


def bulk_rename(mapping, reverse=False):
    for schema, table, type_, old, new in _iter_renames(mapping):
        if reverse:
            old, new = new, old
        if type_ == 'constraints':
            yield _rename_constraint(schema, table, old, new)
        elif type_ == 'indexes':
            yield _rename_index(schema, old, new)
        else:
            raise ValueError('invalid type: ' + type_)
