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

from indico.util.event import truncate_path


@pytest.mark.parametrize(('full_path', 'chars', 'skip_first', 'expected'), (
    ([],                                         10, False, (None, None, None, False)),
    (['aaa'],                                     5, False, (None, None, 'aaa', False)),
    (['aaaaaa'],                                  5, False, (None, None, 'aaaaaa', False)),
    (['aaa', 'bbb'],                             10, False, ('aaa', None, 'bbb', False)),
    (['aaa', 'bbb'],                              5, False, (None, None, 'bbb', True)),
    (['aaa', 'bbb', 'ccc'],                      10, False, ('aaa', ['bbb'], 'ccc', False)),
    (['aaa', 'bbb', 'ccc', 'ddd'],               20, False, ('aaa', ['bbb', 'ccc'], 'ddd', False)),
    (['aaa', 'bbb', 'ccc', 'ddd'],               10, False, ('aaa', ['ccc'], 'ddd', True)),
    (['aaa', 'bbb', 'ccc', 'ddd', 'eee'],        14, False, ('aaa', ['ccc', 'ddd'], 'eee', True)),
    (['aaaaaaaa', 'bbb', 'ccc'],                 10, False, (None, ['bbb'], 'ccc', True)),
    (['aaaaaaaa', 'bbb', 'ccc', 'ddd'],          10, False, (None, ['bbb', 'ccc'], 'ddd', True)),
    ([],                                         10, False, (None, None, None, False)),
    (['aaa'],                                     5, True,  (None, None, 'aaa', False)),
    (['aaaaaa'],                                  5, True,  (None, None, 'aaaaaa', False)),
    (['aaa', 'bbb'],                             10, True,  ('aaa', None, 'bbb', False)),
    (['aaa', 'bbb'],                              5, True,  (None, None, 'bbb', True)),
    (['aaa', 'bbb', 'ccc'],                      10, True,  ('bbb', None, 'ccc', False)),
    (['aaa', 'bbb', 'ccc', 'ddd'],               10, True,  ('bbb', ['ccc'], 'ddd', False)),
    (['aaa', 'bbb', 'ccc', 'ddd', 'eee'],        14, True,  ('bbb', ['ccc', 'ddd'], 'eee', False)),
    (['aaa', 'bbb', 'ccc', 'ddd', 'eee', 'fff'], 14, True,  ('bbb', ['ddd', 'eee'], 'fff', True)),
    (['aaa', 'bbbbbbbb', 'ccc'],                 10, True,  (None, None, 'ccc', True)),
    (['aaa', 'bbbbbbbb', 'ccc', 'ddd'],          10, True,  (None, ['ccc'], 'ddd', True)),
    (['aaa', 'bbbbbbbb', 'ccc', 'ddd', 'eee'],   10, True,  (None, ['ccc', 'ddd'], 'eee', True)),
))
def test_truncate_path(full_path, chars, skip_first, expected):
    assert truncate_path(full_path, chars=chars, skip_first=skip_first) == expected
