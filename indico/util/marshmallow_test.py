# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

from datetime import datetime

import pytest
import pytz
from marshmallow import ValidationError

from indico.util.marshmallow import NaiveDateTime


def test_NaiveDateTime_serialize():
    now = datetime.now()
    utc_now = pytz.utc.localize(datetime.utcnow())
    obj = type(b'Test', (object,), {
        b'naive': now,
        b'aware': utc_now,
    })
    field = NaiveDateTime()
    assert field.serialize('naive', obj) == now.isoformat()
    with pytest.raises(AssertionError):
        field.serialize('aware', obj)


def test_NaiveDateTime_deserialize():
    now = datetime.now()
    utc_now = pytz.utc.localize(datetime.utcnow())
    field = NaiveDateTime()
    assert field.deserialize(now.isoformat()) == now
    with pytest.raises(ValidationError):
        field.deserialize(utc_now.isoformat())
