# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import wraps
from itertools import groupby, islice


def group_list(data, key=None, sort_by=None, sort_reverse=False):
    return {group: sorted(items, key=sort_by, reverse=sort_reverse)
            for group, items in groupby(sorted(data, key=key), key=key)}


def committing_iterator(iterable, n=100):
    """Iterate over *iterable* and commits every *n* items.

    Also issue a commit after the iterator has been exhausted.

    :param iterable: An iterable object
    :param n: Number of items to commit after
    """
    from indico.core.db import db

    for i, data in enumerate(iterable, 1):
        yield data
        if i % n == 0:
            db.session.commit()
    db.session.commit()


def materialize_iterable(type_=list):
    """Decorator that materializes an iterable.

    Iterates over the result of the decorated function and stores
    the returned values into a collection.  This makes most sense
    on functions that use `yield` for simplicity but should return
    a collection instead of a generator.

    :param type_: The collection type to return. Can be any callable
                  that accepts an iterable.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            rv = fn(*args, **kwargs)
            return None if rv is None else type_(rv)

        return wrapper

    return decorator


def window(seq, n=2):
    """
    Return a sliding window (of width n) over data from the iterable.

        s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...
    """
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result
