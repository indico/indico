# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from indico.util.fs import secure_filename


@pytest.mark.parametrize(('filename', 'expected'), (
    ('', 'fallback'),
    (None, 'fallback'),
    ('foo.txt', 'foo.txt'),
    ('', 'fallback'),
    ('../../../etc/passwd', 'etc_passwd'),
    (u'm\xf6p.txt', 'moep.txt'),
    (u'm\xf6p.txt'.encode('utf-8'), 'moep.txt'),
    (u'/m\xf6p.txt', 'moep.txt'),
    (r'spacy   \filename', 'spacy_filename'),
))
def test_secure_filename(filename, expected):
    assert secure_filename(filename, 'fallback') == expected
