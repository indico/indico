# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import FunctionElement


class greatest(FunctionElement):
    name = 'greatest'


@compiles(greatest)
def _greatest_default(element, compiler, **kw):
    return compiler.visit_function(element)


@compiles(greatest, 'postgresql')
def _greatest_case(element, compiler, **kw):
    arg1, arg2 = list(element.clauses)
    return 'CASE WHEN {0} > {1} THEN {0} ELSE {1} END'.format(compiler.process(arg1), compiler.process(arg2))
