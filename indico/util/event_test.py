# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
