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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

__all__ = ['DBMgr', 'MigratedDB']

import logging
import time

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.engine import reflection, Engine
from sqlalchemy.event import listens_for
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import (
    MetaData,
    Table,
    DropTable,
    ForeignKeyConstraint,
    DropConstraint,
)
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.types import Numeric
from zope.sqlalchemy import ZopeTransactionExtension

from indico.core.logger import Logger

from ..errors import IndicoError
from .manager import DBMgr
from .migration import MigratedDB


logger = Logger.get('db')
logger.setLevel(logging.DEBUG)


db = SQLAlchemy(session_options={'extension': ZopeTransactionExtension()})


def apply_db_loggers(debug=False):
    if debug:
        @listens_for(Engine, 'before_cursor_execute')
        def before_cursor_execute(conn, cursor, statement,
                                  parameters, context, executemany):
            context._query_start_time = time.time()
            logger.debug('Start Query: {}'.format(statement))


        @listens_for(Engine, 'after_cursor_execute')
        def after_cursor_execute(conn, cursor, statement,
                                 parameters, context, executemany):
            total = time.time() - context._query_start_time
            logger.debug('Query Complete!')
            logger.debug('Total Time: {}'.format(total))


class IndicoDBError(IndicoError):
    pass


class Committer(object):

    def __enter__(self):
        pass

    def __exit__(self, e_typ, e_val, trcbak):
        if e_typ:
            db.session.rollback()
        else:
            db.session.commit()


# ================================== time diff

# engine specific time differences
class time_diff(FunctionElement):
    name = 'time_diff'
    type = Numeric


@compiles(time_diff, 'default')
def _time_diff_default(element, compiler, **kwargs):
    arg1, arg2 = list(element.clauses)
    return '{} - {}'.format(arg2, arg1)


@compiles(time_diff, 'postgresql')
def _time_diff_postgres(element, compiler, **kwargs):
    arg1, arg2 = list(element.clauses)
    return 'EXTRACT(epoch FROM {}::time) - EXTRACT(epoch FROM {}::time)'.format(arg2, arg1)

# ================================ greatest

class greatest(FunctionElement):
    name = 'greatest'

@compiles(greatest)
def default_greatest(element, compiler, **kw):
    return compiler.visit_function(element)

@compiles(greatest, 'postgresql')
def case_greatest(element, compiler, **kw):
    arg1, arg2 = list(element.clauses)
    return 'CASE WHEN %s > %s THEN %s ELSE %s END' % (
        compiler.process(arg1),
        compiler.process(arg2),
        compiler.process(arg1),
        compiler.process(arg2),
    )

# ============================= least

class least(FunctionElement):
    name = 'least'


@compiles(least)
def default_least(element, compiler, **kw):
    return compiler.visit_function(element)


@compiles(least, 'postgresql')
def case_least(element, compiler, **kw):
    arg1, arg2 = list(element.clauses)
    return 'CASE WHEN %s > %s THEN %s ELSE %s END' % (
        compiler.process(arg1),
        compiler.process(arg2),
        compiler.process(arg2),
        compiler.process(arg1),
    )


def drop_database(db):
    if db.engine.name == 'sqlite':
        db.drop_all()
    else:
        conn = db.engine.connect()
        trans = conn.begin()
        inspector = reflection.Inspector.from_engine(db.engine)

        metadata = MetaData()

        tbs, all_fks = [], []
        for table_name in inspector.get_table_names():
            fks = [ForeignKeyConstraint((), (), name=fk['name'])
                   for fk in inspector.get_foreign_keys(table_name)
                   if fk['name']]
            tbs.append(Table(table_name, metadata, *fks))
            all_fks.extend(fks)

        for fkc in all_fks:
            conn.execute(DropConstraint(fkc))
        for table in tbs:
            conn.execute(DropTable(table))
        trans.commit()
