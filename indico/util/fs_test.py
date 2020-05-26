# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.util.fs import secure_client_filename, secure_filename


@pytest.mark.parametrize(('filename', 'expected'), (
    (u'', u'file'),
    (None, u'file'),
    (u'.', u'_'),
    (u'..', u'__'),
    (u'../', u'.._'),
    (u'foo.txt', u'foo.txt'),
    (u'../../../etc/passwd', u'.._.._.._etc_passwd'),
    (u'm\xf6p.txt', u'm\xf6p.txt'),
    (u'/m\xf6p.txt', u'_m\xf6p.txt'),
    (ur'c:\test.txt', u'c_test.txt'),
    (r'spacy   \filename', u'spacy _filename'),
))
def test_secure_client_filename(filename, expected):
    assert secure_client_filename(filename) == expected


@pytest.mark.parametrize(('filename', 'expected'), (
    ('', 'fallback'),
    (None, 'fallback'),
    ('foo.txt', 'foo.txt'),
    ('../../../etc/passwd', 'etc_passwd'),
    (u'm\xf6p.txt', 'moep.txt'),
    (u'm\xf6p.txt'.encode('utf-8'), 'moep.txt'),
    (u'/m\xf6p.txt', 'moep.txt'),
    (r'spacy   \filename', 'spacy_filename'),
))
def test_secure_filename(filename, expected):
    assert secure_filename(filename, 'fallback') == expected
