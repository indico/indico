# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

from flask import g
from marshmallow import Schema
from webargs import dict2schema
from webargs.compat import Mapping
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


def _split_kwargs(kwargs):
    schema_kwargs = kwargs.copy()
    context = schema_kwargs.pop('context', {})
    webargs_kwargs = {
        a: schema_kwargs.pop(a)
        for a in ('locations', 'as_kwargs', 'validate', 'error_status_code', 'error_headers')
        if a in schema_kwargs
    }
    return schema_kwargs, context, webargs_kwargs


def use_args(schema_cls, **kwargs):
    """Similar to webargs' ``use_args`` but allows passing schema kwargs.

    This makes it much easier to use ``partial=True`` for PATCH endpoints.

    :param schema_cls: A marshmallow Schema or an argmap dict.
    :param kwargs: Any keyword arguments that are supported by ``use_args`` or the
                   Schema constructor.
    """
    schema_kwargs, __, webargs_kwargs = _split_kwargs(kwargs)

    if isinstance(schema_cls, Mapping):
        schema_cls = dict2schema(schema_cls, parser.schema_class)
    elif isinstance(schema_cls, Schema):
        raise TypeError('Pass a schema or an argmap instead of a schema instance to use_args/use_kwargs')

    def factory(req):
        return schema_cls(**schema_kwargs)

    return parser.use_args(factory, **webargs_kwargs)


def use_kwargs(schema_cls, **kwargs):
    """Like ``use_args``, but using kwargs when calling the decorated function."""
    kwargs['as_kwargs'] = True
    return use_args(schema_cls, **kwargs)


def use_rh_args(schema_cls, **kwargs):
    """Similar to ``use_args`` but populates the context from RH attributes.

    The Schema needs a Meta class with an ``rh_context`` attribute specifying
    which attributes should be taken from the current RH.

    :param schema_cls: A marshmallow Schema or an argmap dict.
    :param rh_context: When using an argmap, this argument is required and behaves
                       exactly like the ``rh_context`` Meta attribute mentioned above.
    :param kwargs: Any keyword arguments that are supported by ``use_args`` or the
                   Schema constructor.
    """

    schema_kwargs, default_context, webargs_kwargs = _split_kwargs(kwargs)

    if isinstance(schema_cls, Mapping):
        schema_cls = dict2schema(schema_cls, parser.schema_class)
        rh_context_attrs = schema_kwargs.pop('rh_context')
    elif isinstance(schema_cls, Schema):
        raise TypeError('Pass a schema or an argmap instead of a schema instance to use_rh_args/use_rh_kwargs')
    else:
        if 'rh_context' in schema_kwargs:
            raise TypeError('The `rh_context` kwarg is only supported when passing an argmap')
        rh_context_attrs = schema_cls.Meta.rh_context

    def factory(req):
        context = dict(default_context)
        context.update((arg, getattr(g.rh, arg, None)) for arg in rh_context_attrs)
        return schema_cls(context=context, **schema_kwargs)

    return parser.use_args(factory, **webargs_kwargs)


def use_rh_kwargs(schema_cls, **kwargs):
    """Like ``use_rh_args``, but using kwargs when calling the decorated function."""
    kwargs['as_kwargs'] = True
    return use_rh_args(schema_cls, **kwargs)
