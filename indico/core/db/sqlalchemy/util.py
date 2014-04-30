# -*- coding: utf-8 -*-
##
##
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

from flask.ext.sqlalchemy import Model
from sqlalchemy import MetaData, ForeignKeyConstraint, Table
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.sql.ddl import DropConstraint, DropTable


class IndicoModel(Model):
    """Indico DB model"""

    @classmethod
    def find(cls, *args, **kwargs):
        joins = kwargs.pop('_join', ())
        if not isinstance(joins, (list, tuple)):
            joins = (joins,)
        return cls.query.join(*joins).filter(*args).filter_by(**kwargs)

    @classmethod
    def find_all(cls, *args, **kwargs):
        return cls.find(*args, **kwargs).all()

    @classmethod
    def find_first(cls, *args, **kwargs):
        return cls.find(*args, **kwargs).first()

    @classmethod
    def get(cls, oid):
        return cls.query.get(oid)


def delete_all_tables(db):
    if db.engine.name == 'sqlite':
        db.drop_all()
    else:
        conn = db.engine.connect()
        transaction = conn.begin()
        inspector = Inspector.from_engine(db.engine)

        metadata = MetaData()

        tables = []
        all_fkeys = []
        for table_name in inspector.get_table_names():
            fkeys = [ForeignKeyConstraint((), (), name=fk['name'])
                     for fk in inspector.get_foreign_keys(table_name)
                     if fk['name']]
            tables.append(Table(table_name, metadata, *fkeys))
            all_fkeys.extend(fkeys)

        for fkey in all_fkeys:
            conn.execute(DropConstraint(fkey))
        for table in tables:
            conn.execute(DropTable(table))
        transaction.commit()
