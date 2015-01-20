## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

import pytest

from indico.util.string import seems_html, to_unicode


def test_seems_html():
    assert seems_html('<b>test')
    assert seems_html('a <b> c')
    assert not seems_html('test')
    assert not seems_html('a < b > c')


@pytest.mark.parametrize(('input', 'output'), (
    (b'foo', u'foo'),            # ascii
    (u'foo', u'foo'),            # unicode
    (b'm\xc3\xb6p', u'm\xf6p'),  # utf8
    (b'm\xf6p', u'm\xf6p'),      # latin1
    (b'm\xc3\xb6p m\xf6p',       # mixed...
     u'm\xc3\xb6p m\xf6p'),      # ...decoded as latin1
))
def test_to_unicode(input, output):
    assert to_unicode(input) == output
