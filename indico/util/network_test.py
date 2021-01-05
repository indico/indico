# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.util.network import is_private_url


@pytest.mark.parametrize(('url', 'expected'), (
    ('http://127.0.0.1', True),
    ('https://[::1]', True),
    ('https://localhost', True),
    ('http://192.168.0.12', True),
    ('https://indico.cern.ch', False),
    ('https://[2001:1458:201:87::100:c]', False),
    ('https://indico.local', True),
    ('https://local', True),
    ('https://testing-instance', True),
    ('https://indico', True)
))
def test_is_private_url(url, expected):
    assert is_private_url(url) == expected
