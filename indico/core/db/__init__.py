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

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext import compiler
from sqlalchemy.sql.expression import FunctionElement

from .manager import DBMgr
from .migration import MigratedDB


db = SQLAlchemy()


# engine specific group concat
class group_concat(FunctionElement):
    name = "group_concat"


@compiler.compiles(group_concat, 'sqlite')
def _group_concat_sqlite(element, compiler, **kwargs):
    if len(element.clauses) == 2:
        separator = compiler.process(element.clauses.clauses[1])
    else:
        separator = ', '

    return 'GROUP_CONCAT(%s SEPARATOR %s)'.format(
        compiler.process(element.clauses.clauses[0]),
        separator
    )
