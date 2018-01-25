# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

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
    ('https://indico.dev', True),
    ('https://indico', True)
))
def test_is_private_url(url, expected):
    assert is_private_url(url) == expected
