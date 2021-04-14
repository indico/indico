# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.util.caching import memoize_request


@pytest.fixture
def not_testing(app_context):
    app_context.config['TESTING'] = False
    try:
        yield
    finally:
        app_context.config['TESTING'] = True


@pytest.mark.usefixtures('request_context', 'not_testing')
def test_memoize_request_args():
    calls = [0]

    @memoize_request
    def fn(a, b, c='default', **kw):
        calls[0] += 1

    assert calls[0] == 0
    fn(1, 2)
    assert calls[0] == 1
    fn(1, 2)  # normal memoized call
    assert calls[0] == 1
    # default value explicitly provided (both as arg and kwarg)
    fn(1, 2, 'default')
    fn(1, 2, c='default')
    fn(1, b=2)
    fn(a=1, b=2, c='default')
    assert calls[0] == 1
    fn(2, 2, c='default')
    assert calls[0] == 2
    fn(2, 2)
    assert calls[0] == 2
    fn(2, 2, foo='bar')
    assert calls[0] == 3
    fn(a=2, b=2, foo='bar')
    assert calls[0] == 3
