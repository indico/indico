# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from string import ascii_lowercase

import pytest

from indico.modules.events.util import ZipGeneratorMixin, get_event_from_url


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


@pytest.mark.parametrize(('segments', 'expected'), (
    # Total length is <=255, no change
    # -> just the filename
    (['a_long_filename.txt'],
     ['a_long_filename.txt']),
    # -> dir + filename
    (['a' * 50, 'a_long_filename.txt'],
     ['a' * 50, 'a_long_filename.txt']),
    # -> dir + subdir + filename
    (['a' * 50, 'b' * 50, 'a_long_filename.txt'],
     ['a' * 50, 'b' * 50, 'a_long_filename.txt']),
    # Total length is >255, only the last subdir before the filename is truncated
    (['a' * 200, 'b' * 200, 'a_long_filename.txt'],
     ['a' * 200, 'b' * 34,  'a_long_filename.txt']),
    # Total length is >255, but truncating one subdir is not enough,
    # so both are truncated while the filename is left unchanged
    (['a' * 250, 'b' * 250, 'a_long_filename.txt'],
     ['a' * 224, 'b' * 10,  'a_long_filename.txt']),
    # Total length is >255, and all segments including the filename are truncated
    ([*(letter * 50 for letter in ascii_lowercase), 'a_long_filename.txt'],
     [*(letter * 10 for letter in ascii_lowercase), 'a_long_fil.txt']),
    # A very long filename
    (['a' * 300 + '.txt'],
     ['a' * 251 + '.txt']),
))
def test_zip_generator_ajust_path_length(segments, expected):
    generator = ZipGeneratorMixin()
    assert list(generator._adjust_path_length(segments)) == expected
