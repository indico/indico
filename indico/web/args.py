# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

from flask import g
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


def use_rh_args(schema_cls, **kwargs):
    """Similar to ``use_args`` but populates the context from RH attributes.

    The Schema needs a Meta class with an ``rh_context`` attribute specifying
    which attributes should be taken from the current RH.

    :param schema_cls: A marshmallow Schema. This must be the schema class itself,
                       an argmap or schema instance is not accepted.
    :param kwargs: Any keyword arguments that are supported by ``use_args`` or the
                   Schema constructor.
    """

    default_context = kwargs.pop('context', {})

    webargs_kwargs = {
        a: kwargs.pop(a)
        for a in ('locations', 'as_kwargs', 'validate', 'error_status_code', 'error_headers')
        if a in kwargs
    }

    def factory(req):
        context = dict(default_context)
        context.update((arg, getattr(g.rh, arg, None)) for arg in schema_cls.Meta.rh_context)
        return schema_cls(context=context, **kwargs)

    return use_args(factory, **webargs_kwargs)


def use_rh_kwargs(schema_cls, **kwargs):
    """Like ``use_rh_args``, but using kwargs when calling the decorated function."""
    kwargs['as_kwargs'] = True
    return use_rh_args(schema_cls, **kwargs)
