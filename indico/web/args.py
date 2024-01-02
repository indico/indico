# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections.abc import Mapping

from flask import g
from marshmallow import EXCLUDE, Schema
from webargs.flaskparser import FlaskParser
from webargs.multidictproxy import MultiDictProxy
from werkzeug.datastructures import MultiDict


def _strip_whitespace(value):
    if isinstance(value, str):
        value = value.strip()
    elif isinstance(value, MultiDict):
        return type(value)((k, _strip_whitespace(v)) for k, vals in value.lists() for v in vals)
    elif isinstance(value, dict):
        return {k: _strip_whitespace(v) for k, v in value.items()}
    elif isinstance(value, (list, set)):
        return type(value)(map(_strip_whitespace, value))
    return value


class IndicoFlaskParser(FlaskParser):
    """A custom webargs flask parser that strips surrounding whitespace."""

    DEFAULT_LOCATION = 'json_or_form'

    def load_querystring(self, req, schema):
        # remove immutability since we may want to modify the data in `schema_pre_load`
        return MultiDictProxy(_strip_whitespace(MultiDict(req.args)), schema)

    def load_form(self, req, schema):
        # remove immutability since we may want to modify the data in `schema_pre_load`
        return MultiDictProxy(_strip_whitespace(MultiDict(req.form)), schema)

    def load_json(self, req, schema):
        return _strip_whitespace(super().load_json(req, schema))


parser = IndicoFlaskParser()


@parser.error_handler
def handle_error(error, req, schema, *, error_status_code, error_headers):
    # since 6.0.0b7 errors are namespaced by their source. this is nice for APIs taking
    # data from different locations to serve very specific errors, but in a typical web app
    # where you usually have only one source and certainly not the same field name in different
    # locations, it just makes handling errors in JS harder since we suddenly have to care if
    # it's form data or json data.
    # this gets even worse when using the `json_or_form_or_query` meta location where we don't
    # have detailed location information anyway.
    namespaced = error.messages  # mutating this below is safe
    error.messages = namespaced.popitem()[1]
    assert not namespaced  # we never expect to have more than one location
    parser.handle_error(error, req, schema, error_status_code=error_status_code, error_headers=error_headers)


def _split_kwargs(kwargs):
    schema_kwargs = kwargs.copy()
    context = schema_kwargs.pop('context', {})
    webargs_kwargs = {
        a: schema_kwargs.pop(a)
        for a in ('location', 'as_kwargs', 'validate', 'error_status_code', 'error_headers', 'req', 'unknown')
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
    schema_kwargs, context, webargs_kwargs = _split_kwargs(kwargs)
    webargs_kwargs.setdefault('unknown', EXCLUDE)

    if isinstance(schema_cls, Mapping):
        schema_cls = parser.schema_class.from_dict(schema_cls)
    elif isinstance(schema_cls, Schema):
        raise TypeError('Pass a schema or an argmap instead of a schema instance to use_args/use_kwargs')

    def factory(req):
        return schema_cls(**schema_kwargs, context=context)

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
    webargs_kwargs.setdefault('unknown', EXCLUDE)

    if isinstance(schema_cls, Mapping):
        schema_cls = parser.schema_class.from_dict(schema_cls)
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
