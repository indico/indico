# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.util.fs import secure_client_filename, secure_filename


@pytest.mark.parametrize(('filename', 'expected'), (
    ('', 'file'),
    (None, 'file'),
    ('.', '_'),
    ('..', '__'),
    ('../', '.._'),
    ('foo.txt', 'foo.txt'),
    ('../../../etc/passwd', '.._.._.._etc_passwd'),
    ('m\xf6p.txt', 'm\xf6p.txt'),
    ('/m\xf6p.txt', '_m\xf6p.txt'),
    (r'c:\test.txt', 'c_test.txt'),
    (r'spacy   \filename', 'spacy _filename'),
))
def test_secure_client_filename(filename, expected):
    assert secure_client_filename(filename) == expected


@pytest.mark.parametrize(('filename', 'fallback_ext', 'expected'), (
    ('', '', 'fallback'),
    (None, '', 'fallback'),
    ('foo.txt', '', 'foo.txt'),
    ('foo.txt', 'example.zip', 'foo.txt'),
    ('../../../etc/passwd', '', 'etc_passwd'),
    ('m\xf6p.txt', '', 'moep.txt'),
    ('/m\xf6p.txt', '', 'moep.txt'),
    (r'spacy   \filename', '', 'spacy_filename'),
    ('.filename', '', 'filename'),
    ('filename.', '', 'filename'),
    ('filename', '', 'filename'),
    ('file.name', '', 'file.name'),
    ('   ', '', 'fallback'),
    ('foo.', '', 'foo'),
    ('foo', '.txt', 'foo'),
    ('\u4e17', '', 'fallback'),
    ('\u4e17.txt', '', 'fallback.txt'),
    ('\u4e17.txt', '.zip', 'fallback.txt'),
    ('\u4e17.\u4e17', '', 'fallback'),
    ('\u4e17.', '.txt', 'fallback.txt'),
    ('\u4e17.\u4e17', '.txt', 'fallback.txt'),
    ('.\u4e17', '.txt', 'fallback'),
))
def test_secure_filename(filename, fallback_ext, expected):
    assert secure_filename(filename, f'fallback{fallback_ext}') == expected


@pytest.mark.parametrize(('filename', 'expected'), (
    ('foo', 'foo'),
    ('foo.', 'foo'),
    ('\u4e17', ''),
    ('\u4e17.', ''),
))
def test_secure_filename_empty_fallback(filename, expected):
    assert secure_filename(filename, '') == expected
    assert secure_filename(filename, None) == expected


def test_secure_filename_max_length():
    assert secure_filename(f'{"x" * 500}.pdf', 'fallback') == f'{"x" * 150}.pdf'
