# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from webargs.flaskparser import FlaskParser

from indico.util.string import strip_whitespace


class IndicoFlaskParser(FlaskParser):
    """
    A custom webargs flask parser that strips surrounding whitespace.
    """

    def parse_arg(self, name, field, req, locations=None):
        rv = super(IndicoFlaskParser, self).parse_arg(name, field, req, locations=locations)
        if isinstance(rv, basestring):
            return rv.strip()
        elif isinstance(rv, (list, set)):
            return type(rv)(map(strip_whitespace, rv))
        return rv


parser = IndicoFlaskParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
