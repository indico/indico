# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy import types
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import FunctionElement


class time_diff(FunctionElement):
    name = 'time_diff'
    type = types.Numeric


@compiles(time_diff, 'default')
def _time_diff_default(element, compiler, **kw):
    arg1, arg2 = list(element.clauses)
    return '{} - {}'.format(arg2, arg1)


@compiles(time_diff, 'postgresql')
def _time_diff_postgres(element, compiler, **kw):
    arg1, arg2 = list(element.clauses)
    return 'EXTRACT(epoch FROM {}::time) - EXTRACT(epoch FROM {}::time)'.format(arg2, arg1)
