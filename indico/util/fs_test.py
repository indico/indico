# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
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


@pytest.mark.parametrize(('filename', 'expected'), (
    ('', 'fallback'),
    (None, 'fallback'),
    ('foo.txt', 'foo.txt'),
    ('../../../etc/passwd', 'etc_passwd'),
    ('m\xf6p.txt', 'moep.txt'),
    ('/m\xf6p.txt', 'moep.txt'),
    (r'spacy   \filename', 'spacy_filename'),
))
def test_secure_filename(filename, expected):
    assert secure_filename(filename, 'fallback') == expected
