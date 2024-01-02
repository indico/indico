# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import yaml

from indico.util.enum import RichIntEnum


class TestEnum(RichIntEnum):
    none = 0
    foo = 1


def test_int_enum_behavior():
    assert not TestEnum.none
    assert TestEnum.none == 0
    assert f'{TestEnum.none}' == '0'
    assert TestEnum.foo
    assert TestEnum.foo == 1
    assert f'{TestEnum.foo}' == '1'


def test_serialize_enum():
    # make sure we don't get the broken getattr serialization in python 3.11.[0-4]
    assert yaml.dump(TestEnum.foo) == '!!python/object/apply:indico.util.enum_test.TestEnum\n- 1\n'
