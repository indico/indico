# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import functools
import inspect
from itertools import zip_longest
from types import GeneratorType


def values_from_signal(signal_response, single_value=False, skip_none=True, as_list=False,
                       multi_value_types=GeneratorType, return_plugins=False):
    """Combine the results from both single-value and multi-value signals.

    The signal needs to return either a single object (which is not a
    generator) or a generator (usually by returning its values using
    `yield`).

    :param signal_response: The return value of a Signal's `.send()` method
    :param single_value: If each return value should be treated as a single
                         value in all cases (disables the generator check)
    :param skip_none: If None return values should be skipped
    :param as_list: If you want a list instead of a set (only use this if
                    you need non-hashable return values, the order is still
                    not defined!)
    :param multi_value_types: Types which should be considered multi-value.
                              It is used in an `isinstance()` call and if
                              the check succeeds, the value is passed to
                              `list.extend()`
    :param return_plugins: return `(plugin, value)` tuples instead of just
                           the values. `plugin` can be `None` if the signal
                           was not registered in a plugin.
    :return: A set/list containing the results
    """
    values = []
    for func, value in signal_response:
        plugin = getattr(func, 'indico_plugin', None)
        if not single_value and isinstance(value, multi_value_types):
            value_list = list(value)
            if value_list:
                values.extend(zip_longest([plugin], value_list, fillvalue=plugin))
        else:
            values.append((plugin, value))
    if skip_none:
        values = [(p, v) for p, v in values if v is not None]
    if not return_plugins:
        values = [v for p, v in values]
    return values if as_list else set(values)


def named_objects_from_signal(signal_response, name_attr='name', plugin_attr=None):
    """Return a dict of objects based on an unique attribute on each object.

    The signal needs to return either a single object (which is not a
    generator) or a generator (usually by returning its values using
    ``yield``).

    :param signal_response: The return value of a Signal's ``.send()`` method
    :param name_attr: The attribute containing each object's unique name
    :param plugin_attr: The attribute that will be set to the plugin containing
                        the object (set to `None` for objects in the core)
    :return: dict mapping object names to objects
    """
    objects = values_from_signal(signal_response, return_plugins=True)
    if plugin_attr is not None:
        for plugin, cls in objects:
            setattr(cls, plugin_attr, plugin)
    mapping = {getattr(cls, name_attr): cls for _, cls in objects}
    # check for two different objects having the same name, e.g. because of
    # two plugins using a too generic name for their object
    conflicting = {cls for _, cls in objects} - set(mapping.values())
    if conflicting:
        names = ', '.join(sorted(getattr(x, name_attr) for x in conflicting))
        raise RuntimeError(f'Non-unique object names: {names}')
    return mapping


_inspect_signature = functools.cache(inspect.signature)


def make_interceptable(func, key=None, ctx=None):
    """Create a wrapper to make a function call interceptable.

    The returned wrapper behaves like the original function, but accepting any kwarg and
    triggering a signal which can modify its call arguments or even override the return
    value (in which case the original function would not get called at all, unless the
    signal handler decides to do so itself).

    This function can also be used as a decorator; in that case neither a key nor context
    can be provided (but it would not make sense anyway).

    :param func: The function to make interceptable
    :param key: An optional key in case using just the function name would be too generic
                (e.g. in case of most util functions)
    :param ctx: Additional context (usually a dict) to provide additional data that may
                be useful to the signal handler but isn't part of the call args
    """
    from indico.core import signals
    sender = interceptable_sender(func, key)
    sig = _inspect_signature(func)

    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        if not signals.plugin.interceptable_function.has_receivers_for(sender):
            # this check is rather "optimistic" (quote taken from the has_receivers_for docs) and
            # it usually passes even when there's no receiver connected anymore, but outside testing
            # we never disconnect signals anyway...
            return func(*args, **kwargs)
        call_sig = sig
        if not any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()):
            missing_kwargs = set(kwargs) - set(sig.parameters)
            extra_parameters = [inspect.Parameter(mk, inspect.Parameter.KEYWORD_ONLY) for mk in missing_kwargs]
            call_sig = sig.replace(parameters=[*sig.parameters.values(), *extra_parameters])
        bound_args = call_sig.bind(*args, **kwargs)
        return_none = object()
        sig_rvs = values_from_signal(signals.plugin.interceptable_function.send(sender, func=func, args=bound_args,
                                                                                ctx=ctx, RETURN_NONE=return_none),
                                     as_list=True)
        if not sig_rvs:
            # no return value override -> call the original function
            rv = func(*bound_args.args, **bound_args.kwargs)
        elif len(sig_rvs) != 1:
            raise RuntimeError(f'Multiple results returned for interceptable {sender}')
        else:
            rv = sig_rvs[0]
            if rv is return_none:
                rv = None
        return rv

    return _wrapper


def interceptable_sender(func, key=None):
    """Get the signal sender to intercept a function call.

    :param func: The function that should be intercepted
    :param key: An optional key in case using just the function
                name would be too generic (e.g. most utils)
    """
    name = f'{func.__module__}.{func.__qualname__}'
    return f'{name}::{key}' if key else name
