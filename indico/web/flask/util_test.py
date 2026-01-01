# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.web.flask.util import endpoint_for_url, should_inline_file


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


@pytest.mark.parametrize('mimetype', ('text/html', 'image/svg+xml'))
@pytest.mark.parametrize(('inline', 'safe', 'expected'), (
    (None, True, False),
    (False, True, False),
    (True, True, False),
    (None, False, True),
    (False, False, False),
    (True, False, True),
))
@pytest.mark.usefixtures('request_context')
def test_should_inline_file_dangerous_types(mimetype, inline, safe, expected):
    assert should_inline_file(mimetype, inline, safe=safe) == expected
