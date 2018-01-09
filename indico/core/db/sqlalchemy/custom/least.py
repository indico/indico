# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import FunctionElement


class least(FunctionElement):
    name = 'least'


@compiles(least)
def _least_default(element, compiler, **kw):
    return compiler.visit_function(element)


@compiles(least, 'postgresql')
def _least_case(element, compiler, **kw):
    arg1, arg2 = list(element.clauses)
    return 'CASE WHEN {0} > {1} THEN {1} ELSE {0} END'.format(compiler.process(arg1), compiler.process(arg2))
