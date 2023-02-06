# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.util import get_event_from_url


@pytest.mark.parametrize(('url', 'asserted_error_message'), (
    ('http://example.com', 'Invalid event URL'),
    ('http://example.com/foo', 'Invalid event URL'),
    ('http://example.com/event/123', 'Events from other Indico instances cannot be imported'),
))
def test_get_event_from_url_raises_value_error(url, asserted_error_message):
    with pytest.raises(ValueError, match=asserted_error_message):
        get_event_from_url(url)


def test_get_event_from_url_returns_event(dummy_event):
    event = get_event_from_url(f'http://localhost/event/{dummy_event.id}')
    assert event == dummy_event
