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

from __future__ import unicode_literals

import pytest

from indico.web.flask.util import endpoint_for_url


@pytest.mark.parametrize(('base_url', 'url', 'endpoint'), (
    ('http://indico.test', 'http://indico.test/contact', 'core.contact'),
    ('http://indico.test/indico', 'http://indico.test/indico/contact', 'core.contact'),
    ('http://indico.test', 'http://indico.test/indico/contact', None),
    ('http://indico.test/indico', 'http://indico.test/contact', None),
    ('http://other.test/indico', 'http://indico.test/contact', None),
    ('http://indico.test/indico', 'http://other.test/contact', None),
))
def test_endpoint_for_url(base_url, url, endpoint):
    data = endpoint_for_url(url, base_url=base_url)
    if endpoint is None:
        assert data is None
    else:
        assert data is not None
        assert data[0] == endpoint
